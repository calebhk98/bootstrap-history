"""The base of the agent economy's view parts: the two readers every one of them uses."""
from sim.assembly.api import Part


class AgentViewPart(Part):

	def _economy(self):
		return self.parts.market_objects.economy

	def _answering(self):
		"""The parts of the port over the agent economy, or None while the economy opens."""
		return self.parts.market_objects.economy.answering()
