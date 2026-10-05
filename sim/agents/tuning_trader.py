"""Provisional numbers behind a trader's decisions, each awaiting a derivation."""
from sim.constants import declare

TRADER_DEPTH_SHARE = declare(
	"TRADER_DEPTH_SHARE", 0.3, kind="temporary_heuristic",
	unit="share of a place's yearly buying of a good", source=None, confidence="D",
	why="The most of what buyers at a destination take in a year that traders on one route together "
		"carry there, so chasers of one price gap do not overshoot it. Stands in for the price the "
		"extra supply would push down; used only where the destination's market does not answer "
		"(price_after_cargo), which today is the home society's.")
TRADER_RISK_SHARE = declare(
	"TRADER_RISK_SHARE", 0.02, kind="temporary_heuristic",
	unit="share of cargo value lost to spoilage, theft and wreck per voyage", source=None, confidence="D",
	why="What a trader counts against a cargo for what the road and the sea take. Stands in for a "
		"model of route hazard and insurance.")
TRADER_FOUNDINGS_PER_YEAR = declare(
	"TRADER_FOUNDINGS_PER_YEAR", 2, kind="temporary_heuristic",
	unit="traders founded per year", source=None, confidence="D",
	why="The most merchants who enter in a year however many routes pay; keeps the population "
		"bounded. Stands in for the pace at which people learn of a gap and find the capital.")
