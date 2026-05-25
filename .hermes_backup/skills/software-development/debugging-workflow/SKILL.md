---
name: debugging-workflow
description: General debugging workflows and techniques — dynamic linking issues, shared library debugging, symbol resolution, and systematic root cause analysis for Linux/GPU software.
version: 1.0.0
author: Hermes Agent
license: MIT
---

# Debugging Workflow

Umbrella skill for general debugging techniques. Covers shared library debugging, dynamic linking, symbol resolution errors, and systematic root cause analysis approaches for Linux software and GPU-accelerated applications.

## Shared Library / Dynamic Linking Debugging

See `references/debug-shared-libs.md` for the full detailed guide on:
- `undefined symbol` errors
- `cannot open shared object file` errors
- SONAME mismatches
- DT_NEEDED chain analysis
- dlopen / lazy loading issues
- Container/Docker image linker problems

### Quick Reference: Common Fixes

| Error | Likely Cause | Quick Fix |
|-------|-------------|-----------|
| `undefined symbol: <name>` | Library version mismatch | Check `nm -D` / `objdump -T` on loaded libs |
| `cannot open shared object file` | Library not installed | `ldd <binary>` then `apt install` |
| `version 'GLIBC_XX' not found` | glibc mismatch | Rebuild against older glibc or upgrade OS |
| `wrong ELF class` | 32/64 bit mismatch | Use correct architecture library |

### Key Tools
```bash
ldd <binary>              # List dynamic dependencies
objdump -p <so> | grep -E 'NEEDED|SONAME'  # Check SONAME
nm -D <so> | grep <sym>   # Search for symbol in library
readelf -d <so> | grep SONAME  # Alternative SONAME check
LD_DEBUG=libs,files <program>  # Trace loader activity
strace -e openat -f <program> 2>&1 | grep '\.so'  # Watch .so loading
```

## Systematic Root Cause Analysis (4-Phase)

For complex bugs, follow a structured approach:

1. **Understand** — Reproduce the bug, gather exact error/stack trace, understand expected vs actual behavior
2. **Isolate** — Narrow the scope (which module, which input, which environment variable)
3. **Diagnose** — Form and test hypotheses with minimal reproduction
4. **Fix & Verify** — Apply targeted fix, verify with the original repro case, add regression guard

## Pitfalls

- **`ldd` on foreign architecture binaries** gives misleading results — use `readelf -d` instead
- **Version scripts / symbol visibility** — `nm -D` may show a symbol but it's marked `GLIBC_PRIVATE` or hidden visibility
- **`LD_PRELOAD` interference** can intercept symbols in unexpected ways
- **glibc 2.34+ merged libpthread/libdl** — stub libs; undefined pthread symbols mean binary wasn't linked with `-lpthread`
- **Bazel/Nix/Conda environments** have their own ld.so wrappers/RPATH — check `patchelf --print-rpath` or `chrpath -l`
- Don't reproduce errors in a new container or rebuild from source unless the user explicitly asks for it — diagnose from the error message first
