"""The land module: who holds each tile, the settled colonies, the ways and works built, and the map and geography of the game.

It owns the owner map, the ways and the works (a world slot) and each seat's colonies (a seat slot), and holds the map and the
`Geography` handle built over the views its spec declares. It answers which technologies the people hold and keep in service."""
from sim.assembly.api import Module

from .colonies import Colonies
from .held import Held
from .map_views import MapViews
from .ownership import Ownership
from .ways import Ways
from .works import Works


class Land(Ownership, Colonies, MapViews, Ways, Works, Held, Module):

    def setup(self) -> None:
        self._caches = {}       # the transfer count, the owner map last seen and the tiles by owner; never saved
        self._tile_facts = {}   # tile -> what it gives an army; static, never saved
        self._map_cache = None
        self._geography_cache = None
