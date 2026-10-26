"""Standing timber: the tiles' felled ledger, cut by the firms that fell wood and regrown a year at a time."""
from typing import Any, Dict

import sim.geography.api as geography

from .channels import TIMBER
from .commands import FellTimber, RegrowTimber


class Timber:
    """Needs: legacy_world_map."""

    def timber_felled(self) -> Dict[str, float]:
        """{tile: tonnes of standing timber felled below the tile's full stock}; a missing tile is untouched."""
        return self.world.forest_felled

    def fell_timber(self, command: FellTimber) -> None:
        felled = self.world.forest_felled
        world_map = self.needs.legacy_world_map()
        for tile, tonnes in command.cuts:
            felled = geography.fell_timber(felled, tile, tonnes, world_map)
        self.world.forest_felled = felled
        self.bump(TIMBER)

    def regrow_timber(self, command: RegrowTimber) -> None:
        if self.world.forest_felled:
            self.world.forest_felled = geography.regrow_timber(self.world.forest_felled, self.needs.legacy_world_map())
            self.bump(TIMBER)
