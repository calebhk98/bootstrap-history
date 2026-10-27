"""The commands and figures a mods directory gives a game, without building a whole game: the interface module of an assembly
over that directory (its data views read the directory, and run the mods' allowed code)."""
import functools
import os
from unittest import mock

from sim.engine import bridge_land, game_assembly


def declared_for(mods_dir):
    """The interface module's `Declared` for the game over `mods_dir`; a clash or a bad reference raises here."""
    with mock.patch.object(bridge_land, "MODS_DIR", str(mods_dir)):
        return game_assembly.build(str(mods_dir), True).views["interface_declared"]()


@functools.lru_cache(maxsize=None)
def shipped_declared():
    """The commands and figures of a game over the repository's own mods (data only: none ships code)."""
    return declared_for(bridge_land.MODS_DIR)
