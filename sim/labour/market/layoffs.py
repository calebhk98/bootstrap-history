"""An employer's layoffs from the hours it holds against the hours it needs.

Follows Eurace Firm_set_labour_market_actions (Labour/Firm_Employer_Functions.c): a firm holding more employees than it
needs lays off the difference; holding fewer, it lays off none (the vacancies are what clearing.py leaves unfilled).
Eurace counts employees, here the count is hours. Eurace picks whom to dismiss (lowest general skill first,
Firm_send_redundancies); the market records hours per employer, not per worker, so that does not apply here. The random
monthly dismissals (Firm_send_random_redundancies) are in applications.py.
"""


def hours_to_lay_off(held: float, needed: float) -> float:
    """Hours held beyond the hours needed (Eurace NO_REDUNDANCIES)."""
    return max(0.0, held - needed)
