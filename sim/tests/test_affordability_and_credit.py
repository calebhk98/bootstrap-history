"""spending_power("buy" vs "start"/"open"), credit_limit, arrears and insolvency rules.

What could be raised for each kind of spend, the warning before the line, appearances, a concern's payback and the
reputation an insolvency takes are tested on built numbers (`affordability`, `capital_market`). The game's commands,
callers over stand-ins are test_credit_wiring, test_cash_gates_wiring and test_auto_open_gates."""

QUICK_TOPIC = True
from .harness import *  # noqa: F401,F403
from sim.finance.api import affordability
from sim.finance.rules import calculate_credit_ceiling
from sim.world import capital_market

# --- spending_power: what could be raised for each kind of spend
HALF = 0.5
check("a purchase may draw the ordinary share of the line, a start the whole of it",
      abs(affordability.spending_power_of("buy", 400.0, 210.0, HALF) - 505.0) < 1e-9
      and abs(affordability.spending_power_of("start", 400.0, 210.0, HALF) - 610.0) < 1e-9,
      (affordability.spending_power_of("buy", 400.0, 210.0, HALF), affordability.spending_power_of("start", 400.0, 210.0, HALF)))
check("the debt already carried counts against a purchase: 500 into a 210 line can raise nothing, never a negative amount",
      affordability.spending_power_of("buy", -500.0, 210.0, HALF) == 0.0
      and affordability.spending_power_of("start", -500.0, 210.0, HALF) == 0.0
      and affordability.spending_power_of("buy", -1000.0, 0.0, HALF) == 0.0)
check("a hole smaller than the drawable part of the line leaves the rest to raise",
      abs(affordability.spending_power_of("buy", -50.0, 210.0, HALF) - 55.0) < 1e-9)
check("a door fee on a concern already built does not count the hole: it asks only what the line could advance",
      abs(affordability.spending_power_of("open", -100.0, 210.0, HALF) - 105.0) < 1e-9
      and abs(affordability.spending_power_of("open", 400.0, 210.0, HALF) - 505.0) < 1e-9)
check("past the line nobody lends, so nothing can be raised for a door fee either",
      affordability.spending_power_of("open", -300.0, 210.0, HALF) == 0.0)

# --- the credit line warns before it is crossed, once, and not once it is past
check("a household that is not in arrears, or has no line, is not warned",
      affordability.near_limit(105.0, 100.0, False)[0] is False and affordability.near_limit(0.0, 100.0, False)[0] is False
      and affordability.near_limit(-10.0, 0.0, False)[0] is False)
check("the credit limit warns you BEFORE you cross it, with the share of the line used",
      affordability.near_limit(-75.0, 100.0, False) == (True, True, 0.75), affordability.near_limit(-75.0, 100.0, False))
check("...and does not say it again every year while in the band", affordability.near_limit(-75.0, 100.0, True)[0] is False
      and affordability.near_limit(-75.0, 100.0, True)[1] is True)
check("the limit warning is about what is ahead of you, not behind: nothing once past the line",
      affordability.near_limit(-103.0, 100.0, False)[0] is False)
check("coming back out of the band lets the warning be said again",
      affordability.near_limit(-50.0, 100.0, True)[1] is False and affordability.near_limit(-75.0, 100.0, False)[0] is True)
check("the band starts where the constant says",
      affordability.near_limit(-100.0 * affordability.NEAR_LIMIT_FROM * 0.99, 100.0, False)[0] is False
      and affordability.near_limit(-100.0 * affordability.NEAR_LIMIT_FROM, 100.0, False)[0] is True)

# --- a lender does not lend more than income can carry, whatever the money costs
for _rate in (0.04, 0.12, 0.5):
    _earning = 1000.0
    _serviceable = capital_market.serviceable_debt(_earning, _rate, 0.5)
    _line = calculate_credit_ceiling(1.0e9, 0.0, _serviceable)
    check("a grand friend does not lend you more than your income can carry: at a market rate of %.2f the interest on the "
          "whole line stays under what you earn" % _rate,
          _line * _rate < _earning and _line <= _serviceable, (_line, _rate, _earning))
check("what a lender will advance is the least of what the name vouches for, what income can carry and what lenders hold",
      calculate_credit_ceiling(900.0, 0.0, 500.0, market_cap=300.0) == 300.0
      and calculate_credit_ceiling(900.0, 0.0, 500.0) == 500.0 and calculate_credit_ceiling(400.0, 0.0, 500.0) == 400.0)
check("the running costs are the floor of the line, at this society's prices",
      calculate_credit_ceiling(50.0, 120.0, 80.0, price_index=2.0) == 240.0)

# --- status upkeep is conditional on being able to afford it
check("a ruined household (nothing left after eating) stops keeping up appearances beyond the wealth it still has",
      affordability.appearances_spending(500.0, 0.0, 0.0, 0.015, 0.75) == 0.0)
check("...and a household that can afford the show still pays for it, but never more than the nominal figure plus the "
      "wealth share it must track",
      affordability.appearances_spending(500.0, 2.0e6, 1.0e6, 0.015, 0.75) == 500.0 + 2.0e6 * 0.015
      and affordability.appearances_spending(500.0, 0.0, 400.0, 0.015, 0.75) == 300.0)
check("appearances come out of what is left, not the other way about",
      affordability.appearances_spending(500.0, 0.0, 100.0, 0.015, 0.75) == 75.0)

# --- an earning concern opens in arrears on its own payback
check("a concern's payback is its capex over what it nets a year",
      affordability.payback_years(600.0, 500.0, 100.0) == 1.5 and affordability.payback_years(1.0, 10.0, 10.0) == 100.0)
check("deep in arrears, a concern opens only if it pays for its own doors within the limit",
      affordability.opens_in_deep_arrears(1.0, 3.0) and affordability.opens_in_deep_arrears(3.0, 3.0)
      and not affordability.opens_in_deep_arrears(3.5, 3.0))
check("deep in arrears is past a share of the credit line, and needs arrears at all",
      affordability.deep_in_arrears(-60.0, 100.0, 0.5) and not affordability.deep_in_arrears(-40.0, 100.0, 0.5)
      and not affordability.deep_in_arrears(10.0, 100.0, 0.5))

# --- an insolvency announces what a reputation penalty actually took
check("a reputation penalty announces what it actually took: the whole hit, or what was left of the name",
      affordability.reputation_hit_taken(12.0, 50.0) == 12.0 and affordability.reputation_hit_taken(12.0, 4.9) == 4.9)
check("...and nothing when there was nothing left to take", affordability.reputation_hit_taken(12.0, 0.0) == 0.0
      and affordability.reputation_hit_taken(12.0, -3.0) == 0.0)
# (the room a household can fund shrinking by the arrears it owes is funding_parts, in test_affordability_warning)

