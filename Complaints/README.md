# Complaints

The issue tracker, kept as files.

- `NN-slug.md` here: issues that are not finished (`open`, `partly` or `pinned`).
- `closed/`: issues that are finished (`closed`).
- `reports/`: playtest logs, audits and reviews. Reports are inputs; their
  actionable findings are filed as numbered issues, and each report says where.
- Standing decisions that are not defects go to
  `docs/architecture/DESIGN_PRINCIPLES.md`, not here.

## Filing an issue

Take the number from `python3 sim/issue_status.py --next` (numbers run 1..N
without gaps), name the file `NN-slug.md`,
and write, in this order:

    # Title
    <blank line>
    **Status:** open
    <blank line>
    what is wrong, the evidence (file:line or a command), why it matters,
    what it would take

The status line is exactly `**Status:** <status>` or
`**Status:** <status> - one short note`, and must be the first thing after
the title. Statuses: `open`, `partly`, `pinned` (parked on purpose, held by a
regression test), `closed`. To close an issue set its status to `closed` and
`git mv` it into `closed/`.

    python3 sim/issue_status.py           the table
    python3 sim/issue_status.py --check   validate status lines, folders and numbering

If two branches file the same number, run
`python3 sim/issue_status.py --renumber --write` after merging: it closes gaps
and duplicates (oldest keeps the lowest number), rewrites every reference, and
appends the old -> new map to [RENUMBERED.md](RENUMBERED.md), which resolves old
numbers found in commit messages, `reports/` and history.
