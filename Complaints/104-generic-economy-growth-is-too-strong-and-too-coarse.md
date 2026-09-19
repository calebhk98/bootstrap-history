# Generic economy growth per completed technology is too strong and too coarse

**Source:** playtest findings document, ECON-002. **Status:** Design/balance
recommendation, already substantially aligned with CLAUDE.md's own stated
direction.

## The player's observation and worked calculation

`sim/engine/economy.py` defines (verified at lines 222-241 in the current
tree):

    ECONOMY_INDEX_PER_DIFFUSED_NODE = 0.055   # fraction of output per diffused technology
    ECONOMY_INDEX_PER_LOCKED_NODE   = 0.030   # fraction of output per undispersed technology

and `economy_index()` (lines 336-349):

    diffused = count of completed, non-granted technologies
    economy_index = 1 + 0.055 * diffused     (if corpus_dispersed is running)
                  = 1 + 0.030 * diffused     (otherwise)

`sim/engine/economy_production.py` then raises that index to a fixed
exponent wherever gross revenue is scaled:

    gross = total_revenue * (economy_index ** ECONOMY_OUTPUT_SCALING_EXPONENT)

with `ECONOMY_OUTPUT_SCALING_EXPONENT = 0.75` (declared at line 193-203 of
that file).

The player's example: 500 diffused nodes gives an economy index of roughly
28.5; 718 diffused nodes gives roughly 40.5, and 40.5 raised to the power
0.75 is roughly a 16x output multiplier.

**Arithmetic checked directly:**

    1 + 0.055 * 500 = 28.5
    1 + 0.055 * 718 = 40.49
    40.49 ** 0.75   = 16.05

Both figures the player quoted are correct, computed against the coefficients
as they stand in the current tree.

## How this sits against CLAUDE.md

This is close to a textbook case of what CLAUDE.md §3.1 warns against: an
outcome (an economy-wide productivity multiplier) that stands in for a
mechanism (specific technologies having specific, derivable effects on
specific parts of the economy) the project intends to build but has not yet
built. The code's own comments already say this. `ECONOMY_INDEX_PER_
DIFFUSED_NODE`'s `why` field (verified directly) reads: "standing in for the
real mechanism - diffusion of a specific technology through a specific
population over time - that nothing in this project computes yet." The
player's write-up says the same thing independently, and says the code
comment already labels it a temporary heuristic; that claim is true, checked
below.

**Labelling, checked against `sim/constants.py --burndown`:** both
coefficients, and `ECONOMY_OUTPUT_SCALING_EXPONENT`, are declared through
`sim/constants.py`'s `declare()` with `kind="temporary_heuristic"` and
`confidence="D"`. Run directly:

    python3 sim/constants.py --burndown 2>&1 | grep -i "ECONOMY_INDEX\|ECONOMY_OUTPUT_SCALING"
    ->    ECONOMY_OUTPUT_SCALING_EXPONENT    dimensionless exponent on self.economy engine.economy_production
          ECONOMY_INDEX_PER_DIFFUSED_NODE    fraction of output per diffused technology engine.economy
          ECONOMY_INDEX_PER_LOCKED_NODE      fraction of output per undispersed technology engine.economy

All three appear in the burndown's "outstanding promises" list (numbers
invented because the derivation mechanism does not exist yet), not in its
separate "11 hardcoded outcomes" list (the smaller set CLAUDE.md §3.1 forbids
outright). That header line, also run directly:

    885 numbers declared, 698 are temporary heuristics (78.9%)

So this is correctly labelled today. It is a large, coarse heuristic, not an
unlabelled one, and not one of the eleven the project already treats as a
live rule violation.

## What the finding recommends, and where it already has support

Reduce reliance on the flat node-count index as domain-specific mechanisms
(agricultural productivity, energy per capita, transport/freight, literacy
and human capital, industrial output, finance) come online, letting each of
them carry part of the growth load instead. This is the same recommendation
as `LATE-010` (filed as `Complaints/116`), which should be read alongside
this one: `LATE-010` is the "what replaces it," this complaint is the "why
the current thing is oversized."

`ENDOGENOUS_COSTS_AND_DOMAINS.md` (`docs/architecture/`) already plans this
direction in Part 3's domain table: labour market, production and the price
solve at Layer 3, then infrastructure/transport, trade, settlement and
urbanisation at Layers 4-5, each meant to produce a real price rather than
have the price handed down from a flat multiplier. This complaint does not
duplicate that plan; it adds the specific measured magnitude of the current
stand-in (a ~16x multiplier at 718 nodes) as evidence for why the migration
matters, which the architecture documents do not currently quote.

## Size

This is not a one-line balance tweak. Reducing the index's weight without a
replacement mechanism just makes the game poorer for no modelled reason
(CLAUDE.md §3.2 explicitly allows the baseline to get worse while real
mechanisms are built, but that is a reason to do this deliberately alongside
`LATE-010`'s domain-specific work, not a reason to shrink the coefficient in
isolation). Treat this as advisory to the domain-by-domain migration effort,
not a standalone ticket.
