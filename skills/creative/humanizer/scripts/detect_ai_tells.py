#!/usr/bin/env python3
"""AI-writing tell detector for the humanizer skill.

Scans prose for stock phrases, structural patterns, hedging density,
em-dash overuse, rule-of-three, emoji density, performed authenticity,
and other AI-writing fingerprints.

Usage:
    python3 detect_ai_tells.py <<< "draft text"
    python3 detect_ai_tells.py --json <<< "draft text"
    python3 detect_ai_tells.py -f draft.txt
"""

import argparse
import json
import re
import sys
import unicodedata


# ---------------------------------------------------------------------------
# Stock phrase lists (case-insensitive matching)
# ---------------------------------------------------------------------------

STOCK_OPENERS = [
    r"i hope this (?:email|message) finds you well",
    r"thank you for reaching out",
    r"thanks for your patience",
    r"great question!?",
    r"that'?s a really great question",
    r"absolutely!",
    r"definitely!",
    r"i'?d be happy to help",
    r"happy to help!?",
    r"i appreciate you asking",
    r"i'?m glad you asked",
    r"i want to be transparent",
    r"let me be clear",
    r"good news!",
]

STOCK_TRANSITIONS = [
    r"that being said",
    r"having said that",
    r"with that in mind",
    r"with that said",
    r"without further ado",
    r"let'?s dive (?:in|deep)",
    r"let'?s unpack this",
    r"let'?s explore",
    r"let'?s break this down",
    r"moving forward",
    r"going forward",
    r"at the end of the day",
    r"when all is said and done",
    r"it goes without saying",
    r"needless to say",
    r"as (?:mentioned|noted|discussed) (?:earlier|above|previously|before)",
    r"in this section",
    r"let'?s now turn to",
]

STOCK_HEDGES = [
    r"it'?s worth (?:noting|mentioning) that",
    r"it'?s important to note that",
    r"it should be noted that",
    r"it bears mentioning",
    r"it'?s (?:crucial|essential) to (?:understand|recognize)",
    r"to some extent",
    r"in some ways",
    r"it could be argued that",
    r"one might argue",
    r"it'?s possible that",
    r"there is a growing body of evidence",
]

STOCK_CLOSERS = [
    r"i hope (?:this|that) helps",
    r"let me know if you (?:have any questions|need anything)",
    r"feel free to reach out",
    r"don'?t hesitate to (?:reach out|ask)",
    r"i'?m here if you need anything",
    r"hope that makes sense",
    r"does that make sense\??",
]

PERFORMED_AUTHENTICITY = [
    r"i want to be honest with you",
    r"to be honest",
    r"if i'?m being honest",
    r"(?:^|\.\s+)honestly(?:,|\s)",
    r"i hear you",
    r"i understand your (?:concern|frustration)",
    r"i appreciate your patience",
    r"thank you for your understanding",
    r"i may be wrong,?\s*but",
    r"i could be mistaken,?\s*but",
]

AI_SIGNATURE_WORDS = [
    r"\bdelve[ds]?\b",
    r"\btapestry\b",
    r"\bmultifaceted\b",
    r"\bnuance[ds]?\b",
    r"\blandscape\b",
    r"\ba testament to\b",
    r"\bat its core\b",
    r"\bin today'?s (?:\w+ )?world\b",
    r"\bnavigate the complexities\b",
    r"\brealm\b",
    r"\bpivotal\b",
    r"\bunderscores?\b",
    r"\bembark(?:s|ed|ing)?\b",
    r"\bfoster(?:s|ed|ing)?\b",
    r"\bcomprehensive\b",
    r"\bintricate\b",
    r"\bmeticulous(?:ly)?\b",
    r"\bcommendable\b",
    r"\bnoteworthy\b",
    r"\binvaluable\b",
    r"\bindispensable\b",
    r"\bparamount\b",
    r"\bendeavor\b",
    r"\bbustling\b",
    r"\bvibrant\b",
    r"\bresonat(?:e[ds]?|ing)\b",
    r"\baligns? with\b",
    r"\bharnessing\b",
    r"\bspearheading\b",
    r"\binterplay\b",
    r"\bgame[- ]changer\b",
    r"\bgroundbreaking\b",
    r"\bcutting[- ]edge\b",
    r"\bstate[- ]of[- ]the[- ]art\b",
    r"\bseamless(?:ly)?\b",
    r"\bholistic\b",
    r"\btransformative\b",
    r"\bdisruptive\b",
    r"\bsynerg(?:y|ize|ies)\b",
    r"\bparadigm\b",
    r"\brobust\b",
    r"\bscalable\b",
    r"\binnovati(?:ve|on)\b",
    r"\bleverage[ds]?\b",
    r"\butilize[ds]?\b",
    r"\bfacilitat(?:e[ds]?|ing)\b",
]

