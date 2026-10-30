"""The opening as a resting state of the rules the first year runs under.

Eurace@Unibi (ETACE/eurace_unibi, used with the authors' permission; see NOTICE.md) starts from stocks that agree
with its rules: user manual chapter 10, "If the balance sheets would be inconsistent from the start they would remain
so throughout the entire simulation", and sections 10.1.2 (firm: capital stock large enough that the initial
production needs no further investment, past investment equals depreciation, no initial inventory) and 10.1.3
(household: payment account and share holdings set from the consumption rule's constants). Here each stock is
solved from our rule instead of stored as a multiple. Plain functions; the opening calls them.

What a post-warm-up Eurace state shows against the manual's initial values is in the declarations below.
"""
import math
from typing import Dict, Mapping

from sim.constants import declare

from . import households_buffer_stock, inventory
from .producers import OUTPUT_CHANGE_SHARE_PER_YEAR

OPENING_SPARE_CAPACITY_SHARE = declare(
    "OPENING_SPARE_CAPACITY_SHARE", 0.1, kind="temporary_heuristic",
    unit="share of the opening's required output", source=(
        "Eurace@Unibi user manual section 10.1.2 sizes capital so the initial output needs no investment and "
        "a post-warm-up state (run-trans/0_after_2k_transient.xml, 80 firms) shows median utilisation 1.0 (p10 0.85), "
        "i.e. no standing spare; the 0.1 is ours, not Eurace's"), confidence="D",
    why="A recipe without plant (nothing to wear or to build) still gets room for a good harvest or a rise in demand "
        "to be met from capacity; a recipe whose plant wears out too fast for the growth band to be covered also falls "
        "back to it. Real spare capacity varies by trade and season and is not measured here.",
    retire="Complaints/473: the opening is the stationary state of the rules, with spare capacity only where a rule needs it")


def resting_household_purse(mean_income: float, share_wealth: float, claims: float = 0.0) -> float:
    """The cash a household holds before the year's income arrives so that `households_buffer_stock.spending_budget`,
    taken after the income is in (cash = purse + income, as the year's orders see it), spends exactly its income.
    Follows the manual's household initialisation (section 10.1.3: payment account from the consumption constants).
    Without shares the rule's budget is income plus a share of cash and is capped at cash, so spending equals
    income only when cash is the income: the purse is zero. With shares the budget is income plus the yearly share of
    (cash + claims + share wealth - target wealth), which is zero at the target: the purse is what brings cash up to
    the target wealth (WEALTH_INCOME_RATIO_TARGET months of income) beyond the income, never below zero. A
    post-warm-up Eurace state holds wealth at the target (median 16.7 monthly incomes, of which the payment account
    is about 9) against the manual's initial 25 (payment account 10 to 15)."""
    if share_wealth <= 0.0:
        return 0.0
    target = households_buffer_stock.WEALTH_INCOME_RATIO_TARGET / households_buffer_stock.MONTHS_PER_YEAR * mean_income
    return max(0.0, target - share_wealth - claims - mean_income)


def resting_output_stock(expected_yearly_sales: float, outputs_per_run: Mapping[str, float]) -> Dict[str, float]:
    """The output a producer opens holding: `inventory.target_stock` of its expected sales, per good. The output rule
    (`producers.runs_for_stock`, after Eurace Firm_calc_production_quantity: critical stock less current stock) then
    plans exactly the expected sales, with no gap to fill or work off. (The manual's initial inventory is zero and
    a post-warm-up state holds about two per cent of firm assets in inventory; neither is a target-stock rule.)"""
    if expected_yearly_sales <= 0.0:
        return {}
    target = inventory.target_stock(expected_yearly_sales)
    return {good: target * made for good, made in sorted(outputs_per_run.items()) if made > 0.0}


def spare_capacity_share(recipe) -> float:
    """The capacity above expected sales that a recipe's first year needs no investment beyond replacing wear
    (Eurace manual 10.1.2: past investment equals depreciation). The year-close rule
    (`producers_close.close_year`, `_expansion`) builds when expected sales plus OUTPUT_CHANGE_SHARE_PER_YEAR of
    capacity exceed the capacity left after a year's wear (one over the plant life), so capacity must be expected sales
    over (one less the wear share less that band), and the spare share is that less one. A recipe with no plant, or
    whose plant wears out too fast for any capacity to meet the condition, keeps OPENING_SPARE_CAPACITY_SHARE."""
    life = recipe.plant_life_years
    if life <= 0.0:
        return OPENING_SPARE_CAPACITY_SHARE
    kept = 1.0 - 1.0 / life - OUTPUT_CHANGE_SHARE_PER_YEAR
    return 1.0 / kept - 1.0 if kept > 0.0 and math.isfinite(kept) else OPENING_SPARE_CAPACITY_SHARE
