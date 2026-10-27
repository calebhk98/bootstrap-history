"""The ventures module's rules as plain functions."""


def upkeep_quote(upkeep_now, upkeep_at_full_staffing, price_index):
	"""Yearly running cost at the current price level: as staffed today (what the ledger charges) and with every place filled."""
	return {"now": upkeep_now * price_index, "at_full_staffing": upkeep_at_full_staffing * price_index}
