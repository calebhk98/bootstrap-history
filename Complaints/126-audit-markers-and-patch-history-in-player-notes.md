# Player-facing notes carry audit markers and patch history

**Status:** open

**Source:** `reports/TOP_PROBLEMS.md` item 12. The data-file pointer part was fixed; this remainder was not.

## What is wrong

`why` prints a node's `note` to the player. Many notes end with
`[REVIEWED: prerequisite(s) X added by a reviewer working node by node. Reason: ...]`,
and some describe their own edit history (the `gp_whisker_forming` note says a
material "was charged as a material cost here with nothing gating it" and is
"now a direct prerequisite"). That is developer provenance in a player field;
`CLAUDE.md` says `_internal` is for auditors and `note` is for players.

## Evidence

- Writer: `sim/treetool.py:980` (the `apply-caps` step) appends the marker to
  `note`.
- Count the affected nodes with
  `grep -c "\[REVIEWED" data/tech_tree.json` (counts lines, so it slightly
  overstates nodes that also appear elsewhere in the file).
- `python3 sim/simulator.py why gp_whisker_forming` shows the history-style
  sentences.

## Why it matters

Immersion, and fog: an audit reason can name a prerequisite the player has not
heard of.

## What it would take

Write the marker to `_internal` (as `single_crystal` already does), strip the
existing markers from `data/branches/*.json` and the merged tree, rewrite
history-style notes to describe what the thing is, and add a test that no
`note` contains `[REVIEWED` or a data-file path (a data-path test already
exists in `sim/tests/test_round8g_display.py`; extend it).
