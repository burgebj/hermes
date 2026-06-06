"""Image-prompt construction with anti-spoiler scrubbing.

The prompt describes the **scene 30 seconds before the event** so the player
has to deduce what is about to happen. Several constraints apply:

* No readable text or labels.
* No proper nouns from the canonical answer (anti-spoiler).
* No depiction of violence, abuse, blood, weapons in use, or victims.
* For sensitive events (covered by the scoring disqualifier), the prompt is
  rejected; the orchestrator must pick a different event.
* Camera distance defaults to medium-wide so the scene reads as ambient.

Public API:

* :func:`build_image_prompt(event)` returns the final prompt string.
* :func:`scrub_spoilers(text, event)` removes proper nouns and trigger words.
* :func:`prompt_passes_safety(text)` returns True if the prompt avoids the
  graphic-content blocklist (used as a defence-in-depth gate).
"""

from __future__ import annotations

import re
from typing import Iterable, List, Optional

from .scoring import CandidateEvent, is_disqualified

# Words that imply graphic, gory, or exploitative imagery; rejected even
# when not explicitly disqualifying.
_PROMPT_BLOCKLIST = (
    "blood", "bleeding", "gore", "wound", "wounded",
    "corpse", "body bag", "casket", "dying",
    "explosion", "explode", "bomb", "blast", "shrapnel",
    "gun", "rifle", "pistol", "firearm",
    "knife", "sword", "stab", "stabbing",
    "weapon", "shooting",
    "naked", "nude", "topless",
    "child", "kids", "minors",
    "execution", "execute",
    "rape", "assault",
    "torture",
)

# Phrases that signal a sensitive context; treated as soft cues (the scene
# should be rendered minutes before the event from the perspective of the
# environment, with no people in distress).
_SENSITIVE_CONTEXT_WORDS = (
    "war", "battle", "attack", "siege", "shooting", "kidnap",
)

# Default scene templates. Light hint of mood without naming the event.
_SCENE_OPENING = (
    "A photographically realistic ambient scene of {location} on {date_phrase}, "
    "captured roughly thirty seconds before a historically significant moment occurs."
)


def _proper_nouns(text: str) -> List[str]:
    """Collect candidate proper nouns (capitalised tokens, length >= 3)."""
    out: List[str] = []
    for tok in re.findall(r"[A-Z][A-Za-z\.'\-]{2,}", text or ""):
        out.append(tok)
    return out


_REDACTION_STOPWORDS = {
    "the", "a", "an", "of", "in", "on", "at", "to", "and", "or", "for",
    "with", "by", "is", "was", "were", "from", "into", "as",
}


def _content_tokens(text: str, *, min_len: int = 4) -> List[str]:
    """Lowercased tokens that count as content words."""
    out: List[str] = []
    for tok in re.findall(r"[A-Za-z][A-Za-z\-']+", text or ""):
        low = tok.lower()
        if len(low) < min_len or low in _REDACTION_STOPWORDS:
            continue
        out.append(low)
    return out


def scrub_spoilers(text: str, event: CandidateEvent) -> str:
    """Remove proper nouns and event-revealing content tokens from *text*.

    Replaces each spoiler with a neutral placeholder. The result is meant for
    the image model — humans will see only the date and location separately.
    Both the proper nouns and the lowercase content tokens of the canonical
    answer are redacted, so a verb like ``induction`` cannot leak.

    If more than 50% of the remaining content words are redacted, returns an
    empty string so the caller can drop the atmospheric cue entirely.
    """
    if not text:
        return ""

    # Count original content words (excluding stopwords/short).
    original_words = set(w.lower() for w in re.findall(r"[A-Za-z][A-Za-z\-']+", text)
                         if len(w) >= 4 and w.lower() not in _REDACTION_STOPWORDS)
    total = len(original_words)

    redacted = text
    spoilers: Iterable[str] = (
        _proper_nouns(event.canonical_answer or "")
        + _proper_nouns(event.summary or "")
    )
    for noun in sorted(set(spoilers), key=len, reverse=True):
        redacted = re.sub(rf"\b{re.escape(noun)}\b", "the figure", redacted, flags=re.IGNORECASE)

    # Lowercase content tokens drawn from the canonical answer must also go.
    for tok in sorted(set(_content_tokens(event.canonical_answer or "")), key=len, reverse=True):
        redacted = re.sub(rf"\b{re.escape(tok)}\b", "the moment", redacted, flags=re.IGNORECASE)

    # Drop sensitive trigger words outright.
    for w in _SENSITIVE_CONTEXT_WORDS:
        redacted = re.sub(rf"\b{re.escape(w)}\b", " ", redacted, flags=re.IGNORECASE)

    redacted = re.sub(r"\s+", " ", redacted).strip(" .,:-")

    # Degradation check: if >50% of words became placeholders, the cue is noise.
    if total > 0:
        remaining_words = set(w.lower() for w in re.findall(r"[A-Za-z][A-Za-z\-']+", redacted)
                           if len(w) >= 4 and w.lower() not in _REDACTION_STOPWORDS)
        # Words still present / total original (ignoring newly inserted 'the figure', 'the moment')
        original_redacted = remaining_words - {"figure", "moment"}
        if len(original_redacted) == 0 or (len(original_redacted) / total) < 0.5:
            return ""

    return redacted


