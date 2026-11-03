"""The most any bidder for labour offers per hour, a multiple of the trade's wage last year: the state, its mints and a
seat's standing bid all read this one figure (a leaf both the economy and the markets port import)."""
from sim.constants import declare

WAGE_CEILING_MULTIPLE = declare(
    "WAGE_CEILING_MULTIPLE", 1.5, kind="temporary_heuristic", unit="multiple of last year's wage", source=None, confidence="D",
    retire="Complaints/964: the seat states its own maximum wage",
    why="The most a bidder's standing bid offers per hour, as a multiple of the trade's wage last year, so a wage that rose in "
        "the year does not leave the places empty; the clearing pays the market wage, not the ceiling.")
