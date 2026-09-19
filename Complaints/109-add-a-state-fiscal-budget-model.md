# Add a real state fiscal/budget model

**Source:** playtest findings document, LATE-003. **Status:** Major
roadmap-sized feature recommendation, with an existing code-level admission
that this is missing.

## The player's reasoning

Current state funding and state notice are useful abstractions, but the
player notes that `STATE_FUNDING_BASE` itself, in its own code comment,
says a real answer needs a state budget. A mature industrialising
civilisation should increasingly involve taxes, public debt, state
procurement, infrastructure spending (roads, railways, ports, schools,
sewers), military budgets, subsidies, monopolies, requisitions and public
utilities, extending rather than replacing the existing `state_capacity`,
`state_notice`, requisitions, forced offices, military diffusion and
patronage mechanisms. This would also give industrialisation a source of
capital besides the one household, which bears on `ECON-003`
(`Complaints/105`)'s point about who else captures the gains.

## Checked against the current code

The player's claim about the code comment is correct, verified directly.
`sim/engine/economy_production.py` declares:

    STATE_FUNDING_BASE = declare(
        "STATE_FUNDING_BASE", 2500.0, kind="temporary_heuristic",
        ...
        why="What an imperial patron is worth in direct funding at a "
            "reference civilisation size and state capacity. No fiscal "
            "record backs this figure; a real answer needs a state budget "
            "model - tax revenue, the fiscus's own spending priorities - "
            "that this engine does not have, per CLAUDE.md 3.1's ban on "
            "asserting a state revenue outright.")

This constant, and its two siblings `STATE_FUNDING_POP_SCALE_EXPONENT` and
`STATE_FUNDING_GOV_QUALITY_SCALE`, are all `kind="temporary_heuristic"`, so
this is a correctly labelled heuristic per §3.4, not an unlabelled one. The
`why` field is, in effect, the code itself asking for this exact feature.

## How this sits against CLAUDE.md

This is precisely what §3.1 is about: a Roman soldier, a state's spending
priorities and how much a patron is "worth" should fall out of tax revenue,
recruitment institutions, provisioning and fiscal capacity rather than being
a flat coefficient times population scale. The constant's own `why` field
already cites §3.1 as the reason it exists as a placeholder rather than as a
permanent design.

## What already exists

`docs/architecture/ENDOGENOUS_COSTS_AND_DOMAINS.md` Part 3's domain table
places "Politics and governance: the state as an organisation with a
balance sheet" at Layer 6, after economy/labour (Layer 3) and
infrastructure/trade (Layer 4) and settlement (Layer 5), explicitly because
building a state budget consumer before its producers (a real labour market,
real prices, real trade) means inventing numbers for it. `docs/architecture/
STATE_OF_THE_PROJECT.md`'s Milestone 6+ row lists "state finance" among the
systems with "no dedicated module yet." So this is a genuinely open gap the
architecture plan already sequences; this complaint adds the playtest
motivation and the exact code-level admission, not a new proposal.

`sim/engine/society_state_pressure.py` has requisitions, forced offices and
state-notice/hazard machinery today, which the player correctly says this
system should extend rather than replace.

## Size

Roadmap-sized, and explicitly sequenced behind the labour market, demand and
price-solver wiring per the architecture document's own dependency order
(Layer 3 before Layer 6). Do not pick this up as a standalone task before
`Complaints/106`'s wiring work lands, since a state budget without real
prices and wages to tax is inventing numbers on top of other invented
numbers.

## Cross-references

`Complaints/105` (ECON-003) for why this should redistribute rather than
merely reduce; `Complaints/106` (ECON-004) for the labour/demand
prerequisites; `docs/architecture/ENDOGENOUS_COSTS_AND_DOMAINS.md` Part 3
for the layer ordering.
