"""What a household pays to guard its coin: it comes from the room the purse and the credit line leave, like any other spending."""


def room_under_credit_line(capital, credit_limit, revenue, upkeep, living_cost, mine_cost):
    """Money the year can still spend without capital ending below the negative of the credit limit."""
    return max(0.0, capital + credit_limit + revenue - upkeep - living_cost - mine_cost)


def coin_guard_paid(owed, room):
    """The guard is paid only to the room; the rest of what is owed goes unguarded."""
    return min(owed, room)
