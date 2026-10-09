# Nothing tells the player when history has left its track, and scheduled events fire whether or not their causes still exist

**Status:** partly - `divergence` readout exists and events can state `causes` that skip or weaken them (a first set of events carries them); the remaining events and a baseline ensemble are still to do

Three testers (A, B and the Rome and Han reports in complaint 180): the 235 crisis, Decian edict, Diocletian reforms, Gothic settlement and sacks fire on schedule in an empire with steam, grids and 120 million people; the civilisation is still "under Trajan" in 600 AD (260); Mexica "invasion feels predetermined" (90% a year, all three runs, see 250). Effects are softened by what the player built, but whether they happen at all never changes.

Complaint 180 records the stakeholder decision that dated hazards stay until the dynamic systems can produce them. This complaint asks for two things that decision does not rule out:

1. A divergence readout: a screen comparing the run with the recorded world (population, literacy, key inventions, who holds the territory) and flagging when a dated event's stated causes are no longer true, so the player and the tester can see why it still fired.
2. Events that evaluate their own preconditions (an `if` in the data, not in the engine, per 4.7) and can be skipped, changed or fail, rather than always firing.

Also from A: "conditional historical events", "alternative outcomes", and "dynamic neighbouring societies" (see 103, 109, 112). C also asks the risk text to say the design intent ("you cannot stop the conquest, only protect what you know") and to show how much each hedge moves the odds (see 200, 245).

Status of evidence: reproduces by design; no live run was needed. Related: 180, 260, 103, 109, 245, 200.


Found in the final blind playtests of this branch (Rome 100 AD and Mexica 1500 fog runs; A section 7; B tree and history; C design complaints on the invasion). Reports: `Complaints/reports/playtest-rome-fog-fuzzy-demo.md`, `Complaints/reports/playtest-rome-fog-demo-65pct.md`; triage: `Complaints/reports/final-playtests-triage.md`.

## Done

- `divergence` (aliases `drift`, `baseline`): start values against now for population, wage and price index, both literacies and territory; the technologies the founder built; each dated event as happened, under way, upcoming or before the run began, with `causes_checked` false. It states what it cannot know: no baseline run is held and technologies carry no historical date (`sim/ui/proto/screen_divergence.py`).

- Item 2, mechanism: an event may declare `causes` in its civilisation file (quantity, comparison, threshold, `why`), evaluated by `sim/engine/event_causes.py` (quantities: population, output hours per head, state funded share, army against the threat, both literacies, a technology the state holds, share of start territory held). A failed cause skips the event that year (or weakens it with `causes_effect: scale`) and says so once in the log. `validate` rejects an unknown quantity, operator or technology. The `divergence` screen reports `causes_checked`, `causes_hold_now` and `failed_causes`; the `risk` forecast shows the chances after the causes, with the causes listed. Tests: `sim/tests/test_event_causes.py`.
- Causes are stated for: the plague and epidemic events (population against the opening population), the third-century crisis and the currency debasement (state funding gap), Diocletian's reforms (funding gap, territory held), the Gothic settlement, the sack of Rome, the Lombard invasion and the Spanish invasion (army against the threat), the end of the western empire (funding gap).

## What remains

- The thresholds are reasoned bounds from `Complaints/reports/conditional-events-research.md`, not fitted: no baseline ensemble exists to say how often a baseline run satisfies them. Whether the funding-gap cause ever blocks the crisis in an ordinary run is unmeasured (it needs a whole game, which the quick tests do not build); measure it with an ensemble before trusting it.
- Events left without causes, with the quantity each would need: Christianisation, the Decian edict values, the solidus, Carolingian renaissance, Tang and Sui settlements and other values shifts (a legitimacy or religious-institution quantity); Yellow Turban rebellion (inequality from stratum welfare, harvest shock); An Lushan and Han regency cycle (frontier command concentration, court legitimacy); Justinian's Gothic War and the Hundred Years War (a neighbour's army and aggression); civil-war events (elite numbers and state distress together); Great Famine and the dearth events (a harvest-shortfall quantity); the Spanish invasion's weapons gap and allies (a per-country military capability; the sources dispute the weight, so no `state_holds` cause was stated).
- A baseline ensemble to compare against, and per-technology historical dates, so the screen can say which built technologies the society would not yet have.
- The 386 epidemic model should replace the epidemic events and their population cause.
