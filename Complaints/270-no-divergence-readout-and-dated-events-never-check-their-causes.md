# Nothing tells the player when history has left its track, and scheduled events fire whether or not their causes still exist

**Status:** partly - `divergence` readout exists; events still fire without checking causes

Three testers (A, B and the Rome and Han reports in complaint 184): the 235 crisis, Decian edict, Diocletian reforms, Gothic settlement and sacks fire on schedule in an empire with steam, grids and 120 million people; the civilisation is still "under Trajan" in 600 AD (264); Mexica "invasion feels predetermined" (90% a year, all three runs, see 254). Effects are softened by what the player built, but whether they happen at all never changes.

Complaint 184 records the stakeholder decision that dated hazards stay until the dynamic systems can produce them. This complaint asks for two things that decision does not rule out:

1. A divergence readout: a screen comparing the run with the recorded world (population, literacy, key inventions, who holds the territory) and flagging when a dated event's stated causes are no longer true, so the player and the tester can see why it still fired.
2. Events that evaluate their own preconditions (an `if` in the data, not in the engine, per 4.7) and can be skipped, changed or fail, rather than always firing.

Also from A: "conditional historical events", "alternative outcomes", and "dynamic neighbouring societies" (see 107, 113, 116). C also asks the risk text to say the design intent ("you cannot stop the conquest, only protect what you know") and to show how much each hedge moves the odds (see 204, 249).

Status of evidence: reproduces by design; no live run was needed. Related: 184, 264, 107, 113, 249, 204.


Found in the final blind playtests of this branch (Rome 100 AD and Mexica 1500 fog runs; A section 7; B tree and history; C design complaints on the invasion). Reports: `Complaints/reports/playtest-rome-fog-fuzzy-demo.md`, `Complaints/reports/playtest-rome-fog-demo-65pct.md`; triage: `Complaints/reports/final-playtests-triage.md`.

## Done

- `divergence` (aliases `drift`, `baseline`): start values against now for population, wage and price index, both literacies and territory; the technologies the founder built; each dated event as happened, under way, upcoming or before the run began, with `causes_checked` false. It states what it cannot know: no baseline run is held and technologies carry no historical date (`sim/engine/proto/screen_divergence.py`).

## What remains

- Item 2: events evaluating their own preconditions in data, so they can be skipped or changed. The readout cannot flag a stale cause because no event states its causes.
- A baseline ensemble to compare against, and per-technology historical dates, so the screen can say which built technologies the society would not yet have.
