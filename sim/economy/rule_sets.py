"""The rule sets of the yearly economy: which rule each swappable phase of the year runs.

A setup names one (`EconomySetup.rule_set`); a phase asks `of(setup)` for its rule and calls it, so no phase tests the
name. `SEARCH` is the set the economy was built with: workers and employers find a wage over rounds of search, and
sellers search for their asks. `CLEARING` finds the value that clears a market inside the year and moves what carries
between years a fixed share of the way to it. Adding a set is one entry here."""
from dataclasses import dataclass
from typing import Callable, Dict

import numpy as np

from sim.labour.api import clear_labour_at_one_wage, clear_labour_by_search

from . import (basket_counted, close_pack, coin_cost, durable_stock, goods_clear_one_price, goods_good_clear, goods_respend_year, input_orders_after_hiring, labour_demand,
               making_cost_alone, merchant_stuck_stock, merchant_volume_news, merchant_wage_loans, opening_issuer_coin, plot_hours_value,
               rate_step, servant_hours_counted, spin_up_migration, spin_up_seats, spin_up_stop, spin_up_trim, unkept_goods)
from .setup import DEFAULT_RULE_SET as SEARCH

CLEARING = "clearing"


@dataclass(frozen=True)
class RuleSet:
    sales_the_plan_holds_to: Callable   # (each producer's expected sales in runs, whether nothing it makes keeps a year) -> the sales its plan holds its runs to; NaN: its stock alone holds them
    expected_sales_after_close: Callable   # (the close's expected sales, last year's, the year's takings, what a run was expected to bring in,
                                           #  whether nothing it makes keeps a year, the share moved a year) -> each producer's expected sales in runs
    producer_labour_bids: Callable  # (setup, record, view, the year's plans, the labour bid table): the producers' bids written
    labour_clearing: Callable       # (the labour core's state, its year inputs) -> the year's clearings, the state written
    goods_clearing: Callable        # (clearing context, good, good id) -> the good's `GoodClearing`
    goods_respend: Callable         # (setup, record, view, ledger, the markets with stock left, basket of a cohort, orders): households' later rounds
    close_constants: Callable       # () -> the close kernel's numbers, in its order
    coin_charge: Callable           # (setup, view) -> the share of what a run pays in advance that its coin costs (coin_cost.py)
    merchant_volumes: Callable      # (deliveries by market, (market, unmet demand) pairs) -> the volume of each market merchants learn
    input_orders_after_hiring: Callable   # (setup, record, view, the year's plans, the ledger): the plans' input orders re-sized once the hours are hired
    rate_remembered: Callable       # (the rate remembered, None for none; the rate the year's lending cleared at) -> the rate the economy remembers
    merchant_stock_offered_where_it_stands: Callable   # (units of a stock held for a route, the share of its tile's carriage plan that is crewed, the room at its destinations) -> units offered where they stand
    merchant_cash_for_new_cargo: Callable   # (a merchant's cash, the coin carrying the stock it keeps for routes will cost) -> the cash that buys new cargo
    merchant_wage_loan: Callable    # (the loan a merchant wants for its carriers' wages, its capital, its debt) -> the loan it asks for (None: none)
    memory_making_costs: Callable   # (setup, record) -> {good: what it costs to make}, as the market memory reads it in a year a market traded nothing
    memory_cost_of_costless: Callable   # (a market's remembered price, None for none) -> what its memory plans from where its good has no making cost (None: nothing)
    servant_hours_counted_on: Callable    # (hours of household work a cohort planned to hire last year, hours of that need it went without) ->
                                          #  (the hours its next plan starts from, the most it counts on being served: None for whatever it plans)
    plot_return_for_hours_kept: Callable  # (priced needs, plot options, fertility, a worker's hours, people a worker keeps, hectares an hour takes by recipe,
                                          #  hectares held a worker, the state's share by good, hours the plot takes a worker) -> the return the hours kept are read from
    opening_issuer_coin: Callable   # (setup, the opening's record, its view) -> the coin the money's issuer opens holding
    durable_gap_wear_paces: Callable   # () -> how many times the share of a durable that wears in a year a household may close of the gap
                                       #  to the stock it wants (durable_stock.gap_share); infinite: the declared share alone
    spin_up_trims_workforce: Callable   # () -> whether the spin-up cuts each skilled trade to the hours employers plan to want (workforce_settle.py)
    spin_up_moves_workers: Callable     # () -> whether workers move between labour areas in the hidden years (spin_up_migration.py)
    basket_quantity_counted: Callable   # (a basket good's opening quantity, what its markets usually trade) -> the quantity the price level counts
    spin_up_stops_early: Callable       # () -> whether the spin-up's first stage ends on its first quiet year (spin_up_stop.py)
    spin_up_seats: Callable             # (the year's schools, whether the economy is settling, working people by labour area, the (trade, area) of each labour market) -> the schools the labour core trains through (spin_up_seats.py)


def planned_hours_bids(_setup, _record, _view, plans, bid_table) -> None:
    """Each producer bids for the hours of the runs it planned on last year's wage, at what an hour is worth to them."""
    plans.write_labour_bids(bid_table)


def expected_sales_hold(expected_sales, _output_cannot_be_kept=None):
    """A producer plans no more runs than it expects to sell, with its stock brought toward its target."""
    return expected_sales


