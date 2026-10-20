# No player action can build a sea-to-sea canal

**Status:** closed. A canal across an isthmus is a way (`sea_canal`): data states where a cut is possible (`data/world/geography/isthmuses/`), the cost is the earth moved at the canal mode's rates (`sim/geography/ways_isthmus.py`), and a built cut is a sea link in the route graph. Tests: `geography_sea_canal`, `engine_sea_canal`.

Part of Complaint 487 (No diplomacy).

**What is wrong.** A canal is a way on a land edge between held tiles. A sea-to-sea canal (Nile to Red Sea, Suez, Panama, an invented one) needs a sea link in map data, and sea links are a static catalogue.

**Evidence.** `sim/engine/ways.py` `build_way` handles land edges only; `sim/ui/proto/dispatch_ways.py`; `data/world/geography/sea_links/` (a catalogue a mod overlay can extend; not tested in this review).

**Why it matters.** An intervention must propagate through normal rules (CLAUDE.md 4.3); a canal is a way, not a special case.

**What it would take.** A runtime overlay on the sea-link graph and a recompiled route graph, plus a way definition with costs.

**Test.** A test builds a canal way across a sea link: the route graph is recompiled and a route between the two seas now exists with the way's cost.