FILLER_TRANSITIONS = [
    r"(?:^|\.\s+)furthermore(?:,|\s)",
    r"(?:^|\.\s+)moreover(?:,|\s)",
    r"(?:^|\.\s+)additionally(?:,|\s)",
    r"(?:^|\.\s+)in conclusion(?:,|\s)",
    r"(?:^|\.\s+)to summarize(?:,|\s)",
    r"(?:^|\.\s+)in summary(?:,|\s)",
]

TAUTOLOGIES = [
    (r"\beach and every\b", "each and every"),
    (r"\bfirst and foremost\b", "first and foremost"),
    (r"\bbasic fundamentals?\b", "basic fundamental(s)"),
    (r"\bpast experience\b", "past experience"),
    (r"\bend results?\b", "end result(s)"),
    (r"\bfree gifts?\b", "free gift(s)"),
    (r"\badvance planning\b", "advance planning"),
    (r"\bclose proximity\b", "close proximity"),
    (r"\bconsensus of opinion\b", "consensus of opinion"),
    (r"\bfuture plans?\b", "future plan(s)"),
    (r"\bgeneral consensus\b", "general consensus"),
    (r"\btrue facts?\b", "true fact(s)"),
    (r"\bunexpected surprises?\b", "unexpected surprise(s)"),
    (r"\bbrief summary\b", "brief summary"),
    (r"\bnew innovations?\b", "new innovation(s)"),
    (r"\bpersonal opinions?\b", "personal opinion(s)"),
    (r"\brevert back\b", "revert back"),
    (r"\bstill remains?\b", "still remain(s)"),
]

# Combine all stock phrases for the recurrence-set check
ALL_STOCK_PHRASES = (
    STOCK_OPENERS + STOCK_TRANSITIONS + STOCK_HEDGES +
    STOCK_CLOSERS + PERFORMED_AUTHENTICITY + FILLER_TRANSITIONS
)

# ---------------------------------------------------------------------------
# Structural pattern detection
# ---------------------------------------------------------------------------

EM_DASH_RE = re.compile(r'\u2014')  # —
EN_DASH_RE = re.compile(r'\u2013')  # – (sometimes used as em dash)

EMOJI_RE = re.compile(
    r'[\U0001F600-\U0001F64F'   # emoticons
    r'\U0001F300-\U0001F5FF'    # symbols & pictographs
    r'\U0001F680-\U0001F6FF'    # transport & map
    r'\U0001F1E0-\U0001F1FF'    # flags
    r'\U00002702-\U000027B0'    # dingbats
    r'\U0000FE00-\U0000FE0F'    # variation selectors (with emoji)
    r'\U0001F900-\U0001F9FF'    # supplemental symbols
    r'\U0001FA00-\U0001FA6F'    # chess symbols
    r'\U0001FA70-\U0001FAFF'    # symbols extended
    r'\U00002600-\U000026FF'    # misc symbols
    r'\U0000200D'               # ZWJ (emoji joiner)
    r'\U00002B50]',             # star
    re.UNICODE
)

EXCLAMATION_RE = re.compile(r'!')

