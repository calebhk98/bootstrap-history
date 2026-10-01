"""issue_references.py: find and rewrite references to numbered issues in text.

Used by issue_renumber.py. `rewrite(text, mapping, in_issue_file)` returns the
new text, the number of references changed, and two lists of findings:
`unresolved` (a reference to a number with no issue file, left alone) and
`ambiguous` (a bare number in an issue file that might be a reference, left
alone). All replacements are computed from the original text in one pass, so a
new number is never rewritten again.
"""
import re

_ITEM = r"\d+(?:[-–]\d+)?(?:\s\([^()\d]*\))?(?: closed)?"
_SEPARATOR = r"(?:, and |, | and | or | & |/)"
_LIST = r"%s(?:%s%s)*" % (_ITEM, _SEPARATOR, _ITEM)
_END = r"(?=\s*(?:[.;:)\]]|$)|,(?!\d)|\s+(?:and|or|but|is|are|was|were|for|as|which|that|where|in|on|with)\b|\s*\()"
_REFERENCE_WORDS = re.compile(r"(?i)complaint|related|\bsee\b|filed|issue|status|remain|closed|\bopen\b|next|tracked|covered")
_STRONG_WORDS = re.compile(r"(?i)complaint|related|\bsee\b|filed|tracked|covered by|\*\*status|remains? is|the same gap")
_TESTER_ITEMS = re.compile(r"(?i)tester items?(?:\(s\))?|items? \d")

# (pattern, group holding the numbers, applies to issue files only, needs reference words on the line)
_PATTERNS = [
    (re.compile(r"Complaints/(?:closed/)?(\d+(?:(?:, | and )\d+)*)(?!\d)"), 1, False, False),
    (re.compile(r"\b[Cc]omplaints?[ \t\n]+#?(%s)(?![\d%%]|[.,]\d)" % _LIST), 1, False, False),
    (re.compile(r"complaints?_(\d+)(?:_(\d+))?(?!\d)"), None, False, False),
    (re.compile(r"`(\d+)`(?:, `(\d+)`)*"), None, True, True),
    (re.compile(r"(?i)\b(?:related(?: complaints?)?:?|see(?: also)?|merged into|split into|duplicate of"
                r"|superseded by|filed(?: [a-z]+){0,6}? (?:in|as)|next:|closing(?: the rest of)?|closes|closed|goes with|intent of"
                r"|sized by|the same gap as|same class:)[ \t]+`?(%s)`?%s" % (_LIST, _END)), 1, True, False),
    (re.compile(r"\b(?:is|are)[ \t]+(%s)%s" % (_LIST, _END)), 1, True, True),
    (re.compile(r"(?<=[A-Za-z] )\((\d+(?:(?:, | and )\d+)*)(?:,? closed)?[,)]"), 1, True, True),
]
_NUMBER = re.compile(r"(?<!\d)(\d+)(?!\d)")
_BARE = re.compile(r"(?<![\w.$~/`=,-])(\d{1,3})(?! ?(?:AD|BC|CE|BCE)\b)(?=`?(?:[,.;:)]|$| and\b| or\b))")
_YEAR_WORDS = re.compile(r"(?:AD|BC|BCE|CE|year|years|seed|about|roughly|near|over|to|from|of|x)\s$", re.I)


def _line_of(text, start, end):
    line_end = text.find("\n", end)
    return text[text.rfind("\n", 0, start) + 1:line_end if line_end >= 0 else len(text)]


def _format(old_text, new_number):
    padded = len(old_text) > 1 and old_text.startswith("0")
    return "%02d" % new_number if padded else str(new_number)


def _replacements(segment, mapping, unmapped):
    """Edits for every number in a vetted segment: (start, end, text) and the unmapped numbers."""
    edits = []
    for match in _NUMBER.finditer(segment):
        old = int(match.group(1))
        if old not in mapping:
            unmapped.append(old)
        elif mapping[old] != old:
            edits.append((match.start(1), match.end(1), _format(match.group(1), mapping[old])))
    return edits


def rewrite(text, mapping, in_issue_file):
    """-> (new_text, changed_count, unresolved, ambiguous); line numbers are 1-based."""
    edits = []
    covered = []
    unresolved = []
    for pattern, group, issue_only, needs_words in _PATTERNS:
        if issue_only and not in_issue_file:
            continue
        for match in pattern.finditer(text):
            line = _line_of(text, match.start(), match.end())
            if needs_words and not _REFERENCE_WORDS.search(line):
                continue
            if any(start < match.end() and match.start() < end for start, end in covered):
                continue
            covered.append((match.start(), match.end()))
            if group is None:
                lo, hi = match.span()
            else:
                lo, hi = match.span(group)
            segment = text[lo:hi]
            unmapped = []
            if issue_only and any(int(found) not in mapping for found in _NUMBER.findall(segment)):
                covered.pop()
                continue
            for start, end, replacement in _replacements(segment, mapping, unmapped):
                edits.append((lo + start, lo + end, replacement))
            line_number = text.count("\n", 0, lo) + 1
            unresolved.extend((old, line_number) for old in unmapped)
    ambiguous = []
    if in_issue_file:
        for match in _BARE.finditer(text):
            if any(start < match.end() and match.start() < end for start, end in covered):
                continue
            line = _line_of(text, match.start(), match.end())
            before = text[text.rfind("\n", 0, match.start()) + 1:match.start()]
            text_number = match.group(1)
            if int(text_number) in mapping and (int(text_number) > 9 or text_number.startswith("0")) \
                    and _STRONG_WORDS.search(line) and not _TESTER_ITEMS.search(line) \
                    and not _YEAR_WORDS.search(before):
                ambiguous.append((text.count("\n", 0, match.start()) + 1, match.group(1), line.strip()[:110]))
    new_text = text
    for start, end, replacement in sorted(edits, reverse=True):
        new_text = new_text[:start] + replacement + new_text[end:]
    return new_text, len(edits), unresolved, ambiguous
