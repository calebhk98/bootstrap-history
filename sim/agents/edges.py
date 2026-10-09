"""Named edges: the counterparty of a posting whose other side is not an actor the simulation models.

An edge is a named account outside the actors. Money paid to it leaves every purse, money paid from it
enters one, so purses and edges together stay what they were; what crossed each edge is its `volume`.
A name that stands for people or businesses the simulation will one day model as actors (workers,
suppliers) is where those actors' purses land once they exist.
"""
from typing import Any, Dict

EDGE_WORKERS = "edge:workers"            # wages and fees paid to people the founder's labour market holds
EDGE_SUPPLIERS = "edge:suppliers"        # inputs, upkeep and project work bought from the economy
EDGE_CUSTOMERS = "edge:customers"        # what the economy pays for a concern's takings
EDGE_LANDOWNERS = "edge:landowners"      # land and forest bought from, or sold to, the economy
EDGE_BUILDERS = "edge:builders"          # building work paid for (housing, nitre beds, mines)
EDGE_OFFICIALS = "edge:officials"        # bribes and gifts to people with influence
EDGE_CREDITORS = "edge:creditors"        # interest on arrears and what creditors seize
EDGE_DESTROYED = "edge:destroyed"        # value lost to fire, wreck and failure: a sink, not a payee
EDGE_ECONOMY = "edge:economy"            # the agent economy's households and merchants, outside the registry
EDGE_STATE_SPENDING = "edge:state spending"  # what a state's budget lines pay to people and suppliers
EDGE_TAXPAYERS = "edge:taxpayers"        # revenue from taxpayers who are not modelled actors
EDGE_INTEREST = "edge:interest"          # interest borrowers pay, until the market pays it out to lenders
EDGE_PATRONAGE = "edge:patronage"        # what a state grants a patron; the grant works through its effects, not a purse
EDGE_OPENING = "edge:opening"            # money an actor starts the game with
EDGE_POOLED_CAPITAL = "edge:pooled capital"  # savings pooled to found a business, and taken back at its end
EDGE_ENTRY_PREMIUM = "edge:entry premium"    # what a crowded market charges an entrant to get in
EDGE_MARKET = "edge:market"              # goods bought and sold by a trader
EDGE_FREIGHT = "edge:freight"            # carriers paid for carrying a cargo
EDGE_EMPLOYERS = "edge:employers"        # what employers pay a household for its own work
EDGE_SLAVE_TRADERS = "edge:slave traders"  # what people bought as slaves cost
EDGE_COIN_GUARDS = "edge:coin guards"    # guards paid to keep coin
EDGE_THIEVES = "edge:thieves"            # what thieves take; people in the economy, so it is theirs, not destroyed


class Edge:
	"""One named edge, reading and writing its balance and volume in the state that holds it."""

	def __init__(self, name: str, balances: Dict[str, float], volumes: Dict[str, float]) -> None:
		self.name = name
		self.actor_id = name
		self._balances = balances
		self._volumes = volumes

	def credit(self, amount: float, purpose: Any) -> None:
		"""Money paid to the edge."""
		self._balances[self.name] = self._balances.get(self.name, 0.0) + float(amount)
		self._volumes[self.name] = self._volumes.get(self.name, 0.0) + abs(float(amount))

	def debit(self, amount: float, purpose: Any) -> None:
		"""Money paid out by the edge."""
		self._balances[self.name] = self._balances.get(self.name, 0.0) - float(amount)
		self._volumes[self.name] = self._volumes.get(self.name, 0.0) + abs(float(amount))
