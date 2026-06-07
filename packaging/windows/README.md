# Windows Packaging

Hermes native Windows distribution starts with a reviewed release zip plus
Winget manifests. This keeps packaging separate from the installer itself:
`scripts/install.ps1` remains the canonical bootstrap path, while release
maintainers get reproducible artifacts to upload and submit to Winget.

Build the local artifacts:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File packaging\windows\build-windows-package.ps1
```

Outputs are written to `dist/windows/`:

- `hermes-agent-windows-<version>.zip`
- `hermes-agent-windows-<version>.zip.sha256`
- `winget/NousResearch.HermesAgent*.yaml`

The zip intentionally contains only bootstrap material:

- `scripts/install.ps1`
- `scripts/install.cmd`
- `scripts/windows-sandbox-validate.ps1`
- `scripts/windows-sandbox-smoke.ps1`
- `README.md`
- `website/docs/user-guide/windows-native.md`

Release flow:

1. Run the build script.
2. Upload the zip and SHA256 file to the GitHub release.
3. Run a clean Windows Sandbox validation against the exact release branch/tag.
4. Review the rendered Winget manifests under `dist/windows/winget/`.
5. Submit the manifests to `microsoft/winget-pkgs`.

The Winget manifest uses the zip as an `InstallerType: zip` package with a
nested portable installer pointing at `scripts/install.cmd`. It is a template
rendered with the release URL and SHA256; do not submit placeholder manifests.
