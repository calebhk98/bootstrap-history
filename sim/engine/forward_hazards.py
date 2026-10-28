"""One-line forwarders from the old `Sim` names of hazards to the hazards module, for callers not yet in a module.

The screens, the fog, the epidemic step and the state's demands still say `sim.hazard_figure(kind, hazard)` or
`sim.lose_capital(fraction)`; each line goes when its last caller reads the view or sends the command itself."""
from sim.hazards.api import constants


class HazardsForwardsMixin:

    # numbers other topics' code and mods still read off the game (sim/hazards/constants.py declares them)
    STAFF_LOSS_HAZARD_ANNUAL_CHANCE = constants.STAFF_LOSS_HAZARD_ANNUAL_CHANCE
    PLAGUE_CASH_LOSS_SHARE = constants.PLAGUE_CASH_LOSS_SHARE
    SACK_TAKE_STRENGTH = constants.SACK_TAKE_STRENGTH
    REAL_EROSION_CASH_LOSS_SHARE = constants.REAL_EROSION_CASH_LOSS_SHARE
    FIRE_ANNUAL_CHANCE = constants.FIRE_ANNUAL_CHANCE
    FIRE_CAPITAL_LOSS = constants.FIRE_CAPITAL_LOSS
    BANDITRY_ANNUAL_CHANCE = constants.BANDITRY_ANNUAL_CHANCE
    BANDITRY_TAKE_STRENGTH = constants.BANDITRY_TAKE_STRENGTH
    HAZARD_EROSION_OWN_GOLD = constants.HAZARD_EROSION_OWN_GOLD
    HAZARD_EROSION_OWN_SILVER = constants.HAZARD_EROSION_OWN_SILVER

    # ---- the figures ----

    # ---- the world ----

    # ---- what a hazard does to the acting seat ----
