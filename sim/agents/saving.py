"""What households put aside from income above subsistence."""
from sim.constants import declare

SAVING_SHARE_OF_SURPLUS = declare(
	"SAVING_SHARE_OF_SURPLUS", 0.2, kind="temporary_heuristic",
	unit="share of income above subsistence", source=None, confidence="D",
	why="What households put aside rather than consume from the income they have above what keeps them "
		"fed. Stands in for a saving model with time preference, bequest and risk.")
