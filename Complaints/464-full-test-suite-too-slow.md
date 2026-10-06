# The full test suite takes far longer than fifteen minutes

**Status:** partly - quick tier, cache lock, scoped price-solve key and warm meta-test runs done; the items below remain

The quick tier (`python3 -m sim.tests`) runs only topics marked `QUICK_TOPIC = True`, a few to
a process, and stays fast after engine edits. The full suite (`python3 -m sim.tests --slow`)
is still several times the target. Measure each topic alone, warm, with a cap:

    python3 sim/tests/__main__.py --worker <topic> --worker-result /tmp/r.json --worker-tag t --jobs 1

or `python3 -m sim.tests --slow --timing` for the whole table. The cost sits in a minority of
topics, and almost all of it is whole games stepped over years and CLI processes.

## What remains, largest first

1. **A simulated year is slow.** `Sim.step` (`sim/engine/core.py`) dominates the slow topics,
   and the agent-economy spin-up runs the same economy year up to `SPIN_UP_MAXIMUM_YEARS`
   times before a game opens. Profile one step with cProfile: the hot spots were
   `entry_trial.capacity_in_area`, the comprehension in `goods_market_demand.py`,
   `goods_market.clear` (called thousands of times a year) and `merchants._candidate_routes`.
   Faster code here speeds the game, the spin-up and every slow topic at once. Prove each
   change with `python3 -m sim.tests.fingerprint`.
2. **Any engine edit re-runs the agent-economy spin-up.** Its key
   (`economy_port_year.py`, `.cache/agent_economy`) hashes every `.py` under `sim/`, because
   the spin-up reads a setup built from the whole `Sim`, and only the opening values and the
   civilisation are in the key. Put the setup itself (or its digest) in the key and scope the
   source to what `sim.economy.api` imports, as `prices.py` now does with `source_modules`.
   Until then, the first full run after any edit pays one spin-up per civilisation and
   configuration the tests open.
3. **CLI tests start a process per call.** `proto()` and the `_play`/`_run_agent`/
   `_agent_session` helpers each pay Python start-up, imports and a new `Sim`; a `--session`
   resume builds a `Sim` and then loads over it. Most `proto()` callers only send JSON
   commands, which `_agent_dispatch` (`sim/ui/proto/dispatch.py`) can answer in-process. Keep
   a handful of real-process tests for argv, exit codes and stderr.
4. **Integration tests for unit-level facts.** Many topics build one or more full games to
   check a reply string or a single function, and the two playtest grab-bags
   (`round2_policy_hazards_options`, `scanners_and_scheduling`) step many years. Move such
   checks onto the existing small fixtures (`economy_fixture`, `agents_fake_world`,
   `geography_fixtures`), assert after one year where one is enough, and mark the topics that
   become fast `QUICK_TOPIC = True`.
5. **Copying a built game is not possible.** `copy.deepcopy` of a `Sim` fails on a module
   reference, so tests cannot build one game and hand out copies. Construction itself has
   per-map work that could be memoised per process (`market_areas.carriage_unit`, the tile
   deep-copy in `geography/loading.py`, region and weather tables).
