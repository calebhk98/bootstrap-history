"""Provisional numbers behind how actors answer the state's demands, each awaiting a derivation."""
from sim.constants import declare

DEMAND_STANDING_DISCOUNT = declare(
	"DEMAND_STANDING_DISCOUNT", 0.55, kind="temporary_heuristic",
	unit="share of enforcement turned aside at full standing", source=None, confidence="D",
	why="How much of a state's reach over a refusal a fully protected actor turns aside; the same "
		"share the requisition rate is bargained down by. Stands in for a model of patronage "
		"and who the state can afford to offend.")
REFUSAL_PENALTY_MULTIPLE = declare(
	"REFUSAL_PENALTY_MULTIPLE", 1.0, kind="temporary_heuristic",
	unit="demands, at full state capacity", source=None, confidence="D",
	why="What an enforced refusal adds to the demand itself, in demands, for a state of full "
		"capacity; scaled down by the capacity. Stands in for fines, seizure of the goods "
		"withheld and the cost of the officers sent to collect.")
