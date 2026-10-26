"""Who a household lets go when it cannot meet its payroll."""
import math


def payroll_means(revenue, other_costs, capital, credit_limit):
    """What the household can spend on wages: its takings after every other cost, plus what somebody will still lend it
    (capital is negative in arrears; the credit limit is how far into arrears anyone lets it go)."""
    return revenue - other_costs + max(0.0, capital + credit_limit)


def staff_to_let_go(payroll, means, employees, annual_wage):
    """{trade: whole people} to let go so the wages left fit `means`: dearest trade first, each cut rounded up to whole
    people, nothing cut while the means cover the payroll. `annual_wage` maps a trade to its yearly wage."""
    short = payroll - means
    cuts = {}
    if short <= 0:
        return cuts
    for trade_id in sorted(employees, key=lambda trade: -annual_wage(trade)):
        if short <= 0:
            break
        wage = annual_wage(trade_id)
        if wage <= 0:
            continue
        cut = min(employees[trade_id], math.ceil(short / wage - 1e-9))
        if cut > 0:
            cuts[trade_id] = cut
            short -= cut * wage
    return cuts
