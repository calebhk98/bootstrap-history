"""Provisional numbers behind countries other than the founder's, each awaiting a derivation."""
from sim.constants import declare

COUNTRY_OBSERVATION_RANGE_KM = declare(
	"COUNTRY_OBSERVATION_RANGE_KM", 1500.0, kind="temporary_heuristic",
	unit="km", source=None, confidence="D",
	why="Distance between a country and the founder at which what the founder does is half as "
		"visible there: the fog that makes far countries learn slowly. Stands in for travellers, "
		"trade routes and diplomats carrying news.")
ARMY_SHARE_OF_POPULATION = declare(
	"ARMY_SHARE_OF_POPULATION", 0.003, kind="temporary_heuristic",
	unit="share of a country's people", source=None, confidence="D",
	why="Soldiers a foreign state keeps when its civilisation declares no standing army. Stands in "
		"for a model of rival states' threats and recruiting.")
