# The shipped openings fail their own opening checks on main

**Status:** open - found while rebuilding the shipped openings on branch year-speed-one-second; not investigated

`python3 sim/simulator.py openings` runs the opening checks (`sim/engine/opening_checks.py`) and refuses to ship an
opening that fails them. Every base civilisation fails at least one, so none can be shipped without `--allow-failing`.
`python3 sim/simulator.py opening-checks --civs rome_100ad,mexica_1500` on `main` (478dc816) gives exactly the values
the speed branch gives, so these are the game's state on `main`, not a branch's doing:

- every civilisation: `spin_up_settled` (the hidden spin-up does not settle; Complaint 473)
- `rome_100ad`: `money_against_wear` and `wage_over_floor`
- `mexica_1500`: `wage_over_floor`
- `han_china_100ad`: `money_against_wear` (just below its bound)
- `norse_900ad`: `price_over_cost_sited_ores` and `price_over_cost_coin_metal`
- `england_1300`: only `spin_up_settled`

Run `python3 sim/simulator.py opening-checks` for the current values and bounds (it takes minutes: each civilisation's
opening is opened). Why it matters: a check that every opening fails no longer tells a regression from the usual state, and
shipping needs `--allow-failing`, which also lets a real regression through. Either the openings should meet the bounds,
or a bound that does not describe a working opening should change, each with its reason.
