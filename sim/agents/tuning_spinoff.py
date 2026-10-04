"""Provisional numbers behind staff leaving a business to found a rival, each awaiting a derivation."""
from sim.constants import declare

SPINOFF_CHANCE_PER_STAFF_YEAR = declare(
	"SPINOFF_CHANCE_PER_STAFF_YEAR", 1.0e-4, kind="temporary_heuristic",
	unit="chance per person per year the concern has run", source=None, confidence="D",
	why="How likely one of a concern's staff is to leave and found a rival, per person on the staff "
		"and per year it has run. Stands in for a model of staff outside options and know-how.")
SPINOFF_CHANCE_CAP = declare(
	"SPINOFF_CHANCE_CAP", 0.2, kind="temporary_heuristic",
	unit="chance per year", source=None, confidence="D",
	why="Ceiling on the yearly chance that one concern spawns a rival, so a very large old concern "
		"does not spawn one every year.")
SPINOFF_MIN_YEARS = declare(
	"SPINOFF_MIN_YEARS", 3, kind="temporary_heuristic",
	unit="years", source=None, confidence="D",
	why="Years a concern must have run before its staff know it well enough to leave and copy it.")
