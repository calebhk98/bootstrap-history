"""The diffusion module: how techniques and knowledge spread through the society and abroad, literacy, disclosure."""
from sim.assembly.api import Module

from .disclosure import Disclosure
from .foreign import Foreign
from .literacy import Literacy
from .relief import Relief
from .society import Society
from .spread import Spread
from .tech_effects import TechEffects
from .techniques import Techniques
from .trades import TradeAbsorption


class Diffusion(Module):

    PARTS = {
        "society": Society,
        "techniques": Techniques,
        "disclosure": Disclosure,
        "foreign": Foreign,
        "relief": Relief,
        "spread": Spread,
        "tech_effects": TechEffects,
        "trade_absorption": TradeAbsorption,
        "literacy": Literacy,
    }
