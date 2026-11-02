"""The household income scale the household demand model is measured from."""
from sim.constants import declare

MEAN_INCOME_HOURS_PER_CAPITA = declare(
	"MEAN_INCOME_HOURS_PER_CAPITA", 550.0, kind="temporary_heuristic",
	unit="labour-hours/person/year at the opening economy", source=None,
	confidence="D",
	why="Household income scale at the opening; the "
	    "household model reads it as the mean income.")
