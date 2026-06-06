"""Event scoring for the on-this-day-art-trivia skill.

Each candidate event coming from a source adapter is scored against the
rubric below. The challenge orchestrator picks the highest-scoring event
that also passes the safety floor.

Scoring rubric (all additive; higher is better):

* +30  has a specific named location (city/country)
* +20  has a year in [-3000, present]
* +20  visually depictable (rooms, buildings, vehicles, crowds, ships,
       documents being signed, ceremonies, public squares, vehicles, etc.)
* +20  recognised historic significance (in the curated whitelist of
       categories: war/peace, treaties, coronations, inventions, scientific
       milestones, civil-rights moments, exploration, founding events,
       major court rulings, sports world-firsts)
* +10  guessable: canonical answer is a discrete event-noun-phrase
* −40  birthday entries (penalty heavy — they are rarely guessable)
* −60  death/obituary-only entries
* −30  obscure local trivia
* −1000 disqualifying: requires graphic / exploitative imagery
       (sexual assault, child harm, executions, mutilation, terror attack
       death tolls, mass murder visuals, gore)

Events scoring < 50 are dropped. Events with the disqualifying flag are
hard-rejected even if their additive score is high.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence

# --------------------------------------------------------------------------- #
# Inputs
# --------------------------------------------------------------------------- #

@dataclass
class CandidateEvent:
    """A normalised event from any source adapter."""
    summary: str                          # one-sentence description
    canonical_answer: str                 # short event noun phrase
    year: Optional[int] = None
    location: Optional[str] = None
    country: Optional[str] = None
    category: Optional[str] = None        # 'birth', 'death', 'event', etc.
    source: Optional[str] = None
    raw: Dict[str, object] = field(default_factory=dict)


# Visual-depiction lexicon. Words present in the event summary suggest a
# scene that can be illustrated without spoilers.
_VISUAL_WORDS = (
    "battle", "treaty", "signed", "signing", "coronation", "crowned",
    "flight", "voyage", "expedition", "ship", "vessel", "fleet", "harbor",
    "harbour", "ceremony", "parade", "crowd", "rally", "stadium",
    "court", "courthouse", "trial", "verdict", "speech", "address",
    "summit", "meeting", "assembly", "convention", "march",
    "launch", "rocket", "satellite", "moon", "spacecraft",
    "invention", "patent", "demonstration", "first performance",
    "premiere", "opened", "opening", "founding", "founded",
    "expedition", "discovery", "earthquake", "eruption", "storm", "flood",
    "election", "inauguration", "festival",
)

# High-significance categories (broad lexicon).
_SIGNIFICANT_WORDS = (
    "war", "peace", "treaty", "constitution", "independence", "republic",
    "kingdom", "empire", "revolution", "liberation", "abolition",
    "founding", "inauguration", "coronation", "election",
    "supreme court", "ruling", "patent", "invention", "discovery",
    "first flight", "first manned", "world record", "olympic",
    "civil rights", "suffrage", "vote",
)

# Disqualifying phrases. If any of these appear in the summary, the event
# is rejected outright — both for safety and because the imagery would be
# inappropriate for a casual trivia game.
_DISQUALIFYING_PHRASES = (
    "sexual assault", "raped", "rape ", "rape.", "molested",
    "child abuse", "child sex", "pedophile", "paedophile",
    "execution of", "executed by", "beheaded", "beheading",
    "lynched", "lynching",
    "massacre", "genocide",
    "shooting spree", "school shooting", "mass shooting",
    "suicide bombing", "bombing killed", "killed in a bombing",
    "terror attack", "terrorist attack",
    "self-immolation",
    "mutilated", "mutilation", "torture", "tortured",
)


def is_disqualified(text: str) -> bool:
    low = (text or "").lower()
    return any(phrase in low for phrase in _DISQUALIFYING_PHRASES)


# --------------------------------------------------------------------------- #
# Scoring
# --------------------------------------------------------------------------- #

@dataclass
class ScoreBreakdown:
    score: int
    components: Dict[str, int]
    rejected_reason: Optional[str] = None


def score_event(event: CandidateEvent) -> ScoreBreakdown:
    components: Dict[str, int] = {}

    # Hard reject on disqualifying phrases — short-circuit before any bonus.
    if is_disqualified(event.summary) or is_disqualified(event.canonical_answer):
        return ScoreBreakdown(score=-1000, components={"disqualified": -1000}, rejected_reason="graphic_or_exploitative")

    # Category penalties.
    if event.category in {"birth", "births", "birthday"}:
        components["birthday_penalty"] = -40
    if event.category in {"death", "deaths", "obituary"}:
        components["death_penalty"] = -60

    # Specific named location.
    if event.location and len(event.location.strip()) >= 2:
        components["specific_location"] = 30
    if event.country:
        components["country"] = 5

    # Year.
    if event.year is not None and -3000 <= event.year <= 2100:
        components["year"] = 20

    # Visual depictability.
    summary_low = (event.summary or "").lower()
    if any(w in summary_low for w in _VISUAL_WORDS):
        components["visual"] = 20

    # Significance.
    if any(w in summary_low for w in _SIGNIFICANT_WORDS):
        components["significant"] = 20

    # Guessability: canonical answer is a discrete noun phrase, neither too
    # short (one word like "Election") nor too long (an entire paragraph).
    canon = (event.canonical_answer or "").strip()
    canon_word_count = len(re.findall(r"\w+", canon))
    if 2 <= canon_word_count <= 14:
        components["guessable"] = 10

    # Length sanity: extremely short summaries rarely score well.
    if len(summary_low) < 25:
        components["too_short"] = -10

    # Generic-event penalty for vague single-noun categories with no context.
    if event.location is None and event.year is None:
        components["under_specified"] = -20

    score = sum(components.values())
    return ScoreBreakdown(score=score, components=components)


def rank_candidates(candidates: Sequence[CandidateEvent], *, min_score: int = 50) -> List[CandidateEvent]:
    """Return candidates passing the floor, sorted by score (desc, stable)."""
    enriched = []
    for c in candidates:
        breakdown = score_event(c)
        enriched.append((breakdown.score, c, breakdown))
    enriched.sort(key=lambda triple: triple[0], reverse=True)
    return [c for score, c, _b in enriched if score >= min_score]
