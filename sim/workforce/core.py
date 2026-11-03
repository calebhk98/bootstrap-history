"""The workforce module's labour core, the staffing scale and the reason for the last refused purchase of people."""
from sim.assembly.api import Part
from sim.labour.api import Labour

from .world import WorkforceWorld


class Core(Part):

	def __init__(self, module):
		super().__init__(module)
		self._staff_scales = {}      # seat id -> the share of the institutional staff ceiling its income can pay; worked out each staff step, never saved
		self._buy_refusals = {}      # seat id -> why its last purchase of people was refused, for the screen that asked; never saved

	def setup(self):
		self.labour = Labour(WorkforceWorld(self.needs, self.module, self.parts))

	def staff_scale(self):
		"""The affordability scale `staff_capacity` last worked out for the acting seat (all of the ceiling before the first)."""
		return self._staff_scales.get(self.clock.acting_seat, 1.0)

	def set_staff_scale(self, scale):
		self._staff_scales[self.clock.acting_seat] = scale

	def last_buy_refusal(self):
		return self._buy_refusals.get(self.clock.acting_seat)

	def note_buy_refusal(self, command):
		self._buy_refusals[self.clock.acting_seat] = command.refusal
