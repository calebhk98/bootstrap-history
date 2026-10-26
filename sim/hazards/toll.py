"""Whether a hazard took anything from the household it met, so the log can say "nothing to take" plainly."""

PEOPLE_FLOOR = 0.05
MONEY_FLOOR = 0.5


def staff_loss_toll(people_before, cash_lost):
    """Which parts of a plague hit the household: (people, takings), each a bool. Neither means it had nothing to
    take."""
    return people_before > PEOPLE_FLOOR, cash_lost > MONEY_FLOOR


def sack_toll(capital_taken, people_gone, projects_reset):
    """Which parts of a sack hit the household: (capital, people, projects), each a bool."""
    return capital_taken > MONEY_FLOOR, people_gone > PEOPLE_FLOOR, bool(projects_reset)
