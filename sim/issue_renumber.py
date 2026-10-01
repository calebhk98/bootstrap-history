"""issue_renumber.py: renumber the issue files in Complaints/ so numbers run 1..N.

Called by issue_status.py (`--renumber [--write]`). The map is old number -> new
number by sorted old number; every reference in tracked text files is rewritten
from that map in one pass (see issue_references.py), then the files are renamed.
"""
import datetime
import os
import re
import subprocess


try:
    from sim import issue_references
except ImportError:
    import issue_references

SKIPPED_PREFIXES = (".claude/", "Complaints/reports/")
SKIPPED_FILES = ("Complaints/RENUMBERED.md",)
_ISSUE_PATH = re.compile(r"^Complaints/(?:closed/)?\d+-.+\.md$")
_SLUG = re.compile(r"^\d+-(.+)$")


def build_map(rows):
    """old number -> new number (1..N in row order), and the numbers used twice."""
    mapping, duplicates = {}, []
    for new, row in enumerate(rows, 1):
        if row["number"] in mapping:
            duplicates.append(row["number"])
        else:
            mapping[row["number"]] = new
    return mapping, duplicates


def issue_renames(rows):
    """(old path, new path) for every issue file whose number changes."""
    renames = []
    for new, row in enumerate(rows, 1):
        if row["number"] != new:
            folder = "Complaints/closed/" if row["folder"] == "closed" else "Complaints/"
            slug = _SLUG.match(row["file"]).group(1)
            renames.append((folder + row["file"], "%s%02d-%s" % (folder, new, slug)))
    return renames


def tracked_text_files(root):
    names = subprocess.run(["git", "ls-files", "-z"], cwd=root, check=True,
                           capture_output=True).stdout.decode().split("\0")
    for name in names:
        if name and not name.startswith(SKIPPED_PREFIXES) and name not in SKIPPED_FILES:
            yield name


def plan(root, rows):
    """The whole change: mapping, edits {path: new text}, renames, findings."""
    mapping, duplicates = build_map(rows)
    renames = issue_renames(rows)
    renamed = {old for old, _ in renames}
    edits = {}
    stats = {"rewritten": 0, "unresolved": [], "ambiguous": [], "duplicates": duplicates}
    for name in tracked_text_files(root):
        try:
            with open(os.path.join(root, name), encoding="utf-8") as handle:
                text = handle.read()
        except (UnicodeDecodeError, FileNotFoundError, IsADirectoryError):
            continue
        new_text, count, unresolved, ambiguous = issue_references.rewrite(
            text, mapping, bool(_ISSUE_PATH.match(name)))
        if count:
            edits[name] = new_text
            stats["rewritten"] += count
        stats["unresolved"] += [(name, line, old) for old, line in unresolved]
        stats["ambiguous"] += [(name, line, number, context) for line, number, context in ambiguous]
        head, base = os.path.split(name)
        renamed_base = issue_references.rewrite(base, mapping, False)[0]
        if name not in renamed and renamed_base != base:
            renames.append((name, os.path.join(head, renamed_base)))
    return {"mapping": mapping, "rows": rows, "edits": edits, "renames": renames, "stats": stats}


def report(result):
    mapping = result["mapping"]
    changed = sum(1 for old, new in mapping.items() if old != new)
    stats = result["stats"]
    lines = ["%d issue numbers change (highest becomes %d); %d files rename; %d files edited; "
             "%d references rewritten; %d bare numbers skipped as ambiguous"
             % (changed, len(mapping), len(result["renames"]), len(result["edits"]),
                stats["rewritten"], len(stats["ambiguous"]))]
    for number in stats["duplicates"]:
        lines.append("DUPLICATE number %d: references to it map to the first file" % number)
    for name, line, number, context in stats["ambiguous"]:
        lines.append("AMBIGUOUS skipped %s:%d: %s | %s" % (name, line, number, context))
    for name, line, old in stats["unresolved"]:
        lines.append("UNRESOLVED (no such issue) %s:%d: %d" % (name, line, old))
    return "\n".join(lines)


def apply(root, result, today=None):
    """Write edits, rename in two phases so no name is clobbered, then log the map."""
    for name, text in result["edits"].items():
        with open(os.path.join(root, name), "w", encoding="utf-8") as handle:
            handle.write(text)
    for index, (old, _) in enumerate(result["renames"]):
        subprocess.run(["git", "mv", old, "%s.renumber-%d" % (old, index)], cwd=root, check=True)
    for index, (old, new) in enumerate(result["renames"]):
        subprocess.run(["git", "mv", "%s.renumber-%d" % (old, index), new], cwd=root, check=True)
    write_log(root, result, today or datetime.date.today().isoformat())


def write_log(root, result, today):
    """Append a dated section of `old -> new  slug` lines to Complaints/RENUMBERED.md."""
    lines = []
    for new, row in enumerate(result["rows"], 1):
        if row["number"] != new:
            lines.append("%d -> %d  %s" % (row["number"], new, _SLUG.match(row["file"]).group(1)[:-3]))
    if not lines:
        return
    path = os.path.join(root, "Complaints", "RENUMBERED.md")
    if os.path.exists(path):
        with open(path, encoding="utf-8") as handle:
            existing = handle.read().rstrip("\n") + "\n\n"
    else:
        existing = ("# Renumbered issues\n\nOld issue numbers (in commit messages, reports and history) "
                    "and the number each has now. One section per renumbering, newest last.\n\n")
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(existing + "## %s\n\n" % today + "\n".join(lines) + "\n")
