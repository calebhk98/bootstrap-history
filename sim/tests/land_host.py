"""The land module over a civilisation and the real base map, for tests that read what the land gives (the held tiles' geometry,
the place a stock stands on)."""
from typing import Any, Dict, Optional

from sim.land.module import Land
from sim.land.state import LandSeat, LandWorld
from sim.tests import module_harness


def build(civilisation: Dict[str, Any], views: Optional[Dict[str, Any]] = None, world: Optional[LandWorld] = None) -> Land:
	plain: Dict[str, Any] = {"civilisation": civilisation, "map_overlays": []}
	plain.update(views or {})
	return module_harness.build(Land, views=plain, world=world if world is not None else LandWorld(), seat=LandSeat())
