# The test runner opens a game of every civilisation before any topic outside the quick tier

**Status:** open - found on branch speed-year-step-and-openings

`_run_topics_forked` (`sim/tests/__main__.py`) calls `_warm_starts` whenever the topics to run include one outside the
quick tier, and `_warm_starts` builds `harness.sim(civ=...)` for every civilisation and then the default game. The
harness shortens the spin-up (`ROME_SPIN_UP_YEARS`), which changes the spin-up's cache key, so the shipped openings
never serve it; after any change to the economy source each of those games computes its opening from nothing. Rome's
cold opening is the bulk of that (`python3 sim/simulator.py spin-up-trace --civ rome_100ad --years 1` on a fresh
`ROME_CACHE_DIR` shows it).

So `python3 -m sim.tests --slow --only <one topic>` after an economy edit waits for every civilisation's cold opening
even when the topic builds no game at all (a fixture test that takes seconds outside the quick tier only because it
runs a few hundred hand-built years).

**What it would take.** Warm only the civilisations the chosen topics build (a topic's games are found when it first
calls the harness, so the runner could warm lazily: the first worker to need a start builds it under the cache's
per-key lock, which `solve_cache.cached_json` already holds), and make the cold opening itself fast (497).
