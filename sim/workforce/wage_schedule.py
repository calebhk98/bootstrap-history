"""The civilisation's opening wage schedule, built from the trade registry, the civilisation and the price solver."""
import copy
import warnings
from typing import Any, Mapping, Optional

from sim.default_civilisation import REPOSITORY_ROOT
from sim.content import api as content
from sim.economy.api import HOUSEHOLD_TIME_PREFERENCE
from sim.prices.api import prices as price_solver
from sim.labour.api import CAREER_YEARS, trade_of_role, wage_provider, wages
from sim.world import demand


def _food_per_kg(staple: str, mods_dir: Optional[str] = None) -> float:
    """Food value of a kilogram of the staple in the subsistence quantity's unit (kg wheat equivalent)."""
    goods = content.load_needs(REPOSITORY_ROOT, mods_dir)["goods"]
    food = ((goods.get(staple) or {}).get("satisfies") or {}).get("food")
    if food is None:
        raise ValueError("the staple %r states no food value in the household needs data, so the subsistence basket "
                         "cannot be counted in it" % staple)
    return float(food)


def build_schedule(registry: Mapping[str, Any], civ: Mapping[str, Any],
                   production_entries: Optional[Mapping[str, Any]] = None,
                   mods_dir: Optional[str] = None
                   ) -> wages.WageSchedule:
    """The civilisation's opening wage schedule.

    Costs are solved in labour hours, the numeraire being one hour of the
    unskilled trade, so no money enters until the last step. Closure: the
    wage floor needs the staple's cost, and that cost is built from labour
    at wages, but in numeraire hours the unskilled wage is 1 by definition,
    so the staple solves once from the training premiums alone, priced at the households' own time preference like every other training premium. The real-wage
    condition is then a plain number: the hours of work needed to buy the
    subsistence basket per hour worked. Below 1 the market wage clears it;
    above 1 the floor lifts the unskilled wage. Money is anchored to the
    coin: one unit is `kg_per_unit` of the coin material, worth its solved
    labour hours, so a labour hour is the reciprocal of that in money.
    """
    if production_entries is None:
        production_entries = price_solver.default_production_entries(mods_dir)
    standard = wage_provider.coin_standard(civ)
    civilisation_id = civ.get("id")
    opening = wages.WageSchedule(
        wage_provider.training_years_by_trade(registry), 1.0, 0.0, HOUSEHOLD_TIME_PREFERENCE, CAREER_YEARS)
    with warnings.catch_warnings():
        # Catalogue diagnostics belong to the solver tools, not to every start-up.
        warnings.simplefilter("ignore")
        solved = price_solver.solved_prices(
            civ["starting_techs"], opening.ratio_document(),
            production_entries=production_entries, civilization_id=civilisation_id,
            civilization=civ, unskilled_trade=trade_of_role(registry, "unskilled"))
    staple = wage_provider.staple_material(civ)
    for role, material in (("staple", staple), ("coin", standard["material"])):
        if material not in solved.resolvable_materials:
            raise ValueError(
                "civilization %r cannot price its %s %s with its starting technologies"
                % (civilisation_id, role, material))
    hours_per_kg = solved.prices_in_labour_hours
    coin_hours = standard["kg_per_unit"] * hours_per_kg[standard["material"]]
    if not coin_hours > 0.0:
        raise ValueError("civilization %r: its coin %s costs no labour hours, so a labour hour has no price in coin"
                         % (civilisation_id, standard["material"]))
    subsistence_hours = wages.subsistence_wage_per_hour(
        demand.FOOD_SUBSISTENCE_QUANTITY_KG_PER_CAPITA_PER_YEAR / _food_per_kg(staple, mods_dir),
        hours_per_kg[staple], wage_provider.people_fed_per_worker())
    return wages.WageSchedule(
        wage_provider.training_years_by_trade(registry), 1.0 / coin_hours, subsistence_hours,
        HOUSEHOLD_TIME_PREFERENCE, CAREER_YEARS)


class OpeningSchedules:
    """The opening schedules built so far, one per distinct civilisation record over one trade registry: a record that
    differs in any field (a variant keeping its id), or a registry another mod set made, is built afresh."""

    def __init__(self):
        self._held = {}   # civilisation id -> [(record as built, registry as built, its schedule)]

    def schedule_for(self, civ, registry, build, mods_dir=None):
        """The schedule of `civ` over `registry` and the data of `mods_dir`, from `build()` on the first ask for a record equal to it."""
        held = self._held.setdefault((civ.get("id"), mods_dir), [])
        for record, built_over, schedule in held:
            if record == civ and (built_over is registry or built_over == registry):
                return schedule
        schedule = build()
        held.append((copy.deepcopy(civ), registry, schedule))
        return schedule


_OPENING_SCHEDULES = OpeningSchedules()


def opening_schedule(registry: Mapping[str, Any], civ: Mapping[str, Any], mods_dir: Optional[str] = None) -> wages.WageSchedule:
    """The opening wage schedule of a civilisation record over a trade registry, built once per (record, registry): the one
    memo behind every opening-schedule read. A registry is not edited once it is loaded."""
    return _OPENING_SCHEDULES.schedule_for(civ, registry, lambda: build_schedule(registry, civ, mods_dir=mods_dir), mods_dir)
