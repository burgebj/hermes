"""
Hermes Agent Uninstaller.

Provides options for:
- Full uninstall: Remove everything including configs and data
- Keep data: Remove code but keep ~/.hermes/ (configs, sessions, logs)
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

from hermes_constants import get_hermes_home

from hermes_cli.colors import Colors, color

def log_info(msg: str):
    print(f"{color('→', Colors.CYAN)} {msg}")

def log_success(msg: str):
    print(f"{color('✓', Colors.GREEN)} {msg}")

def log_warn(msg: str):
    print(f"{color('⚠', Colors.YELLOW)} {msg}")

def get_project_root() -> Path:
    """Get the project installation directory."""
    return Path(__file__).parent.parent.resolve()


def find_shell_configs() -> list:
    """Find shell configuration files that might have PATH entries."""
    home = Path.home()
    configs = []
    
    candidates = [
        home / ".bashrc",
        home / ".bash_profile",
        home / ".profile",
        home / ".zshrc",
        home / ".zprofile",
    ]
    
    for config in candidates:
        if config.exists():
            configs.append(config)
    
    return configs


def remove_path_from_shell_configs():
    """Remove Hermes PATH entries from shell configuration files."""
    configs = find_shell_configs()
    removed_from = []
    
    for config_path in configs:
        try:
            content = config_path.read_text()
            original_content = content
            
            # Remove lines containing hermes-agent or hermes PATH entries
            new_lines = []
            skip_next = False
            
            for line in content.split('\n'):
                # Skip the "# Hermes Agent" comment and following line
                if '# Hermes Agent' in line or '# hermes-agent' in line:
                    skip_next = True
                    continue
                if skip_next and ('hermes' in line.lower() and 'PATH' in line):
                    skip_next = False
                    continue
                skip_next = False
                
                # Remove any PATH line containing hermes
                if 'hermes' in line.lower() and ('PATH=' in line or 'path=' in line.lower()):
                    continue
                    
                new_lines.append(line)
            
            new_content = '\n'.join(new_lines)
            
            # Clean up multiple blank lines
            while '\n\n\n' in new_content:
                new_content = new_content.replace('\n\n\n', '\n\n')
            
            if new_content != original_content:
                config_path.write_text(new_content)
                removed_from.append(config_path)
                
        except Exception as e:
            log_warn(f"Could not update {config_path}: {e}")
    
    return removed_from


def remove_wrapper_script():
    """Remove the hermes wrapper script if it exists."""
    wrapper_paths = [
        Path.home() / ".local" / "bin" / "hermes",
        Path("/usr/local/bin/hermes"),
    ]
    
    removed = []
    for wrapper in wrapper_paths:
        if wrapper.exists():
            try:
                # Check if it's our wrapper (contains hermes_cli reference)
                content = wrapper.read_text()
                if 'hermes_cli' in content or 'hermes-agent' in content:
                    wrapper.unlink()
                    removed.append(wrapper)
            except Exception as e:
                log_warn(f"Could not remove {wrapper}: {e}")
    
    return removed


def _node_symlink_candidate_dirs() -> "list[Path]":
    """Directories where the installer may have placed node/npm/npx symlinks."""
    dirs: list[Path] = [Path.home() / ".local" / "bin"]
    # Root FHS installs put links in /usr/local/bin.
    if sys.platform == "linux":
        dirs.append(Path("/usr/local/bin"))
    # Termux installs put links in $PREFIX/bin.
    prefix = os.environ.get("PREFIX", "")
    if prefix and "com.termux" in prefix:
        dirs.append(Path(prefix) / "bin")
    return dirs


def remove_node_symlinks(hermes_home: Path) -> list:
    """Remove the node/npm/npx symlinks the installer placed on PATH.

    The POSIX installer (``scripts/install.sh`` / ``scripts/lib/node-bootstrap.sh``)
    symlinks node/npm/npx into the same directory as the ``hermes`` command:

    - ``/usr/local/bin/`` on root FHS installs (Linux, uid 0)
    - ``$PREFIX/bin/`` on Termux
    - ``~/.local/bin/`` otherwise (the common non-root case)

    We check all candidate directories so that uninstall works regardless of
    how the install was done (e.g. a root FHS install that placed links in
    ``/usr/local/bin``, or an older install that used ``~/.local/bin`` before
    the FHS fix).  Only symlinks that resolve into this Hermes home's ``node``
    directory are removed — links the user has repointed elsewhere (nvm, fnm,
    etc.) are left untouched.
    """
    node_dir = (hermes_home / "node").resolve()
    removed = []

    for name in ("node", "npm", "npx"):
        for bin_dir in _node_symlink_candidate_dirs():
            link = bin_dir / name
            try:
                # Only act on symlinks — never delete a real binary the user put here.
                if not link.is_symlink():
                    continue

                # Resolve the link target and confirm it points into our node dir.
                # os.readlink + manual join handles broken (dangling) links too;
                # Path.resolve() on a dangling link still returns the target path.
                target = Path(os.readlink(link))
                if not target.is_absolute():
                    target = (link.parent / target)
                target = target.resolve()

                if target == node_dir or node_dir in target.parents:
                    link.unlink()
                    removed.append(link)
            except Exception as e:
                log_warn(f"Could not remove {link}: {e}")

    return removed


def uninstall_gateway_service():
    """Stop and uninstall the gateway service (systemd, launchd, Windows
    Scheduled Task / Startup folder) and kill any standalone gateway processes.

    Delegates to the gateway module which handles:
    - Linux: user + system systemd services (with proper DBUS env setup)
    - macOS: launchd plists
    - Windows: Scheduled Task + Startup-folder fallback, via ``gateway_windows``
    - All platforms: standalone ``hermes gateway run`` processes
    - Termux/Android: skips systemd (no systemd on Android), still kills standalone processes
    """
    import platform
    stopped_something = False

    # 1. Kill any standalone gateway processes (all platforms, including Termux)
    try:
        from hermes_cli.gateway import kill_gateway_processes, find_gateway_pids
        pids = find_gateway_pids()
        if pids:
            killed = kill_gateway_processes()
            if killed:
                log_success(f"Killed {killed} running gateway process(es)")
                stopped_something = True
    except Exception as e:
        log_warn(f"Could not check for gateway processes: {e}")

    system = platform.system()

    # Termux/Android has no systemd and no launchd — nothing left to do.
    prefix = os.getenv("PREFIX", "")
    is_termux = bool(os.getenv("TERMUX_VERSION") or "com.termux/files/usr" in prefix)
    if is_termux:
        return stopped_something

    # 2. Linux: uninstall systemd services (both user and system scopes)
    if system == "Linux":
        try:
            from hermes_cli.gateway import (
                get_systemd_unit_path,
                get_service_name,
                _systemctl_cmd,
            )
            svc_name = get_service_name()

            for is_system in (False, True):
                unit_path = get_systemd_unit_path(system=is_system)
                if not unit_path.exists():
                    continue

                scope = "system" if is_system else "user"
                try:
                    if is_system and os.geteuid() != 0:  # windows-footgun: ok — Linux systemd uninstall path, guarded by `if system == "Linux"` above
                        log_warn(f"System gateway service exists at {unit_path} "
                                 f"but needs sudo to remove")
                        continue

                    cmd = _systemctl_cmd(is_system)
                    subprocess.run(cmd + ["stop", svc_name],
                                   capture_output=True, check=False)
                    subprocess.run(cmd + ["disable", svc_name],
                                   capture_output=True, check=False)
                    unit_path.unlink()
                    subprocess.run(cmd + ["daemon-reload"],
                                   capture_output=True, check=False)
                    log_success(f"Removed {scope} gateway service ({unit_path})")
                    stopped_something = True
                except Exception as e:
                    log_warn(f"Could not remove {scope} gateway service: {e}")
        except Exception as e:
            log_warn(f"Could not check systemd gateway services: {e}")

    # 3. macOS: uninstall launchd plist
    elif system == "Darwin":
        try:
            from hermes_cli.gateway import get_launchd_plist_path
            plist_path = get_launchd_plist_path()
            if plist_path.exists():
                subprocess.run(["launchctl", "unload", str(plist_path)],
                               capture_output=True, check=False)
                plist_path.unlink()
                log_success(f"Removed macOS gateway service ({plist_path})")
                stopped_something = True
        except Exception as e:
            log_warn(f"Could not remove launchd gateway service: {e}")

    # 4. Windows: uninstall Scheduled Task + Startup-folder entry.  The
    #    gateway_windows module already knows how to locate and remove both
    #    code paths (schtasks /Delete + .cmd unlink) and how to stop any
    #    running detached pythonw gateway process.  We call into it so the
    #    uninstall logic stays in exactly one place.
    elif system == "Windows":
        try:
            from hermes_cli import gateway_windows
            if gateway_windows.is_installed() or gateway_windows.is_task_registered() \
                    or gateway_windows.is_startup_entry_installed():
                try:
                    gateway_windows.stop()
                except Exception as e:
                    log_warn(f"Could not stop Windows gateway cleanly: {e}")
                try:
                    gateway_windows.uninstall()
                    log_success("Removed Windows gateway (Scheduled Task + Startup entry)")
                    stopped_something = True
                except Exception as e:
                    log_warn(f"Could not fully uninstall Windows gateway: {e}")
        except Exception as e:
            log_warn(f"Could not check Windows gateway service: {e}")

    return stopped_something


# ============================================================================
# Windows-specific uninstall helpers
# ============================================================================
#
# The installer (``scripts/install.ps1``) does four Windows-only things that
# ``remove_path_from_shell_configs`` / ``remove_wrapper_script`` don't cover:
#
#   1. Sets User-scope env vars ``HERMES_HOME`` and ``HERMES_GIT_BASH_PATH``
#      via ``[Environment]::SetEnvironmentVariable(..., "User")``.  These
#      don't live in ~/.bashrc — they're in the Windows registry at
#      HKCU\Environment.
#   2. Prepends to User-scope ``PATH`` (same registry location) entries
#      like ``%LOCALAPPDATA%\hermes\git\cmd``, ``%LOCALAPPDATA%\hermes\git\bin``,
#      ``%LOCALAPPDATA%\hermes\git\usr\bin``, ``%LOCALAPPDATA%\hermes\node``.
#      Again not in any rc file — only accessible via the registry or the
#      .NET [Environment] API.
#   3. Downloads PortableGit to ``%LOCALAPPDATA%\hermes\git\`` and Node to
#      ``%LOCALAPPDATA%\hermes\node\`` as user-scoped, isolated copies.
#      These are ~200MB combined and serve no purpose after uninstall.
#   4. On the ``hermes dashboard`` + gateway paths, drops files into
#      ``%LOCALAPPDATA%\hermes\gateway-service\`` and sometimes
#      ``%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\`` — the
#      latter is handled by ``gateway_windows.uninstall()`` already.
#
# Running a PowerShell one-liner per operation is overkill and fragile on
# locked-down machines (Constrained Language Mode, restricted ExecutionPolicy).
# Direct registry writes via ``winreg`` work without spawning any subprocess
# and apply immediately for new shells (SendMessage WM_SETTINGCHANGE would
# be nicer but requires ctypes and buys us nothing — the user will log out
# or open a new terminal anyway).


def _hermes_path_markers(hermes_home: Path) -> list[str]:
    """Path-entry substrings that identify Hermes-owned User-PATH entries."""
    root = str(hermes_home).rstrip("\\/")
    # Match on prefix so sub-entries (git\cmd, git\bin, git\usr\bin, node, etc.)
    # all get swept.  Also match the bare hermes-agent install dir.
    markers = [root + "\\hermes-agent", root + "\\git", root + "\\node", root + "\\venv"]
    # Also match if HERMES_HOME was customised to somewhere else — find-and-nuke
    # any entry whose path component contains "hermes".  We don't want to catch
    # unrelated entries like "chermes-foo" or "ephermeral", so we look for
    # backslash-hermes as a word-ish boundary.
    return markers


def remove_path_from_windows_registry(hermes_home: Path) -> list[str]:
    """Strip Hermes-owned entries from User-scope PATH in the registry.

    Returns the list of removed path entries.  Operates on HKCU\\Environment,
    same key the installer wrote to via ``[Environment]::SetEnvironmentVariable``.
    """
    try:
        import winreg
    except ImportError:
        return []  # not on Windows, nothing to do

    removed: list[str] = []
    key_path = "Environment"
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0,
                            winreg.KEY_READ | winreg.KEY_WRITE) as key:
            try:
                path_value, path_type = winreg.QueryValueEx(key, "Path")
            except FileNotFoundError:
                return []
            # Preserve REG_EXPAND_SZ vs REG_SZ so unexpanded %VARS% survive.
            entries = [e for e in path_value.split(";") if e]
            markers = _hermes_path_markers(hermes_home)
            kept: list[str] = []
            for entry in entries:
                entry_norm = entry.rstrip("\\/")
                matched = any(entry_norm.lower().startswith(m.lower()) for m in markers)
                if matched:
                    removed.append(entry)
                else:
                    kept.append(entry)
            if removed:
                new_value = ";".join(kept)
                winreg.SetValueEx(key, "Path", 0, path_type, new_value)
    except OSError as e:
        log_warn(f"Could not edit User PATH in registry: {e}")
    return removed


def remove_hermes_env_vars_windows() -> list[str]:
    """Delete HERMES_HOME and HERMES_GIT_BASH_PATH from User-scope env vars."""
    try:
        import winreg
    except ImportError:
        return []

    removed: list[str] = []
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment", 0,
                            winreg.KEY_READ | winreg.KEY_WRITE) as key:
            for name in ("HERMES_HOME", "HERMES_GIT_BASH_PATH"):
                try:
                    winreg.QueryValueEx(key, name)
                except FileNotFoundError:
                    continue
                try:
                    winreg.DeleteValue(key, name)
                    removed.append(name)
                except OSError as e:
                    log_warn(f"Could not delete {name} from User env: {e}")
    except OSError as e:
        log_warn(f"Could not open User Environment key: {e}")
    return removed


def remove_portable_tooling_windows(hermes_home: Path) -> list[Path]:
    """Delete PortableGit and Node installs the Windows installer created under
    ``%LOCALAPPDATA%\\hermes\\``.  Only called on full uninstall; they're
    isolated from any system Git / Node so they cannot break other tools."""
    removed: list[Path] = []
    for sub in ("git", "node", "gateway-service"):
        target = hermes_home / sub
        if target.exists():
            try:
                shutil.rmtree(target, ignore_errors=False)
                removed.append(target)
            except Exception as e:
                log_warn(f"Could not remove {target}: {e}")
    return removed


# ============================================================================
# Desktop app uninstall helpers
# ============================================================================
#
# The desktop app (apps/desktop) is an Electron app built and optionally
# installed alongside the CLI.  It leaves artifacts in several places:
#
#   macOS:
#     /Applications/Hermes.app          (auto-moved on first launch)
#     Dock tile                          (pinned on first launch)
#     ~/Library/Application Support/Hermes/  (Electron userData)
#
#   Windows:
#     %APPDATA%\Hermes\                  (Electron userData)
#
#   All platforms (inside the install dir):
#     apps/desktop/release/              (electron-builder output)
#     apps/desktop/dist/                 (Vite renderer build)
#     apps/desktop/node_modules/         (desktop-only deps, ~150MB)
#
#   HERMES_HOME:
#     desktop-build-stamp.json           (content-hash skip stamp)
#
# The root node_modules/ is NOT removed — `npm ci` in the install dir
# rebuilds it cleanly, and the TUI also depends on it.

def _desktop_dir(project_root: Path) -> Path:
    """Return the apps/desktop directory inside the install root."""
    return project_root / "apps" / "desktop"


def _electron_user_data_dir() -> Path:
    """Return the platform-specific Electron userData directory for Hermes Desktop.

    Electron uses ``app.getPath('userData')`` which resolves to:
      - macOS:  ~/Library/Application Support/Hermes
      - Windows: %APPDATA%\\Hermes
      - Linux:   ~/.config/Hermes   (XDG_CONFIG_HOME if set)
    """
    import sys
    home = Path.home()
    if sys.platform == "darwin":
        return home / "Library" / "Application Support" / "Hermes"
    elif sys.platform == "win32":
        appdata = os.environ.get("APPDATA")
        if appdata:
            return Path(appdata) / "Hermes"
        return home / "AppData" / "Roaming" / "Hermes"
    else:
        xdg = os.environ.get("XDG_CONFIG_HOME")
        config_base = Path(xdg) if xdg else (home / ".config")
        return config_base / "Hermes"


def _unpin_from_dock() -> bool:
    """Remove the Hermes tile from the macOS Dock.

    Best-effort: mirrors the pin logic in main.cjs (``maybePinToDock``).
    We scan ``com.apple.dock persistent-apps`` for a file-reference URL
    pointing at ``/Applications/Hermes.app/`` and remove matching entries.
    Returns True if a tile was removed.
    """
    import sys
    if sys.platform != "darwin":
        return False

    try:
        # Read current Dock tiles — property-list encoded via ``defaults read``.
        result = subprocess.run(
            ["defaults", "read", "com.apple.dock", "persistent-apps"],
            capture_output=True, text=True, check=False,
        )
        if result.returncode != 0:
            return False

        current = result.stdout
        # The Dock stores tiles as file-reference URLs like:
        #   file:///Applications/Hermes.app/
        # We look for that pattern and nuke the whole <dict> containing it.
        hermes_marker = "Hermes.app"
        if hermes_marker not in current:
            return False

        # Use PlistBuddy to find and delete matching entries.
        # PlistBuddy is more reliable than trying to re-serialize the defaults
        # output ourselves. Probe indices until out-of-bounds — no need for
        # a separate count query; the PlistBuddy Print call fails on an
        # invalid index, which is our loop termination condition.
        removed = False
        idx = 0
        while True:
            entry = subprocess.run(
                ["/usr/libexec/PlistBuddy", "-c",
                 f"Print :persistent-apps:{idx}",
                 "~/Library/Preferences/com.apple.dock.plist"],
                capture_output=True, text=True, check=False,
            )
            if entry.returncode != 0:
                break  # out of bounds
            if hermes_marker in entry.stdout:
                subprocess.run(
                    ["/usr/libexec/PlistBuddy", "-c",
                     f"Delete :persistent-apps:{idx}",
                     "~/Library/Preferences/com.apple.dock.plist"],
                    capture_output=True, text=True, check=False,
                )
                removed = True
                # Don't increment — the array shifted down
            else:
                idx += 1

        if removed:
            # Force cfprefsd to flush our PlistBuddy edit back to disk before we
            # restart the Dock. We wrote com.apple.dock.plist directly, so the
            # running cfprefsd still holds the pre-delete copy in memory; a plain
            # `defaults read` makes it reload from disk. Skip this and `killall
            # Dock` races cfprefsd, reloads the stale (still-pinned) prefs, and
            # the tile reappears. (Mirrors the flush before the pin in main.cjs.)
            subprocess.run(
                ["defaults", "read", "com.apple.dock", "persistent-apps"],
                capture_output=True, check=False,
            )
            subprocess.run(["killall", "Dock"], capture_output=True, check=False)
        return removed

    except Exception as e:
        log_warn(f"Could not unpin Hermes from Dock: {e}")
        return False


def _kill_desktop_process() -> None:
    """Kill any running Hermes desktop (Electron) app process.

    Safe to call from the CLI uninstaller — the desktop binary is named
    ``Hermes`` (macOS / Linux AppImage) or ``Hermes.exe`` (Windows), while
    the CLI itself runs as ``python3``.  We never kill ourselves.

    Best-effort: if the process isn't running or the kill tool is
    unavailable, we silently continue (the rmtree below will still
    succeed for any files the dead process isn't holding open).
    """
    import sys
    try:
        if sys.platform == "darwin":
            # macOS: the Electron app binary inside Hermes.app is named
            # "Hermes" (CFBundleExecutable). The CLI runs as python3.
            subprocess.run(["killall", "Hermes"], capture_output=True, check=False)
        elif sys.platform == "win32":
            subprocess.run(
                ["taskkill", "/F", "/IM", "Hermes.exe"],
                capture_output=True, check=False,
            )
        elif sys.platform.startswith("linux"):
            # Heuristic for non-NixOS Linux: match the electron-builder
            # output path.  On NixOS the whole uninstall command is a
            # no-op (see run_uninstall), so this pattern is only ever
            # evaluated on conventional installs.
            subprocess.run(
                ["pkill", "-f", "apps/desktop/release/linux-unpacked/Hermes"],
                capture_output=True, check=False,
            )
    except Exception:
        pass  # not running or kill tool unavailable


def _remove_desktop_external_artifacts(
    project_root: Path, hermes_home: Path
) -> list[str]:
    """Remove desktop app artifacts that live OUTSIDE the install dir and
    HERMES_HOME: the macOS ``/Applications/Hermes.app`` bundle, its Dock pin,
    and the Electron userData directory.

    Returns a list of human-readable descriptions of what was removed.

    This is the shared external-cleanup path used by both the desktop-only
    uninstall (``remove_desktop_app``, which adds the in-tree artifacts on top)
    and the standard full/keep-data flow (whose ``rmtree(project_root)`` /
    ``rmtree(hermes_home)`` already sweep the in-tree pieces but never touch
    these external ones).
    """
    import sys
    removed: list[str] = []

    # Kill the desktop process first — on macOS the .app bundle can't be
    # removed while the binary inside it is running.
    _kill_desktop_process()

    # macOS: /Applications/Hermes.app and Dock pin
    if sys.platform == "darwin":
        app_bundle = Path("/Applications/Hermes.app")
        if app_bundle.is_dir():
            try:
                shutil.rmtree(app_bundle)
                log_success(f"Removed {app_bundle}")
                removed.append("/Applications/Hermes.app")
            except Exception as e:
                log_warn(f"Could not remove {app_bundle}: {e}")

        if _unpin_from_dock():
            log_success("Removed Hermes from the Dock")
            removed.append("Dock tile")

    # Electron userData (outside both project_root and hermes_home)
    user_data = _electron_user_data_dir()
    if user_data.exists():
        try:
            shutil.rmtree(user_data)
            log_success(f"Removed Electron userData ({user_data})")
            removed.append(f"Electron userData ({user_data})")
        except Exception as e:
            log_warn(f"Could not remove Electron userData ({user_data}): {e}")

    return removed


def remove_desktop_app(project_root: Path, hermes_home: Path) -> list[str]:
    """Remove the Hermes desktop app and all its artifacts.

    Returns a list of human-readable descriptions of what was removed.

    This does NOT remove the root node_modules/ (the TUI uses it too),
    the CLI install, or any user data in HERMES_HOME other than the
    desktop build stamp.
    """
    removed: list[str] = []
    desktop = _desktop_dir(project_root)

    # ── External artifacts (kill process, .app bundle, Dock pin, userData) ──
    # Shared with the standard uninstall flow — the single owner of every
    # removal target that lives outside the install dir / HERMES_HOME.
    removed.extend(_remove_desktop_external_artifacts(project_root, hermes_home))

    # ── Built artifacts inside install dir ────────────────────────
    for subdir in ("release", "dist", "node_modules"):
        target = desktop / subdir
        if target.exists():
            try:
                shutil.rmtree(target)
                label = f"apps/desktop/{subdir}/"
                log_success(f"Removed {target}")
                removed.append(label)
            except Exception as e:
                log_warn(f"Could not remove {target}: {e}")

    # ── Desktop build stamp in HERMES_HOME ────────────────────────
    stamp = hermes_home / "desktop-build-stamp.json"
    if stamp.exists():
        try:
            stamp.unlink()
            log_success(f"Removed {stamp}")
            removed.append("desktop-build-stamp.json")
        except Exception as e:
            log_warn(f"Could not remove {stamp}: {e}")

    return removed


def _is_windows() -> bool:
    import sys
    return sys.platform == "win32"


def _is_default_hermes_home(hermes_home: Path) -> bool:
    """Return True when ``hermes_home`` points at the default (non-profile) root."""
    try:
        from hermes_constants import get_default_hermes_root
        return hermes_home.resolve() == get_default_hermes_root().resolve()
    except Exception:
        return False


def _discover_named_profiles():
    """Return a list of ``ProfileInfo`` for every non-default profile, or ``[]``
    if profile support is unavailable or nothing is installed beyond the
    default root."""
    try:
        from hermes_cli.profiles import list_profiles
    except Exception:
        return []
    try:
        return [p for p in list_profiles() if not getattr(p, "is_default", False)]
    except Exception as e:
        log_warn(f"Could not enumerate profiles: {e}")
        return []


def _uninstall_profile(profile) -> None:
    """Fully uninstall a single named profile: stop its gateway service,
    remove its alias wrapper, and wipe its HERMES_HOME directory.

    We shell out to ``hermes -p <name> gateway stop|uninstall`` because
    service names, unit paths, and plist paths are all derived from the
    current HERMES_HOME and can't be easily switched in-process.
    """
    import sys as _sys
    name = profile.name
    profile_home = profile.path

    log_info(f"Uninstalling profile '{name}'...")

    # 1. Stop and remove this profile's gateway service.
    #    Use `python -m hermes_cli.main` so we don't depend on a `hermes`
    #    wrapper that may be half-removed mid-uninstall.
    hermes_invocation = [_sys.executable, "-m", "hermes_cli.main", "--profile", name]
    for subcmd in ("stop", "uninstall"):
        try:
            subprocess.run(
                hermes_invocation + ["gateway", subcmd],
                capture_output=True,
                text=True,
                timeout=60,
                check=False,
            )
        except subprocess.TimeoutExpired:
            log_warn(f"  Gateway {subcmd} timed out for '{name}'")
        except Exception as e:
            log_warn(f"  Could not run gateway {subcmd} for '{name}': {e}")

    # 2. Remove the wrapper alias script at ~/.local/bin/<name> (if any).
    alias_path = getattr(profile, "alias_path", None)
    if alias_path and alias_path.exists():
        try:
            alias_path.unlink()
            log_success(f"  Removed alias {alias_path}")
        except Exception as e:
            log_warn(f"  Could not remove alias {alias_path}: {e}")

    # 3. Wipe the profile's HERMES_HOME directory.
    try:
        if profile_home.exists():
            shutil.rmtree(profile_home)
            log_success(f"  Removed {profile_home}")
    except Exception as e:
        log_warn(f"  Could not remove {profile_home}: {e}")


def _run_desktop_uninstall(project_root: Path, hermes_home: Path, args) -> None:
    """Run the desktop-only uninstall flow.

    This is a focused uninstall that only removes the Electron desktop app
    and its artifacts — the CLI, gateway, configs, and data are untouched.
    """
    skip_confirm = getattr(args, "yes", False) or getattr(args, "skip_confirm", False)

    print()
    print(color("┌─────────────────────────────────────────────────────────┐", Colors.MAGENTA, Colors.BOLD))
    print(color("│         ⚕ Hermes Desktop Uninstaller                   │", Colors.MAGENTA, Colors.BOLD))
    print(color("└─────────────────────────────────────────────────────────┘", Colors.MAGENTA, Colors.BOLD))
    print()
    print(color("This will remove:", Colors.CYAN, Colors.BOLD))

    import sys
    if sys.platform == "darwin":
        print("  • /Applications/Hermes.app")
        print("  • Dock pin (if present)")
    print("  • apps/desktop/release/  (Electron app bundle)")
    print("  • apps/desktop/dist/     (Vite renderer)")
    print("  • apps/desktop/node_modules/  (desktop deps)")
    print("  • desktop-build-stamp.json")
    print("  • Electron userData (desktop settings)")
    print()
    print(color("The CLI, gateway, and all configs/data will be preserved.", Colors.GREEN))
    print()

    if not skip_confirm:
        try:
            confirm = input(f"Type '{color('yes', Colors.YELLOW)}' to confirm: ").strip().lower()
        except (KeyboardInterrupt, EOFError):
            print()
            print("Cancelled.")
            return
        if confirm != "yes":
            print()
            print("Uninstall cancelled.")
            return

    print()
    print(color("Uninstalling desktop app...", Colors.CYAN, Colors.BOLD))
    print()

    removed = remove_desktop_app(project_root, hermes_home)

    print()
    print(color("┌─────────────────────────────────────────────────────────┐", Colors.GREEN, Colors.BOLD))
    print(color("│              ✓ Desktop Uninstall Complete!              │", Colors.GREEN, Colors.BOLD))
    print(color("└─────────────────────────────────────────────────────────┘", Colors.GREEN, Colors.BOLD))
    print()

    if removed:
        print(color("Removed:", Colors.CYAN))
        for item in removed:
            print(f"  • {item}")
        print()

    print("To reinstall the desktop app later:")
    print(color("  hermes gui", Colors.DIM))
    print()
    print("Thank you for using Hermes Agent! ⚕")
    print()


def run_uninstall(args):
    """
    Run the uninstall process.
    
    Options:
    - Full uninstall: removes code + ~/.hermes/ (configs, data, logs)
    - Keep data: removes code but keeps ~/.hermes/ for future reinstall
    - Desktop only: removes only the desktop app (Electron, Dock pin, built artifacts)
    """
    # ── Managed installs (NixOS, Homebrew, etc.) ────────────────────
    # The package manager owns every file — our uninstaller has nothing
    # to remove and would only break the managed layout.  Bail early.
    from hermes_cli.config import is_managed, get_managed_update_command
    if is_managed():
        managed_cmd = get_managed_update_command() or "your package manager"
        print()
        print(color("⚠  Uninstall is not available for managed installs.", Colors.RED, Colors.BOLD))
        print(color("   Hermes is managed by your system package manager.", Colors.YELLOW))
        print(color(f"   To remove it: {managed_cmd}", Colors.YELLOW))
        print()
        return

    project_root = get_project_root()
    hermes_home = get_hermes_home()

    # ── Desktop-only fast path ────────────────────────────────────
    desktop_only = getattr(args, "desktop", False)
    if desktop_only:
        _run_desktop_uninstall(project_root, hermes_home, args)
        return

    # Detect named profiles when uninstalling from the default root —
    # offer to clean them up too instead of leaving zombie HERMES_HOMEs
    # and systemd units behind.
    is_default_profile = _is_default_hermes_home(hermes_home)
    named_profiles = _discover_named_profiles() if is_default_profile else []

    print()
    print(color("┌─────────────────────────────────────────────────────────┐", Colors.MAGENTA, Colors.BOLD))
    print(color("│            ⚕ Hermes Agent Uninstaller                  │", Colors.MAGENTA, Colors.BOLD))
    print(color("└─────────────────────────────────────────────────────────┘", Colors.MAGENTA, Colors.BOLD))
    print()
    
    # Show what will be affected
    print(color("Current Installation:", Colors.CYAN, Colors.BOLD))
    print(f"  Code:    {project_root}")
    print(f"  Config:  {hermes_home / 'config.yaml'}")
    print(f"  Secrets: {hermes_home / '.env'}")
    print(f"  Data:    {hermes_home / 'cron/'}, {hermes_home / 'sessions/'}, {hermes_home / 'logs/'}")
    print()

    if named_profiles:
        print(color("Other profiles detected:", Colors.CYAN, Colors.BOLD))
        for p in named_profiles:
            running = " (gateway running)" if getattr(p, "gateway_running", False) else ""
            print(f"  • {p.name}{running}: {p.path}")
        print()
    
    # Ask for confirmation
    print(color("Uninstall Options:", Colors.YELLOW, Colors.BOLD))
    print()
    print("  1) " + color("Keep data", Colors.GREEN) + " - Remove code only, keep configs/sessions/logs")
    print("     (Recommended - you can reinstall later with your settings intact)")
    print()
    print("  2) " + color("Full uninstall", Colors.RED) + " - Remove everything including all data")
    print("     (Warning: This deletes all configs, sessions, and logs permanently)")
    print()
    print("  3) " + color("Desktop only", Colors.CYAN) + " - Remove only the desktop app")
    print("     (Removes Electron app, Dock pin, and built artifacts; keeps CLI + data)")
    print()
    print("  4) " + color("Cancel", Colors.CYAN) + " - Don't uninstall")
    print()
    
    try:
        choice = input(color("Select option [1/2/3/4]: ", Colors.BOLD)).strip()
    except (KeyboardInterrupt, EOFError):
        print()
        print("Cancelled.")
        return
    
    if choice == "4" or choice.lower() in {"c", "cancel", "q", "quit", "n", "no"}:
        print()
        print("Uninstall cancelled.")
        return
    
    if choice == "3":
        _run_desktop_uninstall(project_root, hermes_home, args)
        return
    
    full_uninstall = (choice == "2")

    # When doing a full uninstall from the default profile, also offer to
    # remove any named profiles — stopping their gateway services, unlinking
    # their alias wrappers, and wiping their HERMES_HOME dirs. Otherwise
    # those leave zombie services and data behind.
    remove_profiles = False
    if full_uninstall and named_profiles:
        print()
        print(color("Other profiles will NOT be removed by default.", Colors.YELLOW))
        print(f"Found {len(named_profiles)} named profile(s): " +
              ", ".join(p.name for p in named_profiles))
        print()
        try:
            resp = input(color(
                f"Also stop and remove these {len(named_profiles)} profile(s)? [y/N]: ",
                Colors.BOLD
            )).strip().lower()
        except (KeyboardInterrupt, EOFError):
            print()
            print("Cancelled.")
            return
        remove_profiles = resp in {"y", "yes"}

    # Final confirmation
    print()
    if full_uninstall:
        print(color("⚠️  WARNING: This will permanently delete ALL Hermes data!", Colors.RED, Colors.BOLD))
        print(color("   Including: configs, API keys, sessions, scheduled jobs, logs", Colors.RED))
        if remove_profiles:
            print(color(
                f"   Plus {len(named_profiles)} profile(s): " +
                ", ".join(p.name for p in named_profiles),
                Colors.RED
            ))
    else:
        print("This will remove the Hermes code but keep your configuration and data.")
    
    print()
    try:
        confirm = input(f"Type '{color('yes', Colors.YELLOW)}' to confirm: ").strip().lower()
    except (KeyboardInterrupt, EOFError):
        print()
        print("Cancelled.")
        return
    
    if confirm != "yes":
        print()
        print("Uninstall cancelled.")
        return
    
    print()
    print(color("Uninstalling...", Colors.CYAN, Colors.BOLD))
    print()
    
    # 1. Stop and uninstall gateway service + kill standalone processes
    log_info("Checking for running gateway...")
    if not uninstall_gateway_service():
        log_info("No gateway service or processes found")
    
    # 2. Remove PATH entries from shell configs (POSIX) AND from the Windows
    #    User-scope registry.  Both helpers no-op on the wrong platform so we
    #    can safely call them unconditionally.
    log_info("Removing PATH entries from shell configs...")
    removed_configs = remove_path_from_shell_configs()
    if removed_configs:
        for config in removed_configs:
            log_success(f"Updated {config}")
    else:
        log_info("No PATH entries found to remove in shell rc files")

    if _is_windows():
        log_info("Removing PATH entries from Windows User environment...")
        # Expand %LOCALAPPDATA% etc. in hermes_home so the marker matching is
        # against fully resolved paths — installer writes literal strings
        # like C:\Users\<u>\AppData\Local\hermes\git\cmd, not %LOCALAPPDATA%.
        removed_path_entries = remove_path_from_windows_registry(Path(os.path.expandvars(str(hermes_home))))
        if removed_path_entries:
            for entry in removed_path_entries:
                log_success(f"Removed from User PATH: {entry}")
        else:
            log_info("No Hermes-owned PATH entries in User environment")

        log_info("Removing HERMES_HOME / HERMES_GIT_BASH_PATH User env vars...")
        removed_env = remove_hermes_env_vars_windows()
        if removed_env:
            for name in removed_env:
                log_success(f"Removed User env var: {name}")
        else:
            log_info("No Hermes-set User env vars to remove")
    
    # 3. Remove wrapper script
    log_info("Removing hermes command...")
    removed_wrappers = remove_wrapper_script()
    if removed_wrappers:
        for wrapper in removed_wrappers:
            log_success(f"Removed {wrapper}")
    else:
        log_info("No wrapper script found")

    # 3b. Remove node/npm/npx symlinks the installer left in ~/.local/bin
    #     (only when they still point into this Hermes home's node dir, so we
    #     never clobber an existing nvm / user-managed Node).
    log_info("Removing Hermes-managed node/npm/npx symlinks...")
    removed_node_links = remove_node_symlinks(hermes_home)
    if removed_node_links:
        for link in removed_node_links:
            log_success(f"Removed {link}")
    else:
        log_info("No Hermes-managed node/npm/npx symlinks found")

    # 3c. Remove desktop app artifacts that live OUTSIDE the install dir
    #     and HERMES_HOME (the .app bundle in /Applications, the Dock tile,
    #     and Electron userData). The install dir's apps/desktop/ subtree is
    #     removed by step 4; these external ones need separate cleanup.
    log_info("Removing desktop app artifacts...")
    _remove_desktop_external_artifacts(project_root, hermes_home)
    
    # 4. Remove installation directory (code)
    log_info("Removing installation directory...")
    
    # Check if we're running from within the install dir
    # We need to be careful here
    try:
        if project_root.exists():
            # If the install is inside ~/.hermes/, just remove the hermes-agent subdir
            if hermes_home in project_root.parents or project_root.parent == hermes_home:
                shutil.rmtree(project_root)
                log_success(f"Removed {project_root}")
            else:
                # Installation is somewhere else entirely
                shutil.rmtree(project_root)
                log_success(f"Removed {project_root}")
    except Exception as e:
        log_warn(f"Could not fully remove {project_root}: {e}")
        log_info("You may need to manually remove it")

    # 4b. Remove Windows-only installer artifacts that are NOT user data:
    #     PortableGit, bundled Node, gateway-service dir.  Installer put them
    #     under HERMES_HOME but they're install tooling, not config — safe to
    #     remove even in "keep data" mode.  If we're doing a full uninstall
    #     the step-5 rmtree(hermes_home) would sweep them anyway; calling
    #     this helper there is a no-op since they'll already be gone.
    if _is_windows():
        log_info("Removing Windows installer artifacts (PortableGit, Node, gateway-service)...")
        removed_artifacts = remove_portable_tooling_windows(hermes_home)
        if removed_artifacts:
            for path in removed_artifacts:
                log_success(f"Removed {path}")
        else:
            log_info("No Windows installer artifacts to remove")
    
    # 5. Optionally remove ~/.hermes/ data directory (and named profiles)
    if full_uninstall:
        # 5a. Stop and remove each named profile's gateway service and
        #     alias wrapper. The profile HERMES_HOME dirs live under
        #     ``<default>/profiles/<name>/`` and will be swept away by the
        #     rmtree below, but services + alias scripts live OUTSIDE the
        #     default root and have to be cleaned up explicitly.
        if remove_profiles and named_profiles:
            for prof in named_profiles:
                _uninstall_profile(prof)

        log_info("Removing configuration and data...")
        try:
            if hermes_home.exists():
                shutil.rmtree(hermes_home)
                log_success(f"Removed {hermes_home}")
        except Exception as e:
            log_warn(f"Could not fully remove {hermes_home}: {e}")
            log_info("You may need to manually remove it")
    else:
        log_info(f"Keeping configuration and data in {hermes_home}")
    
    # Done
    print()
    print(color("┌─────────────────────────────────────────────────────────┐", Colors.GREEN, Colors.BOLD))
    print(color("│              ✓ Uninstall Complete!                      │", Colors.GREEN, Colors.BOLD))
    print(color("└─────────────────────────────────────────────────────────┘", Colors.GREEN, Colors.BOLD))
    print()
    
    if not full_uninstall:
        print(color("Your configuration and data have been preserved:", Colors.CYAN))
        print(f"  {hermes_home}/")
        print()
        print("To reinstall later with your existing settings:")
        if _is_windows():
            print(color("  iex (irm https://hermes-agent.nousresearch.com/install.ps1)", Colors.DIM))
        else:
            print(color("  curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash", Colors.DIM))
        print()

    if _is_windows():
        print(color("Open a new terminal (PowerShell / Windows Terminal) to pick up", Colors.YELLOW))
        print(color("the updated User PATH and environment variables.", Colors.YELLOW))
    else:
        print(color("Reload your shell to complete the process:", Colors.YELLOW))
        print("  source ~/.bashrc  # or ~/.zshrc")
    print()
    print("Thank you for using Hermes Agent! ⚕")
    print()
