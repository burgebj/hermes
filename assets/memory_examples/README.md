# Example Memory Files

These are example `MEMORY.md` and `USER.md` files for reference.

## Usage

Copy these to your Hermes memory directory:

```bash
cp assets/memory_examples/MEMORY.md.example ~/.hermes/memories/MEMORY.md
cp assets/memory_examples/USER.md.example ~/.hermes/memories/USER.md
```

## Format

- Entry delimiter: `§` (section sign)
- Each entry can be multiline
- Files are injected into the system prompt as a frozen snapshot at session start
- Mid-session writes update files immediately but do NOT change the in-session system prompt

## Files

- `MEMORY.md.example` — agent's personal notes and observations
- `USER.md.example` — what the agent knows about the user