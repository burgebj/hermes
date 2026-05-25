Debug shared libraries / dynamic linking / symbol-loading issues on Linux.

Full detailed guide covering missing symbols, SONAME mismatches, DT_NEEDED chains, LD_LIBRARY_PATH ordering, dlopen issues, and container/Docker-image linker problems.

## Quick Diagnostic Flow

1. Get exact error message
2. `ldd <binary>` — check for missing dependencies
3. `objdump -p <binary> | grep -E 'NEEDED|SONAME'` — check expected SONAMEs
4. `nm -D /usr/lib/x86_64-linux-gnu/*.so 2>/dev/null | grep <symbol>` — find where a symbol lives
5. `readelf -d <so> | grep SONAME` — check actual SONAME of installed lib
6. If dlopen crash: `LD_DEBUG=libs,files <program> 2>&1 | tail -50`

## Common Causes & Fixes

| Cause | Fix |
|-------|-----|
| Library not installed | `apt install` or copy .so |
| Wrong SONAME | Symlink: `ln -s libfoo.so.2 libfoo.so.1` (if ABI compatible) |
| Conflicting LD_LIBRARY_PATH | Check order; remove stale copies |
| Missing versioned symbol | Rebuild against installed lib version |
| dlopen dependency not available | Install transitive lib or set LD_LIBRARY_PATH |
| Weak/hidden symbol | Check `objdump -T` for `GLIBC_PRIVATE` |

## Container-Specific

- Multi-stage build copies that miss transitive .so files
- `apt upgrade` bumping lib past what binary expects
- Different lib paths (e.g., `/usr/lib64/` vs `/usr/lib/x86_64-linux-gnu/`)

## Pitfalls

- `ldd` on foreign architecture binaries → use `readelf -d`
- glibc 2.34+ merged libpthread/libdl into libc
- Bazel/Nix/Conda have their own ld.so wrappers — check `patchelf --print-rpath`
- LD_PRELOAD can intercept symbols in unexpected ways
