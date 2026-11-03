"""What staff are paid: plain functions of the headcounts and the market's wage."""


def wage_bill_of(heads, pay_of_trade):
    """What the standing staff costs in a year: the head of each trade times its pay."""
    return sum(head * pay for trade, head in heads.items() for pay in [pay_of_trade(trade)] if pay is not None)


def wage_for_hours_of(annual_wage, hours_per_person_year, hours):
    """What `hours` of the founder's own work pay at the trade's one market wage: its yearly wage over the hours in a year, times the hours."""
    return hours * annual_wage / hours_per_person_year
