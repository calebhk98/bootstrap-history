"""The resources module: the seat's mines and the deposits they name, prospecting, coppice woodland and nitre beds, and the
standing timber firms fell."""
from sim.assembly.api import Module

from .costs import MineCosts
from .deposits import Deposits
from .materials_phase import MaterialsPhase
from .remedies import Remedies
from .sinking import Sinking
from .timber import Timber
from .woodland import Woodland
from .workings import Workings


class Resources(Module):

    PARTS = {
        "workings": Workings,
        "mine_costs": MineCosts,
        "deposits": Deposits,
        "woodland": Woodland,
        "remedies": Remedies,
        "sinking": Sinking,
        "materials_phase": MaterialsPhase,
        "timber": Timber,
    }
