"""The coin a money's issuer opens holding (the rule sets' `opening_issuer_coin`). The issuer pays its mint's crew out
of its own account before the year's revenue comes in (`mint_labour.staff`), so an issuer that opens with nothing hires
no crew in the first year, strikes nothing, and the crew the opening placed for the mint leaves its trades."""
from . import mint, state_budget


def nothing(_setup, _record, _view) -> float:
    """The issuer opens with no coin: its first year's mint is staffed from nothing."""
    return 0.0


def the_mints_wage_bill(setup, record, view) -> float:
    """The issuer opens holding what its mint's crew can cost in the first year (`mint.wage_funding`), as a producer
    opens holding its year's working coin, and enough besides that its own plan for the year leaves that much
    (`state_budget.cash_that_leaves`)."""
    return state_budget.cash_that_leaves(setup.state_policy, mint.wage_funding(setup, record, view))