def hold_to_stock_alone(expected_sales, output_cannot_be_kept=None):
    """A producer plans the runs that pay at the price it expects, less what it holds beyond its target stock spread
    over the years a stock is cleared in (more, when it holds less): the market finds the price that sells them, and
    a pile is worked off. No sales figure holds the runs (NaN to the plan: `plan_kernel.plan_rows`), except those of a
    maker whose goods do not keep a year, which has no stock to hold them and plans to its expected sales
    (unkept_goods.py)."""
    if output_cannot_be_kept is None:
        return np.full_like(expected_sales, np.nan)
    return unkept_goods.stock_alone_where_kept(expected_sales, output_cannot_be_kept)


def schedule_bids_with_coin_cost(setup, record, view, plans, bid_table) -> None:
    """Each producer bids for hours as a schedule over the wage (labour_demand.py), a run's cost counting its coin."""
    labour_demand.write_schedule_bids(setup, record, view, plans, bid_table,
                                      coin_charge=coin_cost.charge_at_the_going_rate(setup, view))


def no_respend(_setup, _record, _view, _ledger, _left_markets, _basket_of, _orders) -> None:
    """A market that cleared at one price turned no buyer away at that price: there is no later round."""


RULE_SETS: Dict[str, RuleSet] = {
    SEARCH: RuleSet(sales_the_plan_holds_to=expected_sales_hold, expected_sales_after_close=unkept_goods.expected_sales_as_closed,
                    producer_labour_bids=planned_hours_bids, labour_clearing=clear_labour_by_search,
                    goods_clearing=goods_good_clear.clear_good, goods_respend=goods_respend_year.respend,
                    close_constants=close_pack.constants_array, coin_charge=coin_cost.no_charge,
                    merchant_volumes=merchant_volume_news.delivered_alone,
                    input_orders_after_hiring=input_orders_after_hiring.leave_as_planned,
                    rate_remembered=rate_step.the_cleared_rate,
                    merchant_stock_offered_where_it_stands=merchant_stuck_stock.kept_whole,
                    merchant_cash_for_new_cargo=merchant_stuck_stock.all_cash,
                    merchant_wage_loan=merchant_wage_loans.as_wanted,
                    memory_making_costs=making_cost_alone.of_every_good,
                    memory_cost_of_costless=making_cost_alone.no_cost,
                    servant_hours_counted_on=servant_hours_counted.as_planned,
                    plot_return_for_hours_kept=plot_hours_value.return_of_the_next_hour,
                    opening_issuer_coin=opening_issuer_coin.nothing,
                    durable_gap_wear_paces=durable_stock.unpaced,
                    spin_up_trims_workforce=spin_up_trim.trims,
                    spin_up_moves_workers=spin_up_migration.workers_move,
                    basket_quantity_counted=basket_counted.whole,
                    spin_up_stops_early=spin_up_stop.on_a_quiet_year,
                    spin_up_seats=spin_up_seats.by_masters),
    CLEARING: RuleSet(sales_the_plan_holds_to=hold_to_stock_alone,
                      expected_sales_after_close=unkept_goods.expected_sales_by_takings_where_unkept,
                      producer_labour_bids=schedule_bids_with_coin_cost, labour_clearing=clear_labour_at_one_wage,
                      goods_clearing=goods_clear_one_price.clear_good_at_one_price, goods_respend=no_respend,
                      close_constants=close_pack.constants_array_for_clearing, coin_charge=coin_cost.charge_at_the_going_rate,
                      merchant_volumes=merchant_volume_news.delivered_and_unmet,
                      input_orders_after_hiring=input_orders_after_hiring.resize_to_hired_hours,
                      rate_remembered=rate_step.toward_the_cleared_rate,
                      merchant_stock_offered_where_it_stands=merchant_stuck_stock.part_it_cannot_carry,
                      merchant_cash_for_new_cargo=merchant_stuck_stock.cash_less_carriage,
                      merchant_wage_loan=merchant_wage_loans.within_leverage,
                      memory_making_costs=making_cost_alone.of_goods_made_alone,
                      memory_cost_of_costless=making_cost_alone.the_price_it_had,
                      servant_hours_counted_on=servant_hours_counted.as_served,
                      plot_return_for_hours_kept=plot_hours_value.return_keeping_what_the_plot_grows,
                      opening_issuer_coin=opening_issuer_coin.the_mints_wage_bill,
                      durable_gap_wear_paces=durable_stock.one_wear_pace,
                      spin_up_trims_workforce=spin_up_trim.leaves_the_workforce,
                      spin_up_moves_workers=spin_up_migration.workers_stay,
                      basket_quantity_counted=basket_counted.still_bought,
                      spin_up_stops_early=spin_up_stop.at_its_bound,
                      spin_up_seats=spin_up_seats.open_while_settling),
}


def of(setup) -> RuleSet:
    """The rule set `setup` names, the default one where it names none (a stand-in setup that carries only what a rule
    reads); a name no set carries is an error listing the ones that exist."""
    name = getattr(setup, "rule_set", SEARCH)
    found = RULE_SETS.get(name)
    if found is None:
        raise ValueError("the economy has no rule set %r; it has %s" % (name, ", ".join(sorted(RULE_SETS))))
    return found
