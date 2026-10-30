"""The campaigns module: armies and their orders, the year's campaign phase, conquest and captives, and the year's revolts.

The armies of every actor that owns tiles are records in the module's state. An army marches on its order, eats from what it
carries and the land, wears down, and where it stands on another actor's tile it besieges and storms it; a tile won is held at
the level the control data names. Captives of a battle or a conquest join the winner's bonded people. Each state's grievances,
hunger and liability burden become unrest on its tiles, and where the armed discontented would beat the garrison they rise."""
from sim.assembly.api import Module

from .armies import Armies
from .campaign_year import CampaignYear
from .captives import Captives
from .contest import Contest
from .stability import Stability


class Campaigns(Armies, CampaignYear, Contest, Captives, Stability, Module):
	pass
