"""The civilisation's opening wage schedule, built from the trade registry, the civilisation and the price solver."""
import warnings
from typing import Any, Dict, Mapping, Optional

from sim.default_civilisation import REPOSITORY_ROOT
from sim.engine import need_data
from sim.labour.api import wage_provider, wages
from sim.world import demand


def _food_per_kg(staple: str) -> float:
    """Food value of a kilogram of the staple in the subsistence quantity's unit (kg wheat equivalent)."""
    goods = need_data.load_needs(REPOSITORY_ROOT)["goods"]
    return float(((goods.get(staple) or {}).get("satisfies") or {}).get("food", 1.0))


def build_schedule(registry: Mapping[str, Any], civ: Mapping[str, Any],
                   tightness_factors: Optional[Dict[str, float]] = None,
                   production_entries: Optional[Mapping[str, Any]] = None
                   ) -> wages.WageSchedule:
    """The civilisation's opening wage schedule.

    Costs are solved in labour hours, the numeraire being one hour of the
    unskilled trade, so no money enters until the last step. Closure: the
    wage floor needs the staple's cost, and that cost is built from labour
    at wages, but in numeraire hours the unskilled wage is 1 by definition,
    so the staple solves once from the training premiums alone. The real-wage
    condition is then a plain number: the hours of work needed to buy the
    subsistence basket per hour worked. Below 1 the market wage clears it;
    above 1 the floor lifts the unskilled wage. Money is anchored to the
    coin: one unit is `kg_per_unit` of the coin material, worth its solved
    labour hours, so a labour hour is the reciprocal of that in money.
    """
    from sim.engine import prices as price_solver
    standard = wage_provider.coin_standard(civ)
    civilisation_id = civ.get("id")
    opening = wages.WageSchedule(
        wage_provider.training_years_by_trade(registry), 1.0, 0.0, civ["starting_interest_rate"])
    with warnings.catch_warnings():
        # Catalogue diagnostics belong to the solver tools, not to every start-up.
        warnings.simplefilter("ignore")
        solved = price_solver.solved_prices(
            civ["starting_techs"], opening.ratio_document(),
            production_entries=production_entries, civilization_id=civilisation_id,
            civilization=civ)
    staple = wage_provider.staple_material(civ)
    for role, material in (("staple", staple), ("coin", standard["material"])):
        if material not in solved.resolvable_materials:
            raise ValueError(
                "civilization %r cannot price its %s %s with its starting technologies"
                % (civilisation_id, role, material))
    hours_per_kg = solved.prices_in_labour_hours
    coin_hours = standard["kg_per_unit"] * hours_per_kg[standard["material"]]
    subsistence_hours = wages.subsistence_wage_per_hour(
        demand.FOOD_SUBSISTENCE_QUANTITY_KG_PER_CAPITA_PER_YEAR / _food_per_kg(staple),
        hours_per_kg[staple], wage_provider.people_fed_per_worker())
    return wages.WageSchedule(
        wage_provider.training_years_by_trade(registry), 1.0 / coin_hours, subsistence_hours,
        civ["starting_interest_rate"], tightness_factors=tightness_factors)
