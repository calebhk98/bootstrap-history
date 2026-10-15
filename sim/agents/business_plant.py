"""`Plant`: one production entry's physical unit that a business runs."""
from dataclasses import dataclass
from typing import Optional


@dataclass
class Plant:
	"""What a business keeps about one plant it runs. Everything else (crew by trade, upkeep, takings) is derived
	from the entry. `entry_key` is a tech node id until entries are keyed on their own (transitional)."""
	entry_key: str = ""
	# how many times the entry's founding size the plant runs at
	size: float = 1.0
	# the year it began operating; None when nobody recorded one
	opened_year: Optional[int] = None
	# share of the crew found in the labour pool last year
	crew_found: float = 1.0
	# what the plant made last year after levy and royalty; None until a year has been tallied
	margin: Optional[float] = None
