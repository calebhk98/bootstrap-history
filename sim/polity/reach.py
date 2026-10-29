"""How far the people grant the state the right to command, and what that does to what the state can do.

A work declares `mechanics.state_legitimacy = {"flat" | "per_unit" | "per_sqrt_unit": v}` (negative lowers it): a paper that
exposes officials lowers it, a paper the state licenses to print its decrees raises it. With no holder it is exactly 1.0. The
state's reach is the share of what is due that the officials it pays collect over the roads from its seat
(`sim/agents/collection.py`); its authority, what it can collect, enforce and borrow against, is that reach times this share.
No civilisation file states either.

Needs: effect_sum, actor_world, year, held_and_running_versions, population_total."""
from . import constants, rules


class Reach:

	def state_legitimacy(self):
		"""The share of its reach that the people's consent leaves the state, between the floor and the ceiling."""
		return rules.legitimacy_share(self.needs.effect_sum("state_legitimacy", 1.0), constants.LEGITIMACY_FLOOR,
		                              constants.LEGITIMACY_CEILING)

	def state_authority(self):
		"""What the state can actually organise and compel: its reach, held up or worn down by consent."""
		return self.state_reach() * self.state_legitimacy()

	def _reach_key(self, unfunded):
		done_version, operating_version = self.needs.held_and_running_versions()
		return (self.needs.year(), done_version, operating_version, round(self.needs.population_total()), unfunded)

	def state_reach(self):
		"""The share of what is due that the home state's paid officials collect, kept for as long as the year, the works held,
		the people and the officials' unpaid share are unchanged."""
		world = self.needs.actor_world()
		unfunded = world.government().record.unfunded.get("administration", 0.0)
		key = self._reach_key(unfunded)
		memo = self._state_reach_memo
		if memo is None or memo[0] != key:
			memo = self._state_reach_memo = (key, world.collectible_share())
		return memo[1]

	def order_reach(self):
		"""The share of the home people its employed guards watch over the roads from the seat."""
		return self._staff_reach("guards", "order_share")

	def inspection_reach(self):
		"""The share of the home people whose claims and workings its employed inspectors check."""
		return self._staff_reach("inspectors", "inspection_share")

	def forest_reach(self):
		"""The share of the home people whose woodland tenure its employed foresters keep."""
		return self._staff_reach("foresters", "forest_share")

	def _staff_reach(self, line_name, share_name):
		world = self.needs.actor_world()
		unfunded = world.government().record.unfunded.get(line_name, 0.0)
		key = self._reach_key(unfunded)
		memo = self._staff_reach_memo.get(line_name)
		if memo is None or memo[0] != key:
			memo = self._staff_reach_memo[line_name] = (key, getattr(world, share_name)())
		return memo[1]
