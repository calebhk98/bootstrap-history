# `why` quotes one failure loss and a failure charges another (Han pays about twice the quote on its strong domains)

**Status:** open

`why` prints "IF IT FAILS: N gone (40% of the money)". The charge when the roll fails is computed from a
different base, so the two disagree by a factor that depends on the civilisation, the opposition factor
and the bill's age.

Code:

- Quote: `sim/engine/proto/techtree.py` (`failure_costs`) is `sim.project_cost(node_id) * 0.4`, and
  `project_cost` includes `civ_cost_factor`, `opposition_factor`, material market prices and the bill frozen at start.
- Charge: `sim/engine/projects_completion.py` (`_lost`) is `node["_total_cost"] * FAILURE_RESET_SHARE * cost_money_factor()`,
  none of those factors.

Measured (Han, `sim/tests/harness.sim`, same formulas the two sites use):

    if_bookbinding_case   quote  919,846   charge 1,702,778   (x1.85, civ factor 0.53)
    corpus_written        quote 1,118,340  charge 2,239,002   (x2.00, civ factor 0.53)
    scientific_method     quote  132,158   charge   125,865   (x0.95, opposition 1.05)

Tester's evidence agrees: mean/variance quoted 103,471, charged 172,452 (ratio 1/0.6, the paper/information
civ factor); mandrel/chuck quoted 112,858, charged 106,092; lead quoted 43.6 million, charged 60.4 million
(the bill is frozen at start, the charge reads the current price); the converter, with no civ factor, matched exactly.
The tester abandoned a geometry plan because the charge exceeded the warning.

Why it matters: a stated maximum loss that is wrong in either direction misprices the risk a player is
explicitly asked to weigh ("a failure costs X extra"), and it is wrong by about a factor of two where the civ is good.

What it would take: one function for the failure loss used by both the quote and the charge (the bill the player
took on, times the reset share); a regression test that the charged amount equals the quoted amount for a civ with
a cost multiplier and for an opposed node.

Found in a Han China 100 AD blind playtest (fog on, poor_scholar kit, immortal founder, goal reached in 399 AD, tester item(s) 35, 55, 70, 159). Reports: `Complaints/reports/playtest-han-china-100ad-fog-tester-notes.md`, `Complaints/reports/playtest-han-china-100ad-fog-yearly-journal.md`; triage: `Complaints/reports/playtest-han-china-100ad-fog-triage.md`.

Also reported (final playtests, B and the severe-bug section of `Complaints/reports/final-playtests-triage.md`): the failure charge disagrees with the `why` forecast by a factor of tens in Rome, not two: blast furnace forecast 31,947 and charge 846,998; industrial zinc forecast about 119 thousand, charge 11.8 million. The cause there is materials (charge uses the static book material bill, the quote excludes materials already bought or held), filed as 251; fix them together.
