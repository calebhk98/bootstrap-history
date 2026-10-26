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


class Resources(Workings, MineCosts, Deposits, Woodland, Remedies, Sinking, MaterialsPhase, Timber, Module):
    def setup(self):
        self._works_effects = None       # (running stamp, effects of the running mining techniques) while what runs is unchanged
        self._modelled_sizes = {}        # resource id -> {deposit id: tonnes} from the older output model
        self._deposit_cache = {}         # deposit rows until the year, the tiles or the deposits found change
