"""The rule sets of the yearly economy: which rule each swappable phase of the year runs.

A setup names one (`EconomySetup.rule_set`); a phase asks `of(setup)` for its rule and calls it, so no phase tests the
name. `SEARCH` is the set the economy was built with: workers and employers find a wage over rounds of search, and
sellers search for their asks. `CLEARING` finds the value that clears a market inside the year and moves what carries
between years a fixed share of the way to it. Adding a set is one entry here."""
from dataclasses import dataclass
from typing import Callable, Dict

import numpy as np

from sim.labour.api import clear_labour_at_one_wage, clear_labour_by_search

from . import (close_pack, coin_cost, goods_clear_one_price, goods_good_clear, goods_respend_year, input_orders_after_hiring, labour_demand,
               making_cost_alone, merchant_volume_news, merchant_wage_loans, plot_hours_value)
from .setup import DEFAULT_RULE_SET as SEARCH

CLEARING = "clearing"


@dataclass(frozen=True)
class RuleSet:
    sales_the_plan_holds_to: Callable   # (each producer's expected sales in runs) -> the sales its plan holds its runs to; NaN: its stock alone holds them
    producer_labour_bids: Callable  # (setup, record, view, the year's plans, the labour bid table): the producers' bids written
    labour_clearing: Callable       # (the labour core's state, its year inputs) -> the year's clearings, the state written
    goods_clearing: Callable        # (clearing context, good, good id) -> the good's `GoodClearing`
    goods_respend: Callable         # (setup, record, view, ledger, the markets with stock left, basket of a cohort, orders): households' later rounds
    close_constants: Callable       # () -> the close kernel's numbers, in its order
    coin_charge: Callable           # (setup, view) -> the share of what a run pays in advance that its coin costs (coin_cost.py)
    merchant_volumes: Callable      # (deliveries by market, (market, unmet demand) pairs) -> the volume of each market merchants learn
    input_orders_after_hiring: Callable   # (setup, record, view, the year's plans, the ledger): the plans' input orders re-sized once the hours are hired
    merchant_wage_loan: Callable    # (the loan a merchant wants for its carriers' wages, its capital, its debt) -> the loan it asks for (None: none)
    memory_making_costs: Callable   # (setup, record) -> {good: what it costs to make}, as the market memory reads it in a year a market traded nothing
    memory_cost_of_costless: Callable   # (a market's remembered price, None for none) -> what its memory plans from where its good has no making cost (None: nothing)
    plot_return_for_hours_kept: Callable  # (priced needs, plot options, fertility, a worker's hours, people a worker keeps, hectares an hour takes by recipe,
                                          #  hectares held a worker, the state's share by good, hours the plot takes a worker) -> the return the hours kept are read from


def planned_hours_bids(_setup, _record, _view, plans, bid_table) -> None:
    """Each producer bids for the hours of the runs it planned on last year's wage, at what an hour is worth to them."""
    plans.write_labour_bids(bid_table)


def expected_sales_hold(expected_sales):
    """A producer plans no more runs than it expects to sell, with its stock brought toward its target."""
    return expected_sales


def hold_to_stock_alone(expected_sales):
    """A producer plans the runs that pay at the price it expects, less what it holds beyond its target stock spread
    over the years a stock is cleared in (more, when it holds less): the market finds the price that sells them, and
    a pile is worked off. No sales figure holds the runs (NaN to the plan: `plan_kernel.plan_rows`)."""
    return np.full_like(expected_sales, np.nan)


def schedule_bids_with_coin_cost(setup, record, view, plans, bid_table) -> None:
    """Each producer bids for hours as a schedule over the wage (labour_demand.py), a run's cost counting its coin."""
    labour_demand.write_schedule_bids(setup, record, view, plans, bid_table,
                                      coin_charge=coin_cost.charge_at_the_going_rate(setup, view))


def no_respend(_setup, _record, _view, _ledger, _left_markets, _basket_of, _orders) -> None:
    """A market that cleared at one price turned no buyer away at that price: there is no later round."""


RULE_SETS: Dict[str, RuleSet] = {
    SEARCH: RuleSet(sales_the_plan_holds_to=expected_sales_hold,
                    producer_labour_bids=planned_hours_bids, labour_clearing=clear_labour_by_search,
                    goods_clearing=goods_good_clear.clear_good, goods_respend=goods_respend_year.respend,
                    close_constants=close_pack.constants_array, coin_charge=coin_cost.no_charge,
                    merchant_volumes=merchant_volume_news.delivered_alone,
                    input_orders_after_hiring=input_orders_after_hiring.leave_as_planned,
                    merchant_wage_loan=merchant_wage_loans.as_wanted,
                    memory_making_costs=making_cost_alone.of_every_good,
                    memory_cost_of_costless=making_cost_alone.no_cost,
                    plot_return_for_hours_kept=plot_hours_value.return_of_the_next_hour),
    CLEARING: RuleSet(sales_the_plan_holds_to=hold_to_stock_alone,
                      producer_labour_bids=schedule_bids_with_coin_cost, labour_clearing=clear_labour_at_one_wage,
                      goods_clearing=goods_clear_one_price.clear_good_at_one_price, goods_respend=no_respend,
                      close_constants=close_pack.constants_array_for_clearing, coin_charge=coin_cost.charge_at_the_going_rate,
                      merchant_volumes=merchant_volume_news.delivered_and_unmet,
                      input_orders_after_hiring=input_orders_after_hiring.resize_to_hired_hours,
                      merchant_wage_loan=merchant_wage_loans.within_leverage,
                      memory_making_costs=making_cost_alone.of_goods_made_alone,
                      memory_cost_of_costless=making_cost_alone.the_price_it_had,
                      plot_return_for_hours_kept=plot_hours_value.return_keeping_what_the_plot_grows),
}


def of(setup) -> RuleSet:
    """The rule set `setup` names, the default one where it names none (a stand-in setup that carries only what a rule
    reads); a name no set carries is an error listing the ones that exist."""
    name = getattr(setup, "rule_set", SEARCH)
    found = RULE_SETS.get(name)
    if found is None:
        raise ValueError("the economy has no rule set %r; it has %s" % (name, ", ".join(sorted(RULE_SETS))))
    return found
