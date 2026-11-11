"""Provisional numbers behind how taxpayers hide income from a form, each awaiting a derivation."""
from sim.constants import declare

_RETIRE = "Complaint 657: what can be hidden and what hiding costs come from the payers' holdings (which income is in kind, in coin, on the road) and from the officials' records"

HIDEABLE_SHARE_OF_INCOME = declare(
	"HIDEABLE_SHARE_OF_INCOME", 0.5, kind="temporary_heuristic", unit="share of a payer's income", source=None,
	confidence="D", retire=_RETIRE,
	why="The most of its income a payer can keep out of the state's rolls however it tries (wages and rents in plain view "
		"cannot be). No source found for a pre-modern state; stands in for a model of which income is visible. The one figure "
		"opened: Arslan 2022 (Medeniyet Belleten 2/3, p. 21) finds 95 adult men living in Uskudar in 1559-1561 court records absent "
		"from the 1560 tahrir, 14 per cent of the 676 registered, a lower bound on persons off the rolls (about 20 were exempt, so "
		"about 11 per cent taxable); it is not an income share and does not bound the ceiling.")
HIDING_MARGINAL_COST_AT_CEILING = declare(
	"HIDING_MARGINAL_COST_AT_CEILING", 0.5, kind="temporary_heuristic", unit="share of the income hidden, for the last unit hidden",
	source=None, confidence="D", retire=_RETIRE,
	why="What hiding the last unit of income costs (go-betweens, goods held out of the market, false books) when a payer "
		"already hides all it can; the cost of each unit before it rises in proportion to the share already hidden. "
		"No source found; stands in for a model of the price of secrecy. With a penalty in proportion to the tax unpaid the "
		"rate has no effect on hiding except through this curve (Yitzhaki 1974; evasion.py), so it also sets the "
		"size of the whole rate response.")
