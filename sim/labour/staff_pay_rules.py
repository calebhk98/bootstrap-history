"""What staff are paid: plain functions of the headcounts and the market's wage."""


def wage_bill_of(heads, pay_of_trade):
    """What the standing staff costs in a year: the head of each trade times its pay."""
    return sum(head * pay_of_trade(trade) for trade, head in heads.items())


def wage_for_hours_of(annual_wage, hours_per_person_year, hours, reputation, bonus_cap, bonus_scale):
    """What `hours` of the founder's own work pay: the trade's hourly rate (its yearly wage over the hours in a year) times a
    bonus of reputation over `bonus_scale`, capped at `bonus_cap`; a reputation below nothing earns a smaller rate."""
    rate = annual_wage / hours_per_person_year
    return hours * rate * (1.0 + min(bonus_cap, reputation / bonus_scale))
