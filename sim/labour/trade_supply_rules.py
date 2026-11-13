"""How many people of a trade exist, how many hours of them the market can offer, and when a hire would leave nobody."""

TOLERANCE_IN_PEOPLE = 1e-6


def people_who_exist(national_estimate, employed):
    """The national estimate, never below the household's own staff (a collapse can leave the estimate under them)."""
    return max(national_estimate, employed)


def supply_hours(hours_on_offer, people_existing, hours_per_person_year, people_alive):
    """The hours a market offers, never more than every existing person of the trade works in a year, nor more than the working
    people alive now work (the trade's figures are the clearing's; a later death in the year lowers `people_alive` under them)."""
    return min(hours_on_offer, people_existing * hours_per_person_year, max(0.0, people_alive) * hours_per_person_year)


def hire_leaves_nobody(on_books, rivals_staff, count, people_existing):
    """True when the household's staff, firms' and states' staff and the hire together exceed the people who exist."""
    return on_books + rivals_staff + count > people_existing + TOLERANCE_IN_PEOPLE