# Invisible Unicode characters — AI uses these as escape hacks (e.g. ZWSP before
# code fences to prevent markdown collision). Humans don't insert these.
INVISIBLE_UNICODE_RE = re.compile(
    r'[\u200B'       # Zero Width Space (ZWSP) — the classic AI fence escape
    r'\u200C'        # Zero Width Non-Joiner
    r'\u200D'        # Zero Width Joiner (outside emoji sequences)
    r'\u200E'        # Left-to-Right Mark
    r'\u200F'        # Right-to-Left Mark
    r'\u202A'        # Left-to-Right Embedding
    r'\u202B'        # Right-to-Left Embedding
    r'\u202C'        # Pop Directional Formatting
    r'\u202D'        # Left-to-Right Override
    r'\u202E'        # Right-to-Left Override (Trojan Source vector)
    r'\u2060'        # Word Joiner
    r'\u2061'        # Function Application (invisible math)
    r'\u2062'        # Invisible Times
    r'\u2063'        # Invisible Separator
    r'\u2064'        # Invisible Plus
    r'\u2066'        # Left-to-Right Isolate
    r'\u2067'        # Right-to-Left Isolate
    r'\u2068'        # First Strong Isolate
    r'\u2069'        # Pop Directional Isolate
    r'\uFEFF'        # Zero Width No-Break Space / BOM (mid-file)
    r'\u00AD'        # Soft Hyphen
    r'\u180E'        # Mongolian Vowel Separator
    r'\u034F'        # Combining Grapheme Joiner
    r']'
)

# Rule of three: detect comma-separated triple lists (approximate)
RULE_OF_THREE_RE = re.compile(
    r'\b(\w+(?:[-\s]\w+)?),\s+'
    r'(\w+(?:[-\s]\w+)?),\s+'
    r'(?:and|or)\s+'
    r'(\w+(?:[-\s]\w+)?)\b'
)

# Sentence-start repetition
SENTENCE_START_RE = re.compile(r'(?:^|[.!?]\s+)([A-Z]\w+)', re.MULTILINE)


def word_count(text):
    """Simple word count."""
    return len(text.split())


def sentence_count(text):
    """Approximate sentence count."""
    sentences = re.split(r'[.!?]+', text)
    return len([s for s in sentences if s.strip()])


def _find_pattern_matches(text, patterns, category):
    """Find all matches for a list of regex patterns."""
    findings = []
    text_lower = text.lower()
    for pattern in patterns:
        for m in re.finditer(pattern, text_lower):
            findings.append({
                'category': category,
                'match': m.group(0).strip(),
                'position': m.start(),
                'pattern': pattern,
            })
    return findings


