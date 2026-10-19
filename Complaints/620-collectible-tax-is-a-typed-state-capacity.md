# A state's collectible share is a typed `state_capacity`, not derived from officials, literacy and distance

**Status:** open

Part of Complaint 542 (State capacity and tax rates are typed, there is no corvée, and the fiscal crisis is a fixed cascade).

Related: 604 (literacy state).

**What is wrong.** Nothing derives capacity from officials, scribes, literacy or distance from the capital.

**Evidence.** `state_capacity` is a typed number (`sim/agents/cast.py`, `records.py`); `ADMINISTRATIVE_SPAN` (`sim/agents/tuning.py`) sizes the officials kept, not what they can collect; assessment is in `sim/agents/revenue.py`.

**Why it matters.** The tax a state can collect should follow from its administrators and reach (CLAUDE.md 4.1).

**What it would take.** Collectible share derived from the officials and literate staff a state employs and the travel time from its seat to each tile (freight and routes exist), replacing typed `state_capacity` for collection.

**Test.** A test: doubling the officials raises collection; a far tile yields less than a near one; no typed capacity is read for collection.
