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
from typing import Dict, Mapping, Tuple

from . import households_buffer_stock, inventory


def resting_household_purse(mean_income: float, share_wealth: float, claims: float = 0.0,
                            extra_spending: float = 0.0) -> float:
    """The cash a household holds before the year's income arrives so that `households_buffer_stock.spending_budget`,
    taken after the income is in (cash = purse + income, as the year's orders see it), spends its income plus
    `extra_spending` (what its own plot frees from the budget: the floors it grows are cut from its bids after the
    budget is set, so the budget must be that much larger for the money it spends on the market to equal its income).
    Follows the manual's household initialisation (section 10.1.3: payment account from the consumption constants).
    Without shares and without extra spending the rule's budget is income plus a share of the account held, capped at
    cash, so spending equals income only when cash is the income: the purse is zero. With shares the budget is
    income plus the yearly share of (cash + claims + share wealth - target wealth), which is zero at the target
    (WEALTH_INCOME_RATIO_TARGET months of income): the purse brings cash up to the target wealth beyond the income,
    never below zero. The extra spending is the yearly share of the account held: the purse is that much larger
    (and never less than the extra itself, which the cap at cash needs). A post-warm-up Eurace state holds wealth at
    the target (median 16.7 monthly incomes, of which the payment account is about 9) against the manual's initial 25
    (payment account 10 to 15)."""
    extra_spending = max(0.0, extra_spending)
    if share_wealth <= 0.0 and extra_spending <= 0.0:
        return 0.0
    share = households_buffer_stock.yearly_cash_share()
    share_term = 0.0
    if share_wealth > 0.0:
        target = households_buffer_stock.WEALTH_INCOME_RATIO_TARGET / households_buffer_stock.MONTHS_PER_YEAR * mean_income
        share_term = share * (share_wealth - target)
    cash = max(mean_income + extra_spending, (extra_spending - share_term) / share - claims)
    return cash - mean_income


def resting_output_stock(expected_yearly_sales: float, outputs_per_run: Mapping[str, float]) -> Dict[str, float]:
    """The output a producer opens holding: `inventory.target_stock` of its expected sales, per good. The output rule
    (`producers.runs_for_stock`, after Eurace Firm_calc_production_quantity: critical stock less current stock) then
    plans exactly the expected sales, with no gap to fill or work off. (The manual's initial inventory is zero and
    a post-warm-up state holds about two per cent of firm assets in inventory; neither is a target-stock rule.)"""
    if expected_yearly_sales <= 0.0:
        return {}
    target = inventory.target_stock(expected_yearly_sales)
    return {good: target * made for good, made in sorted(outputs_per_run.items()) if made > 0.0}


def resting_labour_contracts(hours_needed: Mapping[str, Mapping[str, Mapping[str, float]]], wages: Mapping[str, float]
                             ) -> Tuple[Dict[str, Dict[str, Dict[str, float]]], Dict[str, Dict[str, Dict[str, float]]]]:
    """(hours held, wage each hour is paid), area -> trade -> employer, of an opening whose employers already employ
    the hours they need at the trade's opening wage. Follows the manual's household and firm initialisation
    (chapter 10; section 10.1.2 step 1 sizes output so labour demand is the employment the households already
    have), and the contract rule (`labour.market.clearing.contracted_wage`, after Eurace Household_receive_wage and
    Firm_update_wage_offer): an hour held is paid its contract and only new hires clear at the market, so the hours
    nobody hires (visible idle hours) do not pull the wage of those employed down in the first year. A trade with
    no opening wage, and an employer needing no hours, hold nothing."""
    held: Dict[str, Dict[str, Dict[str, float]]] = {}
    paid: Dict[str, Dict[str, Dict[str, float]]] = {}
    for area, by_trade in sorted(hours_needed.items()):
        for trade, by_employer in sorted(by_trade.items()):
            if wages.get(trade) is None:
                continue
            for employer, hours in sorted(by_employer.items()):
                if hours > 0.0:
                    held.setdefault(area, {}).setdefault(trade, {})[employer] = hours
                    paid.setdefault(area, {}).setdefault(trade, {})[employer] = wages[trade]
    return held, paid