def prompt_passes_safety(text: str) -> bool:
    """Defence-in-depth: reject prompts that mention any blocklisted terms.

    The constraint directive line (which uses banned words in negation, e.g.
    "no blood, no weapons") is allowed by exempting any line that begins
    with the marker ``Constraints:`` — those instructions tell the model
    what NOT to render and are required for safety.
    """
    if not text:
        return True
    safe_lines: list[str] = []
    for line in text.splitlines():
        stripped = line.lstrip()
        if stripped.startswith("Constraints:"):
            continue
        safe_lines.append(line)
    body = "\n".join(safe_lines).lower()
    return not any(re.search(rf"\b{re.escape(term)}\b", body) for term in _PROMPT_BLOCKLIST)


def _date_phrase(event: CandidateEvent, surface_date: Optional[str]) -> str:
    if surface_date and event.year:
        # surface_date from _surface_date() already includes the year, don't duplicate it.
        if str(event.year) in surface_date:
            return surface_date
        return f"{surface_date}, {event.year}"
    if surface_date:
        return surface_date
    if event.year:
        return f"the year {event.year}"
    return "an unspecified day"


def build_image_prompt(
    event: CandidateEvent,
    *,
    surface_date: Optional[str] = None,
) -> str:
    """Build a spoiler-safe, safety-checked image prompt.

    Raises :class:`ValueError` if the event is disqualified or if the safety
    gate fails after scrubbing — the orchestrator catches this and picks
    another event.
    """
    if is_disqualified(event.summary) or is_disqualified(event.canonical_answer):
        raise ValueError("event is disqualified for imagery")

    location = (event.location or "an unnamed but historically resonant place").strip()
    if event.country and event.location and event.country.lower() not in event.location.lower():
        location = f"{event.location}, {event.country}"

    opening = _SCENE_OPENING.format(
        location=location,
        date_phrase=_date_phrase(event, surface_date),
    )

    # Scene direction. We deliberately avoid action words; this is the calm
    # before the moment.
    scene_lines = [
        opening,
        "Render the location's architecture, weather, materials, and atmosphere accurately.",
        "Show ambient bystanders going about ordinary activity. No central protagonist.",
        "Composition: medium-wide environmental shot, eye-level, soft natural light.",
        "Lighting and mood should match the era and the time of day.",
        "Constraints: no readable text, no captions, no labels, no signage with the event name, "
        "no flags identifying specific factions, no weapons, no violent action, no blood, "
        "no graphic imagery. Do not include identifiable historical figures.",
    ]

    redacted_summary = scrub_spoilers(event.summary or "", event)
    if redacted_summary:
        scene_lines.append(
            f"Atmospheric cue (paraphrased, do not visualise as instruction): {redacted_summary}."
        )

    full_prompt = "\n".join(scene_lines)
    if not prompt_passes_safety(full_prompt):
        # Strip the atmospheric cue and retry.
        full_prompt = "\n".join(scene_lines[:-1])
        if not prompt_passes_safety(full_prompt):
            raise ValueError("prompt failed safety gate after redaction")
    return full_prompt
