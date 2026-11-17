"""The opening as a resting state of the rules the first year runs under.

Eurace@Unibi (ETACE/eurace_unibi, used with the authors' permission; see NOTICE.md) starts from stocks that agree
with its rules: user manual chapter 10, "If the balance sheets would be inconsistent from the start they would remain
so throughout the entire simulation", and sections 10.1.2 (firm: capital stock large enough that the initial
production needs no further investment, past investment equals depreciation, no initial inventory) and 10.1.3
(household: payment account and share holdings set from the consumption rule's constants). Here each stock is
solved from our rule instead of stored as a multiple. Plain functions; the opening calls them.

Capacity needs no function here: the investment rule (`producers_close._investment`, after Eurace
Firm_calc_input_demands) builds beyond wear only when the planned runs exceed the capacity, so capacity equal to the
planned runs (expected sales) needs no growth, which agrees with a post-warm-up Eurace state's median utilisation of 1.0.
"""
from typing import Dict, Mapping

from . import households_buffer_stock, inventory


def resting_household_purse(mean_income: float, share_wealth: float, claims: float = 0.0) -> float:
    """The cash a household holds before the year's income arrives so that `households_buffer_stock.spending_budget`,
    taken after the income is in (cash = purse + income, as the year's orders see it), spends its income.
    Follows the manual's household initialisation (section 10.1.3: payment account from the consumption constants).
    Without shares the rule's budget is income plus a share of the account held, capped at cash, so spending equals
    income only when cash is the income: the purse is zero. With shares the budget is income plus the yearly share of
    (cash + claims + share wealth - target wealth), which is zero at the target (WEALTH_INCOME_RATIO_TARGET months of
    income): the purse brings cash up to the target wealth beyond the income, never below zero. A post-warm-up Eurace
    state holds wealth at that target, and the manual's initial household holds a payment account and wealth in the
    same relation to its income (user manual section 10.1.3)."""
    if share_wealth <= 0.0:
        return 0.0
    share = households_buffer_stock.yearly_cash_share()
    target = households_buffer_stock.WEALTH_INCOME_RATIO_TARGET / households_buffer_stock.MONTHS_PER_YEAR * mean_income
    share_term = share * (share_wealth - target)
    cash = max(mean_income, -share_term / share - claims)
    return cash - mean_income


def purse_with_property_income(purse: float, property_income: float) -> float:
    """The cash a household opens holding: the purse (`resting_household_purse`, which counts the year's whole income as
    cash) plus the property income it received at the last close, which is in its account when the year's wages
    arrive; the purse counts wages only."""
    return purse + max(0.0, property_income)


def resting_input_stock(planned_runs: float, inputs_per_run: Mapping[str, float], bought_in_year) -> Dict[str, float]:
    """The inputs a producer opens holding. `producers._input_bids` buys the planned runs' need less what is held and
    the year uses it all, so a producer at rest holds an input at the year's start only if it cannot buy it before
    it works (nothing makes it, or its maker clears no earlier: a cycle); the rest (`bought_in_year`) it buys, with
    the cash `working_capital_target` already gives it."""
    if planned_runs <= 0.0:
        return {}
    return {good: planned_runs * per_run for good, per_run in sorted(inputs_per_run.items())
            if per_run > 0.0 and good not in bought_in_year}


def resting_output_stock(expected_yearly_sales: float, outputs_per_run: Mapping[str, float]) -> Dict[str, float]:
    """The output a producer opens holding: `inventory.target_stock` of its expected sales, per good. The output rule
    (`producers.runs_for_stock`, after Eurace Firm_calc_production_quantity: critical stock less current stock) then
    plans exactly the expected sales, with no gap to fill or work off. (The manual's initial inventory is zero and
    a post-warm-up state holds about two per cent of firm assets in inventory; neither is a target-stock rule.)"""
    if expected_yearly_sales <= 0.0:
        return {}
    target = inventory.target_stock(expected_yearly_sales)
    return {good: target * made for good, made in sorted(outputs_per_run.items()) if made > 0.0}


def resting_hours_held(hours_needed: Mapping[str, Mapping[str, Mapping[str, float]]], wages: Mapping[str, float]
                       ) -> Dict[str, Dict[str, Dict[str, float]]]:
    """Hours held, area -> trade -> employer, of an opening whose employers already employ the hours they need.
    Follows the manual's household and firm initialisation (chapter 10; section 10.1.2 step 1 sizes output so labour
    demand is the employment the households already have). A trade with no opening wage, and an employer needing no
    hours, hold nothing."""
    held: Dict[str, Dict[str, Dict[str, float]]] = {}
    for area, by_trade in sorted(hours_needed.items()):
        for trade, by_employer in sorted(by_trade.items()):
            if wages.get(trade) is None:
                continue
            for employer, hours in sorted(by_employer.items()):
                if hours > 0.0:
                    held.setdefault(area, {}).setdefault(trade, {})[employer] = hours
    return held
