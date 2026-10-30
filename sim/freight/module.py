"""The freight module: carriage of goods at home and abroad. It prices the carriers, finds the cheapest route over the
map's tiles for a partner's goods and for a hauled material, works out what merchants add to a foreign route, and settles
the tolls and port dues of a haul. It owns no saved state; what it remembers between calls is rebuilt on demand."""
from sim.assembly.api import Module

from .dues import Dues
from .haul import Haul
from .models import Models
from .routes import Routes
from .traders import Traders


class Freight(Dues, Traders, Haul, Routes, Models, Module):
    def setup(self):
        self._models_cache = None        # (price table, key, models) while the table, the sea crew's wage and the map hold
        self._haul_routes = {}           # hauled material's route by everything it was priced from
        self._carriage_cache = {}        # the year's route cost between two tiles
