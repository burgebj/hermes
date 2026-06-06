---
title: "Blender Mcp — Керуй Blender безпосередньо з Hermes через socket‑з’єднання з addon blender-mcp"
sidebar_label: "Blender Mcp"
description: "Керуй Blender безпосередньо з Hermes через socket‑з’єднання до blender-mcp addon"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Blender MCP

Керуйте Blender безпосередньо з Hermes через сокет‑з’єднання з аддоном **blender-mcp**. Створюйте 3D‑об’єкти, матеріали, анімації та виконуйте довільний код Blender Python (bpy). Використовуйте, коли користувач хоче створити або змінити будь‑що в Blender.

## Skill metadata

| | |
|---|---|
| Source | Optional — install with `hermes skills install official/creative/blender-mcp` |
| Path | `optional-skills/creative/blender-mcp` |
| Version | `1.0.0` |
| Author | alireza78a |
| Platforms | linux, macos, windows |

## Reference: full SKILL.md

:::info
The following is the complete skill definition that Hermes loads when this skill is triggered. This is what the agent sees as instructions when the skill is active.
:::

# Blender MCP

Керуйте запущеним екземпляром Blender з Hermes через сокет на TCP‑порті 9876.

## Setup (one-time)

### 1. Install the Blender addon

```bash
curl -sL https://raw.githubusercontent.com/ahujasid/blender-mcp/main/addon.py -o ~/Desktop/blender_mcp_addon.py
```

У Blender:
`Edit > Preferences > Add-ons > Install` → виберіть **blender_mcp_addon.py**
Увімкніть **"Interface: Blender MCP"**.

### 2. Start the socket server in Blender

Натисни **N** у вікні перегляду Blender, щоб відкрити бічну панель.
Знайди вкладку **"BlenderMCP"** і натисни **"Start Server"**.

### 3. Verify connection

```bash
nc -z -w2 localhost 9876 && echo "OPEN" || echo "CLOSED"
```

## Protocol

Plain UTF-8 JSON over TCP — без префікса довжини.

**Send:** `{"type": "<command>", "params": {<kwargs>}}`
**Receive:** `{"status": "success", "result": <value>}`
             `{"status": "error",   "message": "<reason>"}`

## Available Commands

| type                    | params            | description                     |
|-------------------------|-------------------|---------------------------------|
| execute_code            | code (str)        | Run arbitrary bpy Python code   |
| get_scene_info          | (none)            | List all objects in scene       |
| get_object_info         | object_name (str) | Details on a specific object    |
| get_viewport_screenshot | (none)            | Screenshot of current viewport  |

## Python Helper

Use this inside `execute_code` tool calls:

    import socket, json

```python
def blender_exec(code: str, host="localhost", port=9876, timeout=15):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, port))
    s.settimeout(timeout)
    payload = json.dumps({"type": "execute_code", "params": {"code": code}})
    s.sendall(payload.encode("utf-8"))
    buf = b""
    while True:
        try:
            chunk = s.recv(4096)
            if not chunk:
                break
            buf += chunk
            try:
                json.loads(buf.decode("utf-8"))
                break
            except json.JSONDecodeError:
                continue
        except socket.timeout:
            break
    s.close()
    return json.loads(buf.decode("utf-8"))
```

## Common bpy Patterns

### Clear scene
```python
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()
```

### Add mesh objects
```python
bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(0, 0, 0))
bpy.ops.mesh.primitive_cube_add(size=2, location=(3, 0, 0))
bpy.ops.mesh.primitive_cylinder_add(radius=0.5, depth=2, location=(-3, 0, 0))
```

### Create and assign material
```python
mat = bpy.data.materials.new(name="MyMat")
mat.use_nodes = True
bsdf = mat.node_tree.nodes.get("Principled BSDF")
bsdf.inputs["Base Color"].default_value = (R, G, B, 1.0)
bsdf.inputs["Roughness"].default_value = 0.3
bsdf.inputs["Metallic"].default_value = 0.0
obj.data.materials.append(mat)
```

### Keyframe animation
```python
obj.location = (0, 0, 0)
obj.keyframe_insert(data_path="location", frame=1)
obj.location = (0, 0, 3)
obj.keyframe_insert(data_path="location", frame=60)
```

### Render to file
```python
bpy.context.scene.render.filepath = "/tmp/render.png"
bpy.context.scene.render.engine = 'CYCLES'
bpy.ops.render.render(write_still=True)
```

## Pitfalls

- Перевіряй, чи відкритий сокет перед запуском (`nc -z localhost 9876`).
- Сервер аддону треба запускати в кожній сесії Blender (N‑панель → BlenderMCP → Connect).
- Діли складні сцени на кілька менших викликів `execute_code`, щоб уникнути тайм‑аутів.
- Шлях виводу рендеру має бути абсолютним (`/tmp/...`), а не відносним.
- `shade_smooth()` вимагає, щоб об’єкт був вибраний і перебував в режимі Object.