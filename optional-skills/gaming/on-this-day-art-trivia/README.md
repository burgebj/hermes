# on-this-day-art-trivia (skill)

Skill component of the `on-this-day-art-trivia` package. The skill is the
core engine; the **hook** at `hook/on-this-day-art-trivia/` and the
**plugin** at `plugin/on_this_day_art_trivia/` wire it into Hermes.

## CLI

```
python -m scripts.challenge start --chat-id 123 --user-id 99 --scope dm
python -m scripts.challenge guess --chat-id 123 --user-id 99 --text "Ali refused the draft"
python -m scripts.challenge hint  --chat-id 123
python -m scripts.challenge reveal --chat-id 123 --user-id 99
python -m scripts.challenge stats --user-id 99
python -m scripts.challenge daily            # cron entry point
```

The CLI is the same surface the hook and plugin call into.

## Direct Python use

```python
from scripts import challenge
res = challenge.start_challenge(
    platform="telegram",
    chat_id="123",
    user_id="99",
    user_display_name="alice",
    scope="dm",
)
print(res.surface_caption)            # "April 28\nHouston, Texas, United States"
print(res.image_prompt)               # spoiler-safe prompt
```

## State

`~/.hermes/data/on-this-day-art-trivia/trivia.db` — created on first use,
WAL-mode, foreign keys on, atomic transactions.

## Cron entry (daily delivery)

Add this routine to your Hermes cron config:

```yaml
- name: otdat-daily
  schedule: "0 8 * * *"     # 08:00 local time
  command: |
    cd ~/.hermes/skills/on-this-day-art-trivia &&
    python -m scripts.challenge daily
```
