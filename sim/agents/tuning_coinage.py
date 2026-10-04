"""Provisional numbers behind a state's choice to cut the metal in its coin, each awaiting a derivation."""
from sim.constants import declare

COIN_RESTRIKE_SHARE_PER_YEAR = declare(
	"COIN_RESTRIKE_SHARE_PER_YEAR", 0.1, kind="temporary_heuristic",
	unit="share of the coin stock", source=None, confidence="D",
	why="Share of the coin in use that comes to the mint to be struck again in a year, so the part "
		"of the stock a lighter coin can replace. Stands in for coin wear, tax payment in the old "
		"coin and recoinage orders; the real cost and the inflation come from the economy.")
DEBASEMENT_SHARE_CEILING = declare(
	"DEBASEMENT_SHARE_CEILING", 0.25, kind="temporary_heuristic",
	unit="share of a coin's metal cut in one year", source=None, confidence="D",
	why="The most metal a state cuts from the coin in a year however large its shortfall; beyond it "
		"the cheat is plain to everyone who weighs coin. Stands in for how far a coin is trusted.")
