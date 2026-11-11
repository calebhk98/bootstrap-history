# Households are seeded with tonnes of platinum in a society that never worked it

**Status:** closed - platinum_g and platinum_ore_kg are gated on mt2_platinum_group_metals; the opening already drops a priced good no held technique makes (port_closure.makeable_prices), so no price means no seeded stock; validate now refuses an ungated entry making a need-serving durable (validate_production.check_durable_gate); the five civilisations declare platinum_g in unsupplied_basket_goods. The 5.4e4 g wear figure is for the orchestrator to re-measure with economy-check once openings are rebuilt.

`python3 sim/simulator.py economy-check --accounts --years 1 --civs mexica_1500` shows `platinum_g` worn at
about 5.4e4 in year one against about 7.6 made. At the good's fifty-year life (data/world/service_lives.json)
that is a household stock of several tonnes of platinum.

Cause found while closing Complaint 975: `platinum_g` serves the ornament need (data/world/needs.json) and
has no `requires_node`, so wherever it has a price the opening gives each household the serving stock of a
durable good (`opening._seed_durable_stocks`, "opening stock of a durable in use") and the year wears it by
its service life. A good a society never worked, held or traded is thereby held in tonnes: the rule asks only
whether a price exists, and the platinum recipe is ungated.

What it would take: a good that serves a need is seeded only where the society has a source for it (a deposit
worked before the start, a partner's supply, or a gate on a node it holds), and the platinum entry carries a
`requires_node` or a deposit site so that a price alone does not create a stock. Not touched by Complaint 975,
which gates the animals and linen and keeps households off mines.
