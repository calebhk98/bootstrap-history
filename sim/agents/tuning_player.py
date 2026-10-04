"""Provisional numbers behind a player's turn, each awaiting a derivation."""
from sim.constants import declare

PLAYER_JOURNAL_LIMIT = declare(
	"PLAYER_JOURNAL_LIMIT", 50, kind="temporary_heuristic",
	unit="journal entries kept", source=None, confidence="D",
	why="How many of a player's most recent command results its record keeps; bounds the save. "
		"Stands in for a proper event log outside the record.")
PLAYER_VISIBLE_EXPOSURE = declare(
	"PLAYER_VISIBLE_EXPOSURE", 0.5, kind="temporary_heuristic",
	unit="share of full visibility", source=None, confidence="D",
	why="How visible a player's profitable concern must be to others, when it is not in public use, "
		"for competitors to count it as proven and enter after it.")
