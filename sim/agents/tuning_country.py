"""Provisional numbers behind countries other than the founder's, each awaiting a derivation."""
from sim.constants import declare

COUNTRY_OBSERVATION_RANGE_KM = declare(
	"COUNTRY_OBSERVATION_RANGE_KM", 1500.0, kind="temporary_heuristic",
	unit="km", source=None, confidence="D",
	why="Distance between a country and the founder at which what the founder does is half as "
		"visible there: the fog that makes far countries learn slowly. Stands in for travellers, "
		"trade routes and diplomats carrying news.")
EARNER_SHARE_OF_POPULATION = declare(
	"EARNER_SHARE_OF_POPULATION", 0.3, kind="temporary_heuristic",
	unit="share of a country's people", source=None, confidence="D",
	why="People whose labour income a foreign state can tax, as a share of its population, each "
		"earning the going labourer's pay. Stands in for a demographic and household model of "
		"countries the simulation does not run actor by actor.")
ARMY_SHARE_OF_POPULATION = declare(
	"ARMY_SHARE_OF_POPULATION", 0.003, kind="temporary_heuristic",
	unit="share of a country's people", source=None, confidence="D",
	why="Soldiers a foreign state keeps when its civilisation declares no standing army. Stands in "
		"for a model of rival states' threats and recruiting.")
RESERVE_YEARS_OF_NEED = declare(
	"RESERVE_YEARS_OF_NEED", 2.0, kind="temporary_heuristic",
	unit="years of the standing need", source=None, confidence="D",
	why="Money a foreign state keeps back before it spends on copying know-how. Stands in for a "
		"reserve policy.")
