# Many node descriptions assume vocabulary instead of teaching the thing

**Status:** closed

**Source:** `reports/COMBINED_TECH_TREE_REALISM_REVIEW_part_01.md` (suggestion 9 and the description-quality column) and `reports/PLAYTEST_LOG_ROME_100_BLIND.md` observation 273.

## What is wrong

Hand-authored core nodes explain mechanism, resistance and purpose. Many
imported deep-tree nodes are a single sentence that uses specialist terms
(retting, selvedge, marling, seigniorage, radical notation, glass-to-metal
seal) without saying what the thing is, how it works, what it needs, and why
it is hard. The playtest agrees: the game teaches "why this matters" better
than "how this works".

## Evidence

- `python3 sim/simulator.py why <node>` for any short-note node versus a core
  node such as `scientific_method`.
- Find short notes with
  `python3 -c "import json;print([n['id'] for n in json.load(open('data/tech_tree.json'))['nodes'] if len(n.get('note',''))<120])"`
  (a length screen, not a quality judgement; no committed command exists).

## Why it matters

The game's pleasure is learning the chain; a player who does not know the term
cannot reason to the next step, and under fog the description is the only clue.

## What it would take

A description standard (what it is, how it works, what makes it possible here,
what the founder must do) checked by a tree audit that flags notes below a
length or lacking those parts, then a rewrite pass on the flagged nodes in
`data/branches/`. Notes stay free of audit markers (`Complaints/122`).

## Resolution

* The standard (what it is, how it works, what it needs, why it is hard and what the founder
  must do) is `data/branches/NOTE_STANDARD.md`.
* `python3 sim/simulator.py validate` prints how many notes fall below the teaching minimum and
  lists the first few; any is an error (`sim/engine/validate_note_quality.py`). The screen is
  length only; meeting the four parts is the author's and reviewer's job.
* Every flagged note in `data/branches/` and the sample mods was rewritten; the count is zero.
* `python3 -m sim.tests --only node_note_standard` fails if a new node falls below the minimum.
