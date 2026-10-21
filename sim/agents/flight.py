"""A payer's comparison of staying under the state's take with leaving to a tile the state reaches less.

The comparison itself is the migration rule (`sim/labour/market/migration.py`, `move_shares`): staying scores the log
of the income kept after the state's take here, a route scores the income kept after the take there, less the move's
cost in years of subsistence. What this module adds is the state's side of it, any state's:

    expected_penalty_of_leaving = chance_recaptured * owed * (1 + reach * penalty_multiple)      (the route's added cost)
    chance_recaptured           = the state's enforcement chance at the tile he goes to (reach there, none past its roads)

so a leaver beyond the officials' reach pays nothing, and the penalty's certainty (the chance), not its size, is what
deters; a tile with no tax is better still. Returning is the same comparison run the other way with the arrears waived
by an amnesty. A payer who stays pays; what he hides is `evasion.py`.
"""
from .demand_answer import enforcement_chance
from .tuning_demand import REFUSAL_PENALTY_MULTIPLE


def recapture_chance(reach_there: float) -> float:
	"""0..1: the chance the state finds and holds a leaver at a tile its officials reach `reach_there` of."""
	return enforcement_chance(reach_there, 0.0)


def expected_penalty_of_leaving(owed: float, reach_there: float) -> float:
	"""Money a leaver expects to lose to recapture: the chance of it times what he owes (this year's tax and arrears)
	and the penalty in proportion to the state's reach there. Zero where the state reaches no one."""
	reach = max(0.0, min(1.0, reach_there))
	return recapture_chance(reach) * max(0.0, owed) * (1.0 + reach * REFUSAL_PENALTY_MULTIPLE)


def arrears_owed_by_fugitive(arrears: float, amnesty_share: float) -> float:
	"""What a fugitive owes on coming home: his arrears less the share an amnesty waives."""
	return max(0.0, arrears) * (1.0 - max(0.0, min(1.0, amnesty_share)))


def share_after_immunity(share_taken: float, years_since_taken_up: float, immunity_years: float) -> float:
	"""The state's take on land newly taken up from desertion: none during the immunity years, the form's share after."""
	return 0.0 if years_since_taken_up < immunity_years else share_taken
