"""Provisional numbers behind exchanges between actors, each awaiting a derivation."""
from sim.constants import declare

OFFER_LIFETIME_YEARS = declare(
	"OFFER_LIFETIME_YEARS", 2, kind="temporary_heuristic",
	unit="years", source=None, confidence="D",
	why="How long an offer stays open to its receiver before it lapses. Stands in for how long "
		"a counterparty's terms hold when prices, harvests and rivals move.")
