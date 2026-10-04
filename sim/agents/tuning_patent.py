"""Provisional numbers behind patents and company shares, each awaiting a derivation."""
from sim.constants import declare

PATENT_TERM_YEARS = declare(
	"PATENT_TERM_YEARS", 14, kind="temporary_heuristic",
	unit="years", source=None, confidence="D",
	why="How long an exclusive right to an invention lasts once a state that knows the institution "
		"grants it. Stands in for the term a statute would set.")
DIVIDEND_PAYOUT_SHARE = declare(
	"DIVIDEND_PAYOUT_SHARE", 0.5, kind="temporary_heuristic",
	unit="share of last year's margin", source=None, confidence="D",
	why="Share of a company's last margin paid out to its outside shareholders each year. Stands "
		"in for the board's choice between dividends and retained capital.")
