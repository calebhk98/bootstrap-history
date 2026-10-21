"""A setup rebuilt from the saved opening scales the needs by the opening's literacy, not the literacy the society has
reached since: a resumed game then plays the same year the unbroken one does. The rule is `society_at_opening` and the
basket's scaling by a civilisation field, called on built inputs; the whole-game check is
test_setup_rebuilt_after_literacy_moves_scenario."""

QUICK_TOPIC = True

from .harness import check

from sim.economy import households
from sim.engine.economy_port_setup import LITERACY_FIELDS, society_at_opening

NEED_DATA = {"needs": {
    "food": {"subsistence_per_capita_per_year": 100.0, "surplus_budget_share": 0.5},
    "writing": {"subsistence_per_capita_per_year": 10.0, "surplus_budget_share": 0.2, "scales_with_civ_field": "literacy_general"},
}}


def weights(civ_values):
    return {need.need_id: (need.subsistence_per_person, need.budget_weight) for need in households.make_basket(NEED_DATA, {}, civ_values=civ_values).needs}


opening = {"literacy": {"literacy_general": 0.1, "literacy_elite": 0.9}}
civ_now = {"id": "home", "literacy_general": 0.4, "literacy_elite": 0.95, "other": 3}
society = society_at_opening(civ_now, opening)
check("the opening's saved literacy replaces the literacy the society has reached since",
      society["literacy_general"] == 0.1 and society["literacy_elite"] == 0.9, society)
check("the rest of the civilisation's fields are untouched", society["id"] == "home" and society["other"] == 3, society)
check("the opening saves both literacy fields", set(opening["literacy"]) == set(LITERACY_FIELDS))
check("a need that scales with literacy weighs by the opening's, so more literacy would weigh more",
      weights(society)["writing"][1] < weights(civ_now)["writing"][1], (weights(society), weights(civ_now)))
check("a setup rebuilt after literacy moved has the first setup's need weights",
      weights(society_at_opening(dict(civ_now, literacy_general=0.8), opening)) == weights(society))
check("a need that scales with no field is untouched by literacy", weights(society)["food"] == weights(civ_now)["food"])
