"""The demography module: the nation's people by age, by region and tile, the town share, the food they ate, the yearly step
that feeds and steps them, and each seat's farm holding.

It owns the three age bands, the regions, the food eaten, the town shares and the demographic record (a world slot), and each
seat's farm: land, granary and cleared area (a seat slot). Everything else it needs it reads as a view of its owner, and
everything it changes outside itself it changes by a command."""
from sim.assembly.api import Module

from .counts import Counts
from .farm import Farm
from .recovery import Recovery
from .regions import Regions
from .urban import Urban


class Demography(Module):

    PARTS = {
        "counts": Counts,
        "regions": Regions,
        "urban": Urban,
        "recovery": Recovery,
        "farm": Farm,
    }
