"""The land module: who holds each tile, the settled colonies, the ways and works built, and the map and geography of the game.

It owns the owner map, the ways and the works (a world slot) and each seat's colonies (a seat slot), and holds the map and the
`Geography` handle built over the views its spec declares. It answers which technologies the people hold and keep in service."""
from sim.assembly.api import Module

from .colonies import Colonies
from .held import Held
from .map_carriage import MapCarriage
from .map_deposits import MapDeposits
from .map_places import MapPlaces
from .map_timber import MapTimber
from .map_views import MapViews
from .ownership import Ownership
from .ways import Ways
from .works import Works


class Land(Module):

    PARTS = {
        "ownership": Ownership,
        "colonies": Colonies,
        "map_views": MapViews,
        "map_places": MapPlaces,
        "map_carriage": MapCarriage,
        "map_timber": MapTimber,
        "map_deposits": MapDeposits,
        "ways": Ways,
        "works": Works,
        "held": Held,
    }
