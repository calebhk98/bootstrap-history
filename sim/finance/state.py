"""The state finance owns: one seat's debt, its freeze, its insolvency count and its bondage."""
from dataclasses import dataclass
from typing import Optional


@dataclass
class FinanceSeat:
	interest_paid: Optional[float] = None   # all the interest the household has paid; None until it first pays some
	bondage_years_left: float = 0.0
	bondage_debt: float = 0.0
	credit_frozen_until: int = 0            # nobody funds new work before this year
	insolvent_years: int = 0                # consecutive years the household's income did not cover its costs in arrears
	last_settlement: int = -999
	# interest the household could not draw on its facility, and the consecutive years it has owed some (sim/agents/borrowing.py)
	interest_arrears: float = 0.0
	arrears_years: int = 0
	said_near_limit: Optional[bool] = None  # whether the warning that comes before the credit line was given
