# The full test suite takes far longer than fifteen minutes

**Status:** partly - a cold full suite runs inside thirty minutes on four cores; three topics still time out cold

The quick tier (`python3 -m sim.tests`) runs only topics marked `QUICK_TOPIC = True`, a few to
a process, and stays fast after engine edits. The full suite (`python3 -m sim.tests --slow
--timing`) prints each topic as it finishes and a per-topic table at the end; the slowest
topics in that table are where the next cut belongs.

## Where it stands

`python3 -m sim.tests` (quick tier) and `python3 -m sim.tests --slow --timing` (full suite) print their wall
time per topic; the runner stops and fails any topic still running after `--topic-seconds` (default in
`sim/tests/__main__.py`), so a run always ends and names what is too slow. Suite games open on a short
spin-up (`ROME_SPIN_UP_YEARS`, set in `sim/tests/harness.py`), cached apart from full games, and the runner
builds one game of every civilisation before the first topic. `arrears_hours` no longer times out (474 closed: its price solves were slow, not stuck). `insolvency_whole_game` leaves the market close out of
the years that do not read it and plays a few full market years after the ruin, which is enough to show the founder's money turn round.
No topic computes a spin-up of its own that a variant of a default game could share: the spin-up key leaves the
coin out (`economy_port_key.py`), variants that only vary a rate or read the farm or prices are built unopened,
and the money-regime runs are one topic per civilisation so the runner can place them side by side. The one
setup that still needs its own spin-up is the in-memory civilisation's run of every screen.

A cold run is the one that matters: any engine edit invalidates the price solves and spin-ups. Measure it with an
empty cache directory that keeps only the runner's remembered topic times:
`mkdir /tmp/cold && cp .cache/test_topic_seconds.json /tmp/cold/ && ROME_CACHE_DIR=/tmp/cold python3 -m sim.tests --slow --timing`.
On a cold run most of the cache work is price solves (one per distinct held gate set, civilisation, wage
ratios, rate and territory), then spin-ups. Topics that still time out cold:
`ventures_lifecycle` and `economy_money_regimes_norse` (both pay their own cold price solves or spin-ups inside the limit).
The time limit runs per topic, also inside a batch of quick topics, so one slow topic no longer fails the
quick topics batched with it.

## What would cut it further

1. **Any engine edit re-runs the agent-economy spin-up** (now a short one in the suite). Its key
   (`economy_port_year.py`, `.cache/agent_economy`) hashes every `.py` under `sim/`, because
   the spin-up reads a setup built from the whole `Sim`, and only the opening values and the
   civilisation are in the key. Put the setup itself (or its digest) in the key and scope the
   source to what `sim.economy.api` imports, as `prices.py` now does with `source_modules`.
   Until then, the first full run after any edit pays one spin-up per civilisation and
   configuration the tests open.
2. **CLI tests start a process per call.** Done for every caller that only sends commands: `proto()`
   and the topics that drive `simulator.py` call `sim/tests/cli_in_process.py`, which runs the real
   `sim.ui.cli.main` on the same argv, swaps stdin, stdout, stderr, argv, the environment and the working
   directory for the call, and gives each call a fresh process's module globals (display units, unit labels,
   the per-year step hook, pushed-back lines), so `--session` still does its save then load, in memory.
   `test_cli_in_process.py` runs a sequence (two civilisations, save then load, the first game again) both
   ways and compares replies; it caught a leaked display-unit setting. Calls that must stay real processes:
   the main-menu run in `cli_menu_options_and_pretty` (true entry point), `--version` in `mod_versions`,
   the closed-pipe save in `people_attrition_scholars`, the hash-seed and reproducibility topics (they
   pin `PYTHONHASHSEED`, which an in-process call cannot), `package_identity` and the `-c` scripts that
   check a clean interpreter. Measure what is left with the last line of `python3 -m sim.tests --slow --timing`
   (spawn calls and seconds waiting on children); only calls through `subprocess.run` are counted.
3. **Integration tests for unit-level facts.** Many topics build one or more full games to
   check a reply string or a single function, and the two playtest grab-bags
   (`round2_policy_hazards_options`, `scanners_and_scheduling`) step many years. Move such
   checks onto the existing small fixtures (`economy_fixture`, `agents_fake_world`,
   `geography_fixtures`), assert after one year where one is enough, and mark the topics that
   become fast `QUICK_TOPIC = True`.
4. **Each simulated year is a full agent-economy year.** A topic that steps a game pays for its market close
   every year; most whole-game topics now step the fewest years their checks need, share stepped games, or run
   one phase of the year where the check is about that phase. Cutting the economy year itself cuts all of them.
5. **Copying a built game is not possible.** `copy.deepcopy` of a `Sim` fails on a module
   reference, so tests cannot build one game and hand out copies. Construction itself has
   per-map work that could be memoised per process (`market_areas.carriage_unit`, the tile
   deep-copy in `geography/loading.py`, region and weather tables).

Owner decision (2026-10-09): the spin-up and test-time work is handled in a separate session; not in this batch.
