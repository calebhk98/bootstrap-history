"""A firm held back for want of credit says how much equity it would raise."""
from typing import Any

NEED_KEY = "equity_need"


def note_need(firm: Any, shortfall: float) -> None:
	"""A firm's expansion is blocked for want of credit: it will raise `shortfall` as equity."""
	firm.record.plan[NEED_KEY] = max(shortfall, float(firm.record.plan.get(NEED_KEY, 0.0)))
