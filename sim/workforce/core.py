"""The workforce module's labour core, the staffing scale and the reason for the last refused purchase of people."""
from sim.assembly.api import Part
from sim.labour.api import Labour

from .world import WorkforceWorld


class Core(Part):

	def __init__(self, module):
		super().__init__(module)
		self._buy_refusals = {}      # seat id -> why its last purchase of people was refused, for the screen that asked; never saved

	def setup(self):
		self.reads = WorkforceWorld(self.needs, self.module, self.parts)   # what labour reads of the game
		self.labour = Labour(self.reads)

	def last_buy_refusal(self):
		return self._buy_refusals.get(self.clock.acting_seat)

	def note_buy_refusal(self, command):
		self._buy_refusals[self.clock.acting_seat] = command.refusal
