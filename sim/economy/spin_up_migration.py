"""Whether workers move between labour areas during the hidden spin-up (the rule sets' `spin_up_moves_workers`). In a
game the labour market's moves are sent to demography, which moves the people (sim/markets/port_year.py); the hidden
years step the economy alone, so a worker who moves leaves the household that eats on the tile behind, and a tile whose
wage is low loses its hands year after year while its people stay. Where they stay put, the hidden years settle the
economy with the people where the scenario places them."""


def workers_move() -> bool:
    """Workers weigh the routes out of their area in the hidden years as in any year."""
    return True


def workers_stay() -> bool:
    """No worker leaves its area in the hidden years."""
    return False


def routes_open(settling: bool, moves_while_settling: bool) -> bool:
    """Whether the year's labour market has routes between areas: always outside the hidden spin-up, and inside it
    only where the rule set moves workers then."""
    return not settling or moves_while_settling
