# The test runner opens a game of every civilisation before any topic outside the quick tier

**Status:** closed - the runner warms only the starts the chosen topics build (`sim/tests/warming.py`); the cold opening itself is 497/968

`_run_topics_forked` (`sim/tests/__main__.py`) calls `_warm_starts` whenever the topics to run include one outside the
quick tier, and `_warm_starts` builds `harness.sim(civ=...)` for every civilisation and then the default game. The
harness shortens the spin-up (`ROME_SPIN_UP_YEARS`), which changes the spin-up's cache key, so the shipped openings
never serve it; after any change to the economy source each of those games computes its opening from nothing. Rome's
cold opening is the bulk of that (`python3 sim/simulator.py spin-up-trace --civ rome_100ad --years 1` on a fresh
`ROME_CACHE_DIR` shows it).

So `python3 -m sim.tests --slow --only <one topic>` after an economy edit waits for every civilisation's cold opening
even when the topic builds no game at all (a fixture test that takes seconds outside the quick tier only because it
runs a few hundred hand-built years).

**What was done.** A topic names the civilisations it builds with a module-level `CIVILISATIONS` tuple (empty when it
builds no game); an undeclared non-quick topic still warms every civilisation, as before; quick topics build none.
`civilisations_to_warm` (`sim/tests/warming.py`) picks the starts. A topic that builds no game declares `CIVILISATIONS = ()`
and then waits for no opening (`grep -l '^CIVILISATIONS' sim/tests/test_*.py` lists the declared topics). Making the cold opening itself fast is 497/968, not this complaint.
