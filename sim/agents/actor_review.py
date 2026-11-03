"""`ActorReview`: an actor's answers when its business is reviewed. Reached as `actor.review`, handed to `Business.reviews` as the owner.

The defaults of `Reviewable` suit an actor with no staffing pool, no creditors at the door and no plants it keeps for other reasons
than their takings (a firm); the plants are the actor's business.
"""
from typing import Any

from .business_review import Reviewable


class ActorReview(Reviewable):

	def __init__(self, actor: Any) -> None:
		self.actor = actor

	@property
	def business(self) -> Any:
		return self.actor.business
