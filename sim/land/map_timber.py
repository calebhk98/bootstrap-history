"""What the land module answers about the forest on the map: the wood a tile grows and has standing, and the felled ledger after
cuts and a year's regrowth. Mixed into `Land`."""
from typing import Any, Dict, Iterable, Mapping, Optional, Tuple

from sim.geography.api import (fell_timber, regrow_timber, standing_timber_tonnes, timber_haul_km,
                               timber_mean_increment_tonnes_per_hectare_year)


class MapTimber:
    """Mixed into `Land`."""

    world_map: Any

    def forest_increment(self, tiles: Iterable[str]) -> float:
        """Air-dry stem wood a year per hectare over these tiles' forest, weighted by forest area; 0 with no forest."""
        return timber_mean_increment_tonnes_per_hectare_year(tiles, self.world_map)

    def felled_after_cuts(self, felled: Mapping[str, float], cuts: Iterable[Tuple[str, float]]) -> Dict[str, float]:
        """The felled ledger ({tile: tonnes felled}) after each cut ((tile, tonnes), in order) comes off its tile."""
        for tile, tonnes in cuts:
            felled = fell_timber(felled, tile, tonnes, self.world_map)
        return dict(felled)

    def felled_after_regrowth(self, felled: Mapping[str, float]) -> Dict[str, float]:
        """The felled ledger a year on: every tile regrows at its increment until whole."""
        return regrow_timber(felled, self.world_map)

    def timber_on_tile(self, felled: Mapping[str, float], tile: str) -> Dict[str, Optional[float]]:
        """{standing_tonnes: wood standing on the tile, haul_km: km from the settlement to the nearest standing wood (None
        where none stands)}, once `felled` has been cut."""
        standing = standing_timber_tonnes(felled, tile, self.world_map)
        return {"standing_tonnes": standing, "haul_km": timber_haul_km(felled, tile, self.world_map) if standing > 0.0 else None}
