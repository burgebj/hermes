---
name: python-package-management
description: Python dependency management with Poetry — add, update, configure packages
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [python, poetry, pyproject, dependency]
    related_skills: []
---

# Python Package Management

## Style & Interaction Preferences

- USER PREFERENCE: When the user asks a package-management question, respond with ONLY the command(s) or configuration snippet needed. Do NOT include explanations, context, or "you might also want to..." unless explicitly asked. The user will request elaboration if needed.
- TOOLCHAIN: Default to Poetry for dependency management, pyproject.toml for configuration. Never suggest pip freeze, requirements.txt, or setup.py unless user signals an older project.
- PITFALL: Do not offer alternative approaches (e.g., "you could also use pip or Conda") unless user asks. Choose the standard Poetry route and deliver it as a single, executable block.

## Common Commands

```bash
# Add a dependency
poetry add <package>

# Add a dev dependency
poetry add --group dev <package>

# Update all dependencies
poetry update

# Update a specific package
poetry update <package>

# Show outdated packages
poetry show --outdated

# Export requirements.txt (for CI/CD)
poetry export --without-hashes -o requirements.txt

# Build and publish
poetry build
poetry publish
```