def scan(text):
    """Scan text for AI-writing tells.

    Returns dict with findings, scores, and summary.
    """
    findings = []
    wc = word_count(text)
    sc = sentence_count(text)

    if wc == 0:
        return {
            'findings': [],
            'scores': {},
            'word_count': 0,
            'sentence_count': 0,
            'ai_tell_score': 0,
            'summary': 'Empty text.',
        }

    # --- Stock phrases ---
    findings.extend(_find_pattern_matches(text, STOCK_OPENERS, 'stock_opener'))
    findings.extend(_find_pattern_matches(text, STOCK_TRANSITIONS, 'stock_transition'))
    findings.extend(_find_pattern_matches(text, STOCK_HEDGES, 'stock_hedge'))
    findings.extend(_find_pattern_matches(text, STOCK_CLOSERS, 'stock_closer'))
    findings.extend(_find_pattern_matches(text, PERFORMED_AUTHENTICITY, 'performed_authenticity'))
    findings.extend(_find_pattern_matches(text, AI_SIGNATURE_WORDS, 'ai_signature_word'))
    findings.extend(_find_pattern_matches(text, FILLER_TRANSITIONS, 'filler_transition'))

    # --- Tautologies ---
    text_lower = text.lower()
    for pattern, label in TAUTOLOGIES:
        for m in re.finditer(pattern, text_lower):
            findings.append({
                'category': 'tautology',
                'match': label,
                'position': m.start(),
                'pattern': pattern,
            })

    # --- Em dashes ---
    em_dashes = EM_DASH_RE.findall(text)
    em_dash_count = len(em_dashes)
    em_dash_ratio = em_dash_count / max(wc / 200, 1)

    if em_dash_count > 0 and em_dash_ratio > 1.0:
        findings.append({
            'category': 'em_dash_overuse',
            'match': f'{em_dash_count} em dashes in {wc} words (ratio: {em_dash_ratio:.1f}x threshold)',
            'position': -1,
            'count': em_dash_count,
        })

    # --- Exclamation marks ---
    excl_count = len(EXCLAMATION_RE.findall(text))
    excl_ratio = excl_count / max(wc / 500, 1)

    if excl_count > 0 and excl_ratio > 1.0:
        findings.append({
            'category': 'exclamation_overuse',
            'match': f'{excl_count} exclamation marks in {wc} words',
            'position': -1,
            'count': excl_count,
        })

    # --- Emoji density ---
    emoji_matches = EMOJI_RE.findall(text)
    emoji_count = len(emoji_matches)
    emoji_ratio = emoji_count / max(wc / 300, 1)

    if emoji_count > 0 and emoji_ratio > 1.0:
        findings.append({
            'category': 'emoji_overuse',
            'match': f'{emoji_count} emojis in {wc} words',
            'position': -1,
            'count': emoji_count,
        })

    # --- Invisible Unicode ---
    invisible_matches = list(INVISIBLE_UNICODE_RE.finditer(text))
    invisible_count = len(invisible_matches)
    if invisible_count > 0:
        # Group by character name for reporting
        char_names = {}
        for m in invisible_matches:
            ch = m.group(0)
            name = unicodedata.name(ch, f'U+{ord(ch):04X}')
            char_names[name] = char_names.get(name, 0) + 1
        detail = ', '.join(f'{n} x{c}' if c > 1 else n for n, c in char_names.items())
        findings.append({
            'category': 'invisible_unicode',
            'match': f'{invisible_count} invisible character(s): {detail}',
            'position': invisible_matches[0].start(),
            'count': invisible_count,
        })

    # --- Rule of three ---
    rot_matches = RULE_OF_THREE_RE.findall(text)
    if len(rot_matches) >= 2:
        findings.append({
            'category': 'rule_of_three',
            'match': f'{len(rot_matches)} triple-item lists detected',
            'position': -1,
            'count': len(rot_matches),
        })
    # Also flag individual instances if 3+ in a short text
    for m in RULE_OF_THREE_RE.finditer(text):
        findings.append({
            'category': 'rule_of_three_instance',
            'match': m.group(0)[:80],
            'position': m.start(),
        })

    # --- Sentence-start repetition ---
    starts = SENTENCE_START_RE.findall(text)
    if len(starts) >= 4:
        start_counts = {}
        for s in starts:
            start_counts[s.lower()] = start_counts.get(s.lower(), 0) + 1
        repeated = {w: c for w, c in start_counts.items() if c >= 3}
        for word, count in repeated.items():
            findings.append({
                'category': 'sentence_start_repetition',
                'match': f'"{word.title()}" starts {count} sentences',
                'position': -1,
                'count': count,
            })

    # --- Paragraph length uniformity ---
    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
    if len(paragraphs) >= 3:
        para_lengths = [word_count(p) for p in paragraphs]
        avg_len = sum(para_lengths) / len(para_lengths)
        if avg_len > 0:
            variance = sum((l - avg_len) ** 2 for l in para_lengths) / len(para_lengths)
            cv = (variance ** 0.5) / avg_len  # coefficient of variation
            if cv < 0.15 and len(paragraphs) >= 4:
                findings.append({
                    'category': 'uniform_paragraphs',
                    'match': f'Paragraphs suspiciously uniform in length (CV={cv:.2f})',
                    'position': -1,
                })

    # --- Compute scores ---
    stock_count = len([f for f in findings if f['category'].startswith('stock_')])
    hedge_count = len([f for f in findings if f['category'] == 'stock_hedge'])
    authenticity_count = len([f for f in findings if f['category'] == 'performed_authenticity'])
    sig_word_count = len([f for f in findings if f['category'] == 'ai_signature_word'])
    filler_count = len([f for f in findings if f['category'] == 'filler_transition'])
    tautology_count = len([f for f in findings if f['category'] == 'tautology'])
    rot_count = len([f for f in findings if f['category'] == 'rule_of_three_instance'])
    invis_count = len([f for f in findings if f['category'] == 'invisible_unicode'])

    # AI-tell score: 0-100 heuristic
    score = 0
    score += min(stock_count * 8, 30)
    score += min(sig_word_count * 4, 20)
    score += min(hedge_count * 6, 15)
    score += min(authenticity_count * 8, 15)
    score += min(em_dash_count * 3, 10) if em_dash_ratio > 1 else 0
    score += min(rot_count * 4, 10)
    score += min(filler_count * 5, 10)
    score += min(tautology_count * 5, 10)
    score += min(excl_count * 3, 5) if excl_ratio > 1 else 0
    score += min(emoji_count * 3, 5) if emoji_ratio > 1 else 0
    score += min(invisible_count * 6, 15)  # invisible chars are a strong AI tell
    score = min(score, 100)

    scores = {
        'stock_phrases': stock_count,
        'ai_signature_words': sig_word_count,
        'hedges': hedge_count,
        'performed_authenticity': authenticity_count,
        'filler_transitions': filler_count,
        'tautologies': tautology_count,
        'em_dashes': em_dash_count,
        'em_dash_over_threshold': em_dash_ratio > 1,
        'exclamation_marks': excl_count,
        'exclamation_over_threshold': excl_ratio > 1,
        'emojis': emoji_count,
        'emoji_over_threshold': emoji_ratio > 1,
        'invisible_unicode': invisible_count,
        'rule_of_three_instances': rot_count,
        'ai_tell_score': score,
    }

    # --- Summary ---
    if score >= 60:
        verdict = "Heavy AI tells. Needs significant rewriting."
    elif score >= 30:
        verdict = "Moderate AI tells. Worth a cleanup pass."
    elif score >= 10:
        verdict = "Light AI tells. Minor tweaks needed."
    else:
        verdict = "Reads human. Minimal or no AI tells detected."

    summary = (
        f"AI-tell score: {score}/100. {verdict} "
        f"({len(findings)} findings in {wc} words)"
    )

    return {
        'findings': findings,
        'scores': scores,
        'word_count': wc,
        'sentence_count': sc,
        'ai_tell_score': score,
        'summary': summary,
    }


