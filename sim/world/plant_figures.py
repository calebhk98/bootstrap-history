"""The plant kernel: the physical and money figures of one plant, from its production entries.

Pure functions of entries, prices and wages, which the caller passes: no `Sim`, no node dict, no money field read.
The caller (an engine adapter, a business) decides whose prices and wages these are. Pieces:
- crew: the people a plant keeps busy (`crew_people`), from the hours its lines ask in a year;
- capacity and takings: the yearly baskets (`plant_baskets`, re-exported here) and what they sell for less what they buy;
- upkeep: plant wear and maintenance, the non-crew share of upkeep (`non_labour_share`), and the crew's pay;
- ramp: how much of its full takings a plant makes by its age (`ramp`).
"""
from typing import Dict, Iterable, Mapping, Optional, Tuple

from sim.constants import declare

from .plant_baskets import (ENERGY_CARRIERS, Baskets, line_capacities, net_per_batch,  # noqa: F401  (kernel surface)
                            yearly_baskets)

PLANT_MAINTENANCE_SHARE_PER_YEAR = {
    "INFRASTRUCTURE": declare(
        "PLANT_MAINTENANCE_SHARE_INFRASTRUCTURE", 0.02, kind="temporary_heuristic",
        unit="share of build cost per year", source=None, confidence="D",
        why="Yearly upkeep of earthworks, masonry and channels as a share of what they cost to "
            "build. It goes when each plant states the parts it renews and their lives "
            "(the `capital` entries of the production data already do for some)."),
    "ENGINEERING": declare(
        "PLANT_MAINTENANCE_SHARE_ENGINEERING", 0.04, kind="temporary_heuristic",
        unit="share of build cost per year", source=None, confidence="D",
        why="Yearly upkeep of machinery and workshop plant as a share of what it cost to build; "
            "moving parts wear faster than masonry. Replaced by per-part lives as above."),
    "RESOURCE": declare(
        "PLANT_MAINTENANCE_SHARE_RESOURCE", 0.03, kind="temporary_heuristic",
        unit="share of build cost per year", source=None, confidence="D",
        why="Yearly upkeep of workings and held resources (shoring, drainage, fences) as a share "
            "of what they cost to open."),
}
DEFAULT_MAINTENANCE_SHARE = declare(
    "PLANT_MAINTENANCE_SHARE_DEFAULT", 0.03, kind="temporary_heuristic",
    unit="share of build cost per year", source=None, confidence="D",
    why="Yearly upkeep share for a node whose kind has no share of its own.")


# ---------------------------------------------------------------- crew

def derived_crew_hours(revenue_basis: Optional[str], labour_hours_by_trade: Optional[Mapping[str, float]]) -> float:
    """Hours a year the plant's lines ask of their staff; zero where the plant is not derived from its output."""
    if revenue_basis != "output":
        return 0.0
    return float(sum((labour_hours_by_trade or {}).values()))


def crew_people(derived_hours: float, hours_per_person_year: float, stated_people: Optional[float],
                fallback_people: float) -> float:
    """People one plant keeps busy: its derived hours over a person-year, else the crew it states, else the
    caller's fallback rule."""
    if derived_hours > 0.0:
        return derived_hours / hours_per_person_year
    return float(stated_people or fallback_people)


def crew_is_fallback(derived_hours: float, stated_people: Optional[float]) -> bool:
    """True when neither the plant's data nor a stated crew gives the people, so the caller's rule decides."""
    return derived_hours <= 0.0 and not stated_people


# ---------------------------------------------------------------- takings

def takings(baskets: Baskets, goods: Mapping[str, float]) -> float:
    """Money a year the baskets sell for less what they buy (outputs and energy sold, inputs and energy bought, at
    the prices passed), never negative. Linear in the prices of what it sells."""
    sold = sum(quantity * goods[material] for material, quantity in baskets.outputs.items())
    sold += sum(basket["value"] for basket in baskets.energy_sold.values())
    bought = sum(quantity * goods.get(material, 0.0) for material, quantity in baskets.purchases.items())
    bought += sum(basket["value"] for basket in baskets.energy_bought.values())
    return max(0.0, sold - bought)


# ---------------------------------------------------------------- upkeep

