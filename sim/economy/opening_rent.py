"""Land rent at the opening: what the first year's land market will let the land at, carried by the opening's
prices, the producers' sizes and the households' property income, so that the first year sees the rent and costs the
opening did (Complaint 473).

The rent a tile's land fetches is the year's own rule (`land_market.post_rents`), run on the producers the opening
placed. A hectare's rent is a share of the value of what it grows, so an opening whose prices only paid labour and
inputs leaves no room for it: the prices of the recipes that take land rise until their revenue pays cost and rent
(`covering_prices`), and the rent is paid to the households that own the land, which their property income counts.
"""
import math
from typing import Dict, Iterable, Mapping, Sequence, Set, Tuple

from . import land_market, opening_income, opening_runs, ownership, unit_cost
from .replaced import replaced
from .types import AgentId, GoodId, Recipe

# numerical bounds, not behaviour: passes of the price fixed point (a dearer input raises the price of what uses it)
COVERING_PASSES = 20
COVERING_TOLERANCE = 1e-9
RENT_SHARE_CEILING = 0.9      # a share of revenue the rent cannot reach: the covering price would not be finite


def rent_share_of_revenue(rows: Iterable[Tuple[str, float, float, float]]) -> Dict[str, float]:
    """{recipe: rent paid over revenue} of the runs given as (recipe, runs, rent a run, revenue a run)."""
    rent: Dict[str, float] = {}
    revenue: Dict[str, float] = {}
    for recipe_id, runs, rent_per_run, revenue_per_run in rows:
        rent[recipe_id] = rent.get(recipe_id, 0.0) + runs * rent_per_run
        revenue[recipe_id] = revenue.get(recipe_id, 0.0) + runs * revenue_per_run
    return {recipe_id: min(RENT_SHARE_CEILING, rent[recipe_id] / revenue[recipe_id]) if revenue[recipe_id] > 0.0 else 0.0
            for recipe_id in sorted(rent)}


def covering_prices(recipes: Mapping[str, Recipe], prices: Mapping[GoodId, float], wages: Mapping[str, float],
                    rent_share: Mapping[str, float], active: Set[str], yields: Mapping[str, float]) -> Dict[GoodId, float]:
    """`prices` with the main output of each `active` recipe raised, where it must be, until a run's revenue (at its
    yield) pays its variable cost, and a rent that is `rent_share[recipe]` of that revenue. A price that already pays
    stays; an input made dearer raises the price of what uses it (the passes repeat until nothing moves)."""
    covered = dict(prices)
    main = opening_runs.main_outputs(recipes, prices)
    # a recipe the authored prices already leave short of its cost stays short by as much: only rent and dearer inputs are covered
    shortfall = {recipe_id: min(0.0, _revenue(recipes[recipe_id], prices, yields.get(recipe_id, 1.0))
                                - unit_cost.variable_cost_per_run(recipes[recipe_id], prices, wages))
                 for recipe_id in active}
    for _pass in range(COVERING_PASSES):
        moved = False
        for recipe_id in sorted(active):
            recipe = recipes[recipe_id]
            cost = unit_cost.variable_cost_per_run(recipe, covered, wages)
            share = rent_share.get(recipe_id, 0.0)
            made = recipe.outputs.get(main[recipe_id], 0.0) * yields.get(recipe_id, 1.0)
            if not math.isfinite(cost) or made <= 0.0 or share >= 1.0:
                continue
            others = math.fsum(quantity * yields.get(recipe_id, 1.0) * covered.get(good, 0.0)
                               for good, quantity in recipe.outputs.items() if good != main[recipe_id])
            price = (cost / (1.0 - share) + shortfall[recipe_id] - others) / made
            if price > covered.get(main[recipe_id], 0.0) * (1.0 + COVERING_TOLERANCE):
                covered[main[recipe_id]] = price
                moved = True
        if not moved:
            break
    return covered


def _revenue(recipe: Recipe, prices: Mapping[GoodId, float], yield_factor: float) -> float:
    return unit_cost.revenue_per_run(recipe, prices) * yield_factor


def property_income_with_rent(property_income: Mapping[AgentId, float], rent: Mapping[AgentId, float]) -> Dict[AgentId, float]:
    """The property income of an opening whose cohorts' figure (`property_income`, by what each owns) holds the rent
    paid (`rent`, by who receives it): the receivers get the rent, and the rest of the figure is what is left of it
    after the rent, spread as before (none when the rent is the whole figure)."""
    total = math.fsum(property_income.values())
    paid = math.fsum(rent.values())
    rest = max(0.0, total - paid) / total if total > 0.0 else 0.0
    result = {agent_id: amount * rest for agent_id, amount in property_income.items()}
    for agent_id, amount in rent.items():
        result[agent_id] = result.get(agent_id, 0.0) + amount
    return {agent_id: amount for agent_id, amount in sorted(result.items()) if amount > 0.0}


def shares_of_revenue(setup, record) -> Dict[str, float]:
    """The rent each recipe's opening producers pay, over their revenue at the prices the memory holds."""
    rows = []
    for producer in record.producers.values():
        recipe = setup.recipes[producer.recipe_id]
        rows.append((producer.recipe_id, producer.expected_sales, producer.land_rent_per_run,
                     unit_cost.revenue_per_run(recipe, setup.opening_prices) * producer.yield_factor))
    return rent_share_of_revenue(rows)


def settle(setup, record, view, plot_hectares_by_tile: Mapping[str, float]) -> Dict[AgentId, float]:
    """The first year's rent on the producers placed: the record's posted rent and each producer's rent a run are set
    as the year's close would set them, a producer's plant is sized to the share that works once the rent is a cost,
    and the rent each cohort receives is returned."""
    result, demands = land_market.post_rents(setup, record, view, {agent_id: producer.expected_sales
                                                                    for agent_id, producer in record.producers.items()},
                                             plot_hectares_by_tile)
    for producer_id, producer in list(record.producers.items()):
        if producer.land_rent_per_run <= 0.0:
            continue
        recipe = setup.recipes[producer.recipe_id]
        before = opening_income.working_share(recipe, setup.opening_prices, setup.opening_wages, producer.yield_factor)
        after = opening_income.working_share(recipe, setup.opening_prices, setup.opening_wages, producer.yield_factor,
                                             producer.land_rent_per_run)
        record.producers[producer_id] = replaced(producer, capacity_runs=producer.capacity_runs * before / after)
    owners = {tile: ownership.owner_cohort(record, tile) for tile in result.rent_per_hectare_by_tile}
    paid = ownership.spread(record, land_market.rent_postings(result, demands, owners, setup.currency_id))
    received: Dict[AgentId, float] = {}
    for payment in paid:
        received[payment.payee] = received.get(payment.payee, 0.0) + payment.amount
    return received
