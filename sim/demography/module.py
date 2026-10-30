"""The demography module: the nation's people by age, by region and tile, the town share, the food they ate, the yearly step
that feeds and steps them, and each seat's farm holding the farm year works on.

It owns the three age bands, the regions, the food eaten, the town shares and the demographic record (a world slot), and each
seat's farm: land, granary and the last farm year (a seat slot). Everything else it needs it reads as a view of its owner, and
everything it changes outside itself it changes by a command."""
from sim.assembly.api import Module

from .counts import Counts
from .farm import Farm
from .recovery import Recovery
from .regions import Regions
from .urban import Urban


class Demography(Counts, Regions, Urban, Recovery, Farm, Module):

    def setup(self):
        self._urban_ceilings_cache = {}        # (the year's inputs) -> {tile: people its town can feed}; never saved
        self._last_demographic_step = None     # the nation's flows of the last yearly step, until the next
        self._last_regional_step = None        # the same by region
