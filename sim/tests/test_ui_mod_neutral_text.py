"""Test that UI strings do not hardcode 'denarii' or 'transistor'."""

QUICK_TOPIC = True

import tokenize
import io

from .harness import *  # noqa: F401,F403


TARGET_FILES = [
    "sim/ui/proto/saving_plan.py",
    "sim/ui/proto/dispatch_money.py",
    "sim/ui/cli.py",
    "sim/ui/cli_interactive.py",
]


def _read_strings_from_file(filepath):
    """Extract all string literals from a Python file, excluding comments."""
    try:
        with open(filepath, "rb") as f:
            content = f.read()
        tokens = tokenize.tokenize(io.BytesIO(content).readline)
    except FileNotFoundError:
        return []

    strings = []
    for token in tokens:
        if token.type == tokenize.STRING:
            strings.append((token.string, token.start[0]))
    return strings


# Run the test at import time
violations = []

for filepath in TARGET_FILES:
    try:
        strings = _read_strings_from_file(filepath)
    except (FileNotFoundError, tokenize.TokenError):
        continue

    for string_literal, line_num in strings:
        # Remove quotes from the string literal
        content = string_literal
        if content.startswith(('"""', "'''")):
            content = content[3:-3]
        elif content.startswith(('"', "'")):
            content = content[1:-1]

        # Check for forbidden words (case-insensitive for "denarii", case-sensitive for "transistor")
        if "denarii" in content.lower():
            violations.append(f"{filepath}:{line_num}: contains 'denarii': {string_literal[:60]}")
        if "transistor" in content:
            violations.append(f"{filepath}:{line_num}: contains 'transistor': {string_literal[:60]}")

detail = ""
if violations:
    detail = "Found hardcoded currency/goal names in UI strings:\n" + "\n".join(violations)
check("no_hardcoded_denarii_or_transistor", not violations, detail)
