"""The founder's seat as the owner of a reviewed business; mixed into `SimWorld`."""
from typing import Any

from .projects_review import SeatReview


class ReviewView:
	_sim: Any

	# the year plants shut by a review are dated; the scenario's year when None
	review_year: Any = None

	def founder_review(self) -> SeatReview:
		"""The seat's answers to a business review (sim/agents/business_review.py)."""
		return SeatReview(self, self.review_year)
