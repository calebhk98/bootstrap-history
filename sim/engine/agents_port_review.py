"""The founder's seat as the owner of a reviewed business; mixed into `SimWorld`."""
from typing import Any

from .projects_review import SeatReview


class ReviewView:
	_sim: Any

	def founder_review(self) -> SeatReview:
		"""The seat's answers to a business review (sim/agents/business_review.py)."""
		return SeatReview(self)
