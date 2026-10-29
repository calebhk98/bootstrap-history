"""Standing timber: the tiles' felled ledger, cut by the firms that fell wood and regrown a year at a time."""
from typing import Dict

from .channels import TIMBER
from .commands import FellTimber, RegrowTimber


class Timber:
    """Needs: felled_after_cuts, felled_after_regrowth."""

    def timber_felled(self) -> Dict[str, float]:
        """{tile: tonnes of standing timber felled below the tile's full stock}; a missing tile is untouched."""
        return self.world.forest_felled

    def fell_timber(self, command: FellTimber) -> None:
        self.world.forest_felled = self.needs.felled_after_cuts(self.world.forest_felled, command.cuts)
        self.bump(TIMBER)

    def regrow_timber(self, command: RegrowTimber) -> None:
        if self.world.forest_felled:
            self.world.forest_felled = self.needs.felled_after_regrowth(self.world.forest_felled)
            self.bump(TIMBER)
