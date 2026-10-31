"""An employer's layoffs and vacancies from the hours it holds against the hours it needs.

Follows Eurace Firm_set_labour_market_actions (Labour/Firm_Employer_Functions.c): a firm holding more employees than it
needs lays off the difference and posts no vacancy; holding fewer, it lays off none and posts the difference as
vacancies. Eurace counts employees, here the count is hours. Eurace picks whom to dismiss (lowest general skill first,
Firm_send_redundancies); the market records hours per employer, not per worker, so that does not apply here. The random
monthly dismissals (Firm_send_random_redundancies) are in applications.py.
"""


def hours_to_lay_off(held: float, needed: float) -> float:
    """Hours held beyond the hours needed (Eurace NO_REDUNDANCIES)."""
    return max(0.0, held - needed)


def hours_vacant(held: float, needed: float) -> float:
    """Hours needed beyond the hours held (Eurace VACANCIES)."""
    return max(0.0, needed - held)
