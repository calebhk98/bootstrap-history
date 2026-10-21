"""How much of its income a taxpayer keeps off a state's rolls: the payer's own choice, against the state's reach.

Hiding a unit of income saves the form's rate; if the officials find it the payer pays the tax and a penalty in
proportion to the state's capacity (the penalty rule of demand_answer.py). Hiding more costs more per unit, up to
the most that can be hidden at all. The payer hides the share at which the last unit's saving, less the chance of
being found times what that costs, equals the cost of hiding it:

    saving = rate * (1 - chance_found * (1 + capacity * penalty_multiple))
    share_hidden = hideable_share * saving / marginal_cost_at_ceiling      (within 0..hideable_share)

so a higher rate hides more and a state whose officials reach more of the payers hides less. Any state, any payer.
Nothing here names a civilisation, a form or a stratum.
"""
from .demand_answer import enforcement_chance
from .tuning_demand import CONCEALMENT_DETECTION_SHARE, REFUSAL_PENALTY_MULTIPLE
from .tuning_evasion import HIDEABLE_SHARE_OF_INCOME, HIDING_MARGINAL_COST_AT_CEILING


def saving_per_unit_hidden(rate: float, collectible: float) -> float:
	"""Expected tax kept by hiding one more unit of income, after the risk of being found."""
	capacity = max(0.0, min(1.0, collectible))
	chance_found = CONCEALMENT_DETECTION_SHARE * enforcement_chance(capacity, 0.0)
	return max(0.0, rate) * (1.0 - chance_found * (1.0 + capacity * REFUSAL_PENALTY_MULTIPLE))


def hidden_share(rate: float, collectible: float) -> float:
	"""0..HIDEABLE_SHARE_OF_INCOME: the share of its income a payer keeps off the rolls under `rate`, when the
	state's officials reach `collectible` of the payers."""
	wanted = HIDEABLE_SHARE_OF_INCOME * saving_per_unit_hidden(rate, collectible) / HIDING_MARGINAL_COST_AT_CEILING
	return max(0.0, min(HIDEABLE_SHARE_OF_INCOME, wanted))


def declared_income(income: float, rate: float, collectible: float) -> float:
	"""The income the state sees on a payer's rolls."""
	return max(0.0, income) * (1.0 - hidden_share(rate, collectible))


def yield_of_rate(gross_income: float, rate: float, collectible: float) -> float:
	"""What a form at `rate` yields on payers earning `gross_income` in all, after hiding and the officials' reach."""
	return collectible * rate * declared_income(gross_income, rate, collectible)
