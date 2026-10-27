"""One-line forwarders from the old `Sim` names of the ventures topic to the ventures module, for callers not yet in a module.

The screens, the agent economy's production port and the tests still say `sim.venture_real_earnings(node)`, `sim.open_venture(node)` or
`sim.sell_concern(node)`; each line goes when its last caller reads the view (`sim.view(name)`) or sends the command itself."""
from sim.ventures.api import constants


class VenturesForwardsMixin:

	# the numbers the tests still read off the game (sim/ventures/constants.py declares them)
	vars().update({name: value for name, value in vars(constants).items() if name.isupper()})

	# ---- what a concern ties up ----

	# ---- what opening costs and what a concern earns ----

	# ---- opening, selling, rolling out ----
