"""The household income scale the market's demand ratios are measured from."""
from sim.constants import declare

MEAN_INCOME_HOURS_PER_CAPITA = declare(
	"MEAN_INCOME_HOURS_PER_CAPITA", 550.0, kind="temporary_heuristic",
	unit="labour-hours/person/year at the opening economy", source=None,
	confidence="D",
	why="Household income scale at the opening; income then moves with the "
	    "wage the labour market pays (household_income_hours_per_capita). Returns to land and capital "
	    "are not yet in it.")
