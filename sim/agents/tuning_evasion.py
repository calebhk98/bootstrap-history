"""Provisional numbers behind how taxpayers hide income from a form, each awaiting a derivation."""
from sim.constants import declare

_RETIRE = "Complaints/657: what can be hidden and what hiding costs come from the payers' holdings (which income is in kind, in coin, on the road) and from the officials' records"

HIDEABLE_SHARE_OF_INCOME = declare(
	"HIDEABLE_SHARE_OF_INCOME", 0.5, kind="temporary_heuristic", unit="share of a payer's income", source=None,
	confidence="D", retire=_RETIRE,
	why="The most of its income a payer can keep out of the state's rolls however it tries (wages and rents in plain view "
		"cannot be). No source found for a pre-modern state; stands in for a model of which income is visible.")
HIDING_MARGINAL_COST_AT_CEILING = declare(
	"HIDING_MARGINAL_COST_AT_CEILING", 0.5, kind="temporary_heuristic", unit="share of the income hidden, for the last unit hidden",
	source=None, confidence="D", retire=_RETIRE,
	why="What hiding the last unit of income costs (go-betweens, goods held out of the market, false books) when a payer "
		"already hides all it can; the cost of each unit before it rises in proportion to the share already hidden. "
		"No source found; stands in for a model of the price of secrecy.")
