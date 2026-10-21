"""What a state's own take does to the base it takes from, through the payers' flight (Complaint 657), for the fiscal menu.

A payer weighs staying under the take against leaving to a tile the officials do not reach (the labour market's migration
rule, called here as the one rule): his real income after the take against all of it. A refuge beyond the reach has no
recapture, so no penalty (`flight.expected_penalty_of_leaving`); the state's reach is what limits who can leave. So raising a
rate sends more of the base away; remitting part of it, or an amnesty on arrears, brings it back; and collective liability
puts the leavers' assessment on the stayers.

    flight_share(take, reach)  = share of the payers who leave in a year at that take
    base_after(base, take_before, take_after, reach) = base * (1 - flight_share(take_after) + flight_share(take_before))
"""
from typing import Any, List, Tuple

from . import flight
from .flight_inputs import INCOME_BASES
from .tuning_fiscal import RATE_RAISE_STEP

_TINY = 1e-12


def flight_share(take: float, reach: float) -> float:
	"""Share of payers who leave in a year when the state takes `take` of income. Only the payers who can reach a tile the
	officials do not (the share the state's reach leaves) can leave untaxed and unrecaptured; for them the migration rule
	is the log of the income kept against the whole of it."""
	from sim.labour.api import migration_shares   # imported where used: the labour package reads actors too
	kept = 1.0 - max(0.0, min(1.0, take))
	if take <= 0.0:
		return 0.0
	return (1.0 - max(0.0, min(1.0, reach))) * migration_shares(max(kept, _TINY), [(1.0, 0.0)])[0]


def base_after(base: float, take_before: float, take_after: float, reach: float) -> float:
	"""A base after the payers' flight at the new take rather than the old (more when the take falls)."""
	return max(0.0, base * (1.0 - flight_share(take_after, reach) + flight_share(take_before, reach)))


def on_income(assessed: Any) -> bool:
	return assessed.basis in INCOME_BASES


def stepped(assessed: Any, share: float) -> float:
	"""The rate of a form moved by `share` of the step: up for a positive share, down for a negative one, within 0..1."""
	return max(0.0, min(1.0, assessed.rate * (1.0 + RATE_RAISE_STEP * share)))


def gross_of(assessed: Any) -> float:
	"""The base the form's payers earn before hiding (the declared base where it is not on what actors hold)."""
	return assessed.base + assessed.concealed if assessed.payers else assessed.base


def fugitive_share(world: Any) -> float:
	"""Share of the country's people who are away having fled the take; none for a world that does not say."""
	return float(getattr(world, "fugitive_share", lambda: 0.0)())


def fugitive_base(forms: List[Any], away: float) -> float:
	"""Money's worth of the income the people who fled would bear a take on, if those who stayed are the rest."""
	if not 0.0 < away < 1.0:
		return 0.0
	return sum(gross_of(assessed) for assessed in forms if on_income(assessed)) * away / (1.0 - away)


def amnesty_return(take: float, reach: float) -> Tuple[float, float]:
	"""(share who come home with arrears owed, share with them waived) when home leaves `1 - take` of income and a refuge
	leaves it all, arrears being a year's take."""
	from sim.labour.api import migration_shares
	kept = 1.0 - max(0.0, min(1.0, take))
	if kept <= _TINY:
		return 0.0, 0.0
	owed = flight.expected_penalty_of_leaving(take, reach)
	return migration_shares(1.0, [(kept, take + owed)])[0], migration_shares(1.0, [(kept, 0.0)])[0]


def collective_yield(world: Any, forms: List[Any]) -> Tuple[float, float]:
	"""(what the stayers' extra take recovers of the leavers' assessment, the base more flight under it loses) of
	moving from individual to collective liability, in money; zero when nobody has fled."""
	away = fugitive_share(world)
	if away <= 0.0 or away >= 1.0:
		return 0.0, 0.0
	recovered = lost = 0.0
	for assessed in forms:
		if not on_income(assessed):
			continue
		own = assessed.rate * assessed.collectible
		heavier = min(1.0, own / (1.0 - away))
		recovered += assessed.collectible * assessed.rate * gross_of(assessed) * away / (1.0 - away)
		lost += own * gross_of(assessed) * (flight_share(heavier, assessed.collectible) - flight_share(own, assessed.collectible))
	return recovered, lost
