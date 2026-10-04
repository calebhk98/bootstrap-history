# No command prints the agent economy's health figures

**Status:** open - needs a `sim/simulator.py` subcommand

`sim/economy_validate.py` was deleted with the top-level cleanup, and with it the only way to print
grain and metal volatility, the wage in grain, hunger, money drift and conservation over civilisations
and seeds. Every complaint about the agent economy (387, 388, 398, 400, 428) cites it. The figures are
now pure functions in `sim/economy/diagnostics.py` (`summary`, `volatility`, `hired_share`,
`hunger_share`, `price_over_labour`, `ratio`), tested on the engine-free fixture
(`python3 -m sim.tests --only economy_diagnostics`).

What it would take: a `simulator.py economy-check [--years N] [--seeds a,b] [--civs ...]` subcommand
that plays games and prints `diagnostics.summary` per civilisation and seed. The staple and metal goods
should come from data (good categories, Complaint 429), not from a list of ids in the command.
