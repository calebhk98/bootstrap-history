"""The commands other modules send polity: standing changes of the acting seat, the society's value weights and the records of
the state of a country (its army, its tiles' unrest, its risings, its ruler).

Needs: country_world."""
from sim.agents.api import army_raising
from sim.refusal import Refusal

from . import constants
from .state import STANDING, VALUES
from .value_weight import VALUE_WEIGHT_CEILING, VALUE_WEIGHT_FLOOR, shifted


class Appliers:

	# ---- the acting seat's standing ----

	def raise_scandal(self, command):
		self.seat.scandal += command.scandal
		if self.seat.scandal_last_year is not None:
			self.seat.scandal_last_year += command.scandal
		self.bump(STANDING)

	def add_scandal(self, command):
		self.seat.scandal += command.amount
		self.bump(STANDING)

	def record_bribe(self, command):
		self.seat.bribes_ytd = command.bribes_year_to_date
		self.seat.scandal = command.scandal
		self.update_protection()

	def scale_protection(self, command):
		self.seat.protection *= command.share
		self.bump(STANDING)

	def scale_familiarity(self, command):
		self.seat.familiarity *= command.share
		self.bump(STANDING)

	def gain_reputation(self, command):
		self.seat.reputation = min(constants.REPUTATION_CEILING, self.seat.reputation + command.amount)
		self.bump(STANDING)

	def set_reputation(self, command):
		self.seat.reputation = command.value
		self.bump(STANDING)

	def add_governance(self, command):
		self.seat.gov += command.amount

	def answer_state_demands(self, command):
		return self.set_household_stance(command.stance, command.service)

	def withdraw_command(self, command):
		return self.withdraw_from_public_life()

	def settle_command(self, command):
		return self.settle_with_state(command.target, command.amount)

	def transfers_command(self, command):
		self.carry_out_transfers(command.node_id)

	def renew_command(self, command):
		self.renew_standing()
		self.bump(STANDING)

	def close_year_command(self, command):
		self.close_standing_year()

	# ---- the society's value weights ----

	def set_value_weights(self, command):
		self.world.value_weights = dict(command.weights)
		self.bump(VALUES)

	def shift_value_weight(self, command):
		weights = self.world.value_weights
		if command.field not in weights:
			return Refusal("not_a_value_weight", "the society has no value weight %s" % command.field, field=command.field)
		before = weights[command.field]
		weights[command.field] = shifted(before, command.delta, VALUE_WEIGHT_FLOOR, VALUE_WEIGHT_CEILING)
		self.bump(VALUES)
		return before, weights[command.field]

	# ---- the records of a country's state ----

	def _government_record(self, owner):
		return self.needs.country_world[owner].government().record

	def strike_from_force(self, command):
		world = self.needs.country_world[command.owner]
		world.government().record.army = army_raising.struck_from_force(float(world.soldiers_under_arms()), command.killed)

	def set_land_taken_memory(self, command):
		self._government_record(command.owner).land_taken_by_tile = command.by_tile

	def register_people(self, command):
		registered = self._government_record(command.owner).registered_people
		for tile, count in command.by_tile.items():
			registered[tile] = max(registered.get(tile, 0.0), count)

	def set_grievance_reference(self, command):
		self._government_record(command.owner).grievance_reference = command.reference

	def reset_state_unrest(self, command):
		record = self._government_record(command.owner)
		record.unrest_by_tile, record.hold_by_tile = {}, {}

	def set_tile_reading(self, command):
		record = self._government_record(command.owner)
		record.unrest_by_tile[command.tile] = command.unrest
		record.hold_by_tile[command.tile] = command.hold

	def record_rising(self, command):
		record = self._government_record(command.owner)
		record.risings = (record.risings + [command.entry])[-command.kept:]

	def replace_ruler(self, command):
		record = self._government_record(command.owner)
		record.ruler_age = command.age
		record.ruler_backer = command.backer
		record.accession_due = True

	def close_succession_dispute(self, command):
		self._government_record(command.owner).succession_challenger = ""
