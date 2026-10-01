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

- Writer: `sim/treetool.py:990` (the `apply-caps` step) appends the marker to
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

Also reported (Han China 100 AD fog playtest, tester item(s) 22, 37, 184, 152; `Complaints/reports/playtest-han-china-100ad-fog-triage.md`): `gp_whisker_forming`'s note still says the material "was floating free of the tree with nothing gating it; it is now a real prerequisite here, one step short of the goal so it stays properly" hidden (reproduces: yes, `data/tech_tree.json`); the combined-commitment warning prints `funding_capacity()` and `your_real_ceiling` (`sim/engine/proto/dispatch_ventures.py`); the kit description says "It used to make things worse and no longer does"; a risk note read "what a break tester meant". The `labour.py` pointer in `population` is gone. See 236.

Also reported (Han China 100 AD fog playtest, tester item(s) 49; `Complaints/reports/playtest-han-china-100ad-fog-triage.md`): `arrival_orientation`'s note says it is "OPTIONAL, and no longer a prerequisite for anything" (patch history; reproduces in `data/tech_tree.json`), which the tester read as development commentary.
