"""One-line forwarders from the old `Sim` names of polity to the polity module, for callers not yet in a module.

The screens, the agents' world, the project completion and the mods still say `sim.state_reach()` or `sim.reputation`; each line
goes when its last caller reads the view or sends the command itself."""
from sim.polity.api import constants
from . import money_units


class PolityForwardsMixin:

    # numbers other topics' code, the screens and the tests still read off the game (sim/polity/constants.py declares them)
    vars().update({name: value for name, value in vars(constants).items() if name.isupper()})
    STATE_FUNDING_BASE = money_units.PricedInLabourHours("STATE_FUNDING_BASE_LABOUR_HOURS")
    # ---- the seat's figures ----

    # ---- what the state notices and asks ----

    # ---- how far the state reaches ----

    # ---- the groups, the transfers and the patron's funding ----
