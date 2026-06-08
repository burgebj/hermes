# Fix: Use _resolve_detached_python for uv venvs in .cmd generation

Fixes #30308

## Problem

`_build_gateway_cmd_script()` uses `_derive_venv_pythonw()` which only finds
the uv shim (~44KB) that spawns python.exe with console. The real pythonw.exe
is at the base Python installation path.

## Solution

In `_build_gateway_cmd_script()`, replace:
```python
pythonw_path = _derive_venv_pythonw(python_path)
```

With:
```python
pythonw_path, _, extra_pythonpath = _resolve_detached_python(python_path)
```

And add PYTHONPATH to the generated .cmd when uv is detected:
```python
if extra_pythonpath:
    pythonpath = os.pathsep.join([str(Path(working_dir))] + extra_pythonpath)
    lines.append(f'set "PYTHONPATH={pythonpath}"')
```

This reuses the existing `_resolve_detached_python()` function that already
handles uv detection correctly.