def format_text(result):
    """Human-readable output."""
    lines = []
    lines.append(f"## AI-Tell Score: {result['ai_tell_score']}/100\n")
    lines.append(result['summary'])
    lines.append("")

    if result['findings']:
        # Group by category
        by_cat = {}
        for f in result['findings']:
            cat = f['category']
            if cat not in by_cat:
                by_cat[cat] = []
            by_cat[cat].append(f)

        lines.append("## Findings\n")
        for cat, items in sorted(by_cat.items()):
            label = cat.replace('_', ' ').title()
            lines.append(f"### {label} ({len(items)})\n")
            for item in items[:10]:  # cap display per category
                lines.append(f"- \"{item['match']}\"")
            if len(items) > 10:
                lines.append(f"- ... and {len(items) - 10} more")
            lines.append("")

    lines.append("## Scores\n")
    for k, v in result['scores'].items():
        lines.append(f"- {k}: {v}")

    return '\n'.join(lines)


def format_json(result):
    """JSON output."""
    return json.dumps(result, indent=2, ensure_ascii=False, default=str)


def main():
    parser = argparse.ArgumentParser(description='AI-Writing Tell Detector')
    parser.add_argument('--json', action='store_true', dest='json_output',
                        help='Output as JSON')
    parser.add_argument('-f', '--file', help='Input file (default: stdin)')
    args = parser.parse_args()

    if args.file:
        with open(args.file, 'r', encoding='utf-8') as fh:
            text = fh.read()
    else:
        text = sys.stdin.read()

    result = scan(text)

    if args.json_output:
        print(format_json(result))
    else:
        print(format_text(result))


if __name__ == '__main__':
    main()
