# Dozens of slow topics exceed the runner's time limit on a cold cache

**Status:** partly - the shared build cost is cut and stale openings fail fast; the remaining time is stepped Rome years and per-node tree loops (engine cost), and the two spin-up topics wait on regenerated openings

The runner fails any topic still running after `TOPIC_SECONDS` (`sim/tests/__main__.py`; a topic file may raise its own with a module-level `TOPIC_SECONDS`, currently `test_baseline_rome_full_length.py`, `test_economy_bronze_market_price.py`, `test_spin_up_money_supply_full_length.py`). After an economy edit (every price solve and spin-up cache key changes), a cold full `--slow` run times out topics that pass alone with a longer limit, so they are slow, not stuck. The full history and the per-topic tables: `Complaints/reports/557-history.md`.

## What is wrong now

- What the slow topics share is stepped Rome years (the first dearest) and per-node loops over the whole tree (`can_start`, `start_blockers`, `research_filters`), both engine cost (497 owns the per-year cost). Measure a topic: `python3 -m sim.tests --slow --only <topic> --jobs 1 --timing`, a second run in the same cache directory being the warm one.
- `economy_bronze_market_price` steps eighteen years by hand, mostly `_good_routes` in `sim/economy/merchants.py`; it carries its own `TOPIC_SECONDS` until a year is cheaper. Its check reopens Complaint 502 (closed) as a baseline validation, so a failure there is a regression to read, not a time failure.
- `spin_up_money_supply` and `shipped_opening_game` have a full spin-up as their subject; cold they run the whole spin-up. `openings/` must be regenerated for them to be fast (`python3 sim/simulator.py openings --prune`), and `openings` should also ship the longer money trace `spin_up_money_supply` keys in the opening traces cache (`opening_checks_run.TRACE_CACHE_DIRECTORY`, a 40-year entry; today only the 30-year trace ships). Regeneration waits on the opening settling (473).
- `full_length_opening_checks_<civilisation>` is stale-fast (a miss raises `StaleShippedOpening`; `ROME_COMPUTE_STALE_OPENINGS=1` computes anyway). It is a plain failure, not slow, until `openings/` matches the source.
- Left in the sampled slow list: `disease_century` (the pure model, three seeds by four settings) and `economy_state_budget` (opens the full-length opening, so it follows the shipped openings).

## What it would take

- Cut a game year's cost (497), then move each remaining slow topic onto `unopened_sim`, a shared stepped game or fewer years, as 464 lists.
- Regenerate `openings/` once the spin-up settles (473).
- A per-year profile of `_good_routes` for the bronze topic.

## Done (where to look)

- `priced_at_the_margin` (`sim/engine/economy_port_coin.py`) re-opened a whole blank economy on every game build; its result is kept in `.cache/backing_margin`, keyed like the spin-up (`sim/tests/test_backing_margin_cache.py`). A warm game build fell from tens of seconds to about two (measure: `ROME_CACHE_DIR=<dir with only test_topic_seconds.json> python3 -m sim.tests --slow --only <topic> --jobs 1`).
- `load_civ` re-read and re-checked every mod on every call (thousands a year); `get_ordered_mods` (`sim/engine/mods.py`) now keeps the order per directory until a file under it changes. Measure: `python3 -c "import time; from sim.engine.data import load_civ; t=time.time(); [load_civ('rome_100ad') for _ in range(200)]; print(time.time()-t)"`.
- Stale openings fail fast (`sim/tests/test_stale_opening_guard.py`); `full_length_opening_checks` is one topic per civilisation; several topics cut years or split by subject (`real_output`, `cli_in_process`, `home_cargo_price`, `state_debases_coin`).

## Tried and not kept

- A per-topic time allowance for `hash_seed_order` (its subject is two fresh openings side by side): proposed, not in the tree now.
- `step_reply_severity` with one or two years: no faster.
