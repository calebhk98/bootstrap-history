# Most tests check a rule through a whole game, so a failure cannot say which rule broke

**Status:** open

A large share of `sim/tests/test_*.py` builds a whole game (`harness.sim()`, `opened()`, `close_years`) and reads a
value off it, to check a rule that is one function. Such a test passes only while the live game happens to hold the
condition it assumes, and when it fails it names a symptom, not the rule. Count them (a rough grep of how each file
builds its subject; a file can match several):

    cd sim/tests && for f in test_*.py; do grep -qE "(^|[^_a-z])sim\(|Sim\(|opened\(|close_years|resumed\(" $f && echo $f; done | wc -l
    ls sim/tests/test_*.py | wc -l

Examples that went red together with no rule of theirs changing on purpose:

- `strata_income_from_cohorts` "strata that earn the same per head tie in rank": it reads two strata of a live Rome
  game and assumes they earn the same. The subject is the tie-break in `stratum_rank`; the equality was an accident.
- `cargo_cost` "dearer money raises domestic freight": it swaps `market_rate` on a running game. The subject is the
  interest term of one freight formula.
- `player_log`, `state_surplus`, `rush_fiscal_controls`, `training_ledger_and_hazard_reports`, `workforce_spinup`,
  `mines_deposits_whole_game`, `one_default_rule`, `mod_effects`, `rome_slave_stratum`.

Measure: `python3 -m sim.tests --slow --only <topic>` for each.

Why it matters: a failing check should name the broken rule where it stands, with no bisect over merges. Whole-game
tests also make most of the slow suite's time (`python3 -m sim.tests --slow --timing`).

What it would take: each such check becomes a test that calls the function with inputs it builds itself, or is
deleted where another test already holds the rule. When the rewritten test fails, the rule is fixed. A whole-game test
stays only as a named scenario or smoke test. Where the rule is a `Sim` method that needs the whole game, pull it into
a plain function first (508). Start with the failing topics above, then the rest in batches.

## Applied: the settling and real-output topics

- `real_output_cheaper_entry`: deleted. Rule tests in `test_cheaper_entry_lowers_price.py` (cost of a halved-labour entry; a
  cheaper entrant past the margin lowers the cleared price and raises the quantity; one under the margin changes nothing).
- `real_output`: the arithmetic moved to `sim/engine/real_output_measure.py` and is tested in `test_real_output_measure.py`; the
  111 s "a technology that improves no entry" check is deleted (held by `test_engine_prices` gate tests); the file is the wiring
  scenario plus one named validation.
- `saving_finds_a_use`: the paired whole-run "lent share doubles" is deleted (the two runs no longer differ); the rule is the
  `goods_orders` test that an owner offers less idle cash. One validation remains.
- `baseline_fixture`, `real_output_baseline`: kept as baseline validations (4.2), named so, failing on 473 with that message.
- `spin_up_sensitivity`: now `simulator.py spin-up-sensitivity` (a measurement); its rules are `test_spin_up_sensitivity_rules.py`.
