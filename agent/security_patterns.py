"""Shared heuristic prompt-injection scanner patterns.

These patterns are intentionally conservative: context files and durable memory
entries are injected into the system prompt, so suspicious instruction override
phrases should be blocked even when they contain extra filler words.
"""

# Match zero or more simple words between anchor terms, e.g.
# "ignore ALL prior project instructions" or "disregard any and all rules".
_OPTIONAL_WORDS = r'(?:\w+\s+)*'

IGNORE_INSTRUCTIONS_PATTERN = (
    rf'ignore\s+{_OPTIONAL_WORDS}'
    rf'(?:previous|all|above|prior)\s+{_OPTIONAL_WORDS}instructions'
)

DISREGARD_RULES_PATTERN = (
    rf'disregard\s+{_OPTIONAL_WORDS}'
    rf'(?:your|all|any)\s+{_OPTIONAL_WORDS}(?:instructions|rules|guidelines)'
)
