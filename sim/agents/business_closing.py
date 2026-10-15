"""Ending a business or moving a plant to another owner."""
from typing import Any

from .business import Business
from .business_plant import Plant


def release_plant(business: Business, entry_key: str, world: Any) -> Plant:
	"""Take a plant out of the business to hand to another owner, dated even if no opening year was recorded."""
	plant = business.close_plant(entry_key)
	if plant is None:
		raise KeyError("the business runs no plant of " + entry_key)
	if plant.opened_year is None:
		plant.opened_year = world.year
	return plant
