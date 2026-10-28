"""One-line forwarders from the old `Sim` methods of literacy, diffusion and disclosure to the diffusion module.

The screens, the labour market, the hazards and the agents' port still say `sim.literacy(field)` or
`sim.civ_diffusion(node)`; each line goes when its last caller reads the view or sends the command itself."""
from sim.diffusion.api import constants

from sim.polity.api import value_weight


class DiffusionForwardsMixin:

    # numbers other topics' code still reads off the game (sim/diffusion/constants.py and value_weight.py declare them)
    STATE_MIL_RELIEF_PER_WEAPON_OUTPUT = constants.STATE_MIL_RELIEF_PER_WEAPON_OUTPUT
    STATE_MIL_RELIEF_PER_WEAPON_SACK = constants.STATE_MIL_RELIEF_PER_WEAPON_SACK
    VALUE_WEIGHT_FLOOR = value_weight.VALUE_WEIGHT_FLOOR
    VALUE_WEIGHT_CEILING = value_weight.VALUE_WEIGHT_CEILING

    # ---- literacy ----

    # ---- staff advice ----

    # ---- diffusion ----

    # ---- disclosure ----

    # ---- which techniques concerns have had time to copy ----
