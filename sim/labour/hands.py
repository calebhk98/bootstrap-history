"""How many people a household can put on a project: plain arithmetic, one rule for scholars and craftsmen."""


def contracted_hours_of(contract_hours, counts_trade):
    """The hours bought under contract in the trades `counts_trade` accepts."""
    return sum(hours for trade, hours in contract_hours.items() if counts_trade(trade))


def hands_available(staff, founder_alive, contracted_hours, hours_per_person_year):
    """Staff on the payroll, the founder while alive, and a person for every full year of contracted hours."""
    return staff + (1.0 if founder_alive else 0.0) + contracted_hours / hours_per_person_year
