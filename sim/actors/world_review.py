"""The founder's seat as the owner of a reviewed business; mixed into the actors' world."""
from typing import Any


class ReviewView:
	needs: Any

	# the year plants shut by a review are dated; the scenario's year when None
	review_year: Any = None

	def founder_review(self) -> Any:
		"""The seat's answers to a business review (sim/agents/business_review.py)."""
		return self.needs.seat_review(self, self.review_year)
