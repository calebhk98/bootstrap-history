"""What a household keeps in reputation for what it has built, and how much easier reputation makes everything.

Needs: techniques_held, techniques_granted, effect_sum."""
from . import rules


class StandingFloor:

	def standing_floor(self):
		"""The reputation you keep for what you have built, whatever else happens. Novelty fades; a corpus in three libraries, a
		school with students and a senator who will receive you do not."""
		needs = self.needs
		standing = rules.earned_standing(len(needs.techniques_held()), len(needs.techniques_granted()))
		standing = needs.effect_sum("standing", standing)
		return rules.standing_after_scandal(standing, self.seat.scandal)

	def rep_factor(self):
		"""How much easier reputation makes everything. 1.0 at zero reputation."""
		return rules.reputation_ease(self.seat.reputation)
