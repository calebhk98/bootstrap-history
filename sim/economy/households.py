"""Household cohorts as agents: the public API of the household side of the economy.

    make_basket(need_data, production)                      -> Basket   (once)
    cohorts_for_tile(tile, people, working_share, gini, class_count=None,
                     opening_income_per_capita=0.0)          -> [Cohort], poorest first
    distribute_property_income(cohorts, amount)             -> {agent_id: amount} by ownership share
    labour_offers(cohort, workers_by_trade, view, subsistence_cost_per_year, working_hours_per_year,
                  danger_by_trade)                          -> [LabourOffer]
    need_prices(basket, view, tile)                         -> priced needs, shareable across a tile's classes
    goods_orders(cohort, view, cash, income_this_year, basket, specs, priced=None, smooth_rise=True)
                                                            -> AgentOrders
    close_year(cohort, received_by_good, view, specs, basket, income_received, spent)
                                                            -> (Cohort, [GoodsMove])

`Cohort.unmet_floor_by_need` holds need units short of the floor (per need, since goods within a need
substitute); demography reads the food entry as hunger.
"""
from sim.world.need_basket import make_basket

from .households_basket import need_prices
from .households_close import close_year, unmet_floor_by_need
from .households_cohort import (Cohort, cohort_id, cohorts_for_tile, distribute_property_income,
                                labour_offers)
from .households_orders import goods_orders

__all__ = ["make_basket", "need_prices",
           "close_year", "unmet_floor_by_need", "Cohort", "cohort_id", "cohorts_for_tile",
           "distribute_property_income", "labour_offers", "goods_orders"]