def maintenance_hours(kind: Optional[str], build_cost_hours: float, wear_hours: Optional[float] = None) -> float:
    """Labour hours a year to maintain a plant of this kind of node: a share of what it cost to build, and never
    more than the wear the solved price already charges for the same plant (maintenance is part of keeping a plant
    to its service life, not a charge on top of it)."""
    share = PLANT_MAINTENANCE_SHARE_PER_YEAR.get(kind, DEFAULT_MAINTENANCE_SHARE)
    kept = share * build_cost_hours
    return kept if wear_hours is None else min(kept, wear_hours)


def staff_hours_cost(labour_hours_by_trade: Mapping[str, float], wages: Mapping[str, float],
                     money_per_labour_hour: float) -> float:
    """Labour hours (of unskilled work) a year the lines' staff are paid."""
    return sum(wages[trade] * hours for trade, hours in labour_hours_by_trade.items()) / money_per_labour_hour


def _capital_build_hours(capital: Mapping, goods: Mapping[str, float], wages: Mapping[str, float],
                         money_per_labour_hour: float) -> float:
    money = sum(goods.get(material, 0.0) * quantity
                for material, quantity in (capital.get("build_materials") or {}).items())
    money += sum(wages[trade] * hours for trade, hours in (capital.get("build_labour_hours") or {}).items())
    return money / money_per_labour_hour


def plant_build_hours(plant: Iterable[Tuple[Mapping, float]], goods: Mapping[str, float],
                      wages: Mapping[str, float], money_per_labour_hour: float) -> float:
    """Labour hours it takes to build one of each capital good the lines run in: its materials at solved
    prices and its labour at wages (the build bill each production entry states)."""
    return sum(_capital_build_hours(capital, goods, wages, money_per_labour_hour) for capital, _used in plant)


def plant_wear_hours(plant: Iterable[Tuple[Mapping, float]], goods: Mapping[str, float],
                     wages: Mapping[str, float], money_per_labour_hour: float) -> float:
    """Labour hours a year the plant wears out at the share of its capacity the lines use: its build
    bill over its service life, which the solved price of what it makes charges per unit."""
    return sum(_capital_build_hours(capital, goods, wages, money_per_labour_hour)
               / capital["service_life_years"] * used for capital, used in plant if capital.get("service_life_years"))


def upkeep_parts(kind: Optional[str], baskets: Baskets, goods: Mapping[str, float], wages: Mapping[str, float],
                 money_per_labour_hour: float) -> Dict[str, float]:
    """A plant's yearly upkeep in labour hours: its crew's pay (`staff`) and the wear and maintenance of its
    capital (`plant`), with the build and wear hours the plant part comes from."""
    staff = staff_hours_cost(baskets.labour_hours, wages, money_per_labour_hour)
    build_hours = plant_build_hours(baskets.plant, goods, wages, money_per_labour_hour)
    wear_hours = plant_wear_hours(baskets.plant, goods, wages, money_per_labour_hour)
    plant = maintenance_hours(kind, build_hours, wear_hours)
    return {"staff": staff, "plant": plant, "plant_build_hours": build_hours, "plant_wear_hours": wear_hours}


def non_labour_share(stated_parts: Optional[Mapping[str, float]], upkeep_basis: Optional[str]) -> float:
    """The share of an upkeep that is not its crew's pay (plant wear and the like). A derived upkeep states its staff
    and plant parts; a staff-priced upkeep (a science's places) is all crew; an authored or defaulted figure states no
    split, so all of it stays (a gap until those figures are derived)."""
    if stated_parts is not None and stated_parts["staff"] + stated_parts["plant"] > 0.0:
        return stated_parts["plant"] / (stated_parts["staff"] + stated_parts["plant"])
    return 0.0 if upkeep_basis == "staff" else 1.0


# ---------------------------------------------------------------- ramp

def ramp(age_years: float, ramp_years: float, industry_depth: float = 0.0, share_at_full_depth: float = 1.0) -> float:
    """How much of its full takings a plant makes, 0..1, `age_years` after its doors opened (the first year is age
    zero). An established industry (`industry_depth` 0..1) finds its custom sooner: the ramp shortens to
    `share_at_full_depth` of `ramp_years` at full depth."""
    ramp_years = ramp_years * (1.0 - (1.0 - share_at_full_depth) * industry_depth)
    return min(1.0, (age_years + 1) / ramp_years)
