"""Provisional weights a state's own valuation puts on the consequences of each way to meet a shortfall."""
from sim.constants import declare

_RETIRE = "Complaints/625: a ruler's valuation comes from the interest groups that hold it, not from one weight per consequence"

FISCAL_DEBT_CARRY_YEARS = declare(
	"FISCAL_DEBT_CARRY_YEARS", 3.0, kind="temporary_heuristic", unit="years of interest",
	source=None, confidence="D", retire=_RETIRE,
	why="Years a state expects to carry what it borrows or defers, so the interest it counts is that many years of "
		"the rate. Stands in for a repayment plan.")
FISCAL_SERVICE_LOSS_WEIGHT = declare(
	"FISCAL_SERVICE_LOSS_WEIGHT", 1.0, kind="temporary_heuristic", unit="cost per unit of service not paid",
	source=None, confidence="D", retire=_RETIRE,
	why="What a state counts as lost for each unit of a standing line it cuts and never pays.")
FISCAL_LOYALTY_WEIGHT = declare(
	"FISCAL_LOYALTY_WEIGHT", 0.2, kind="temporary_heuristic", unit="cost per share of pay unpaid",
	source=None, confidence="D", retire=_RETIRE,
	why="What a state counts as lost for the share of its army's and officials' pay it leaves unpaid, which "
		"lowers their loyalty.")
FISCAL_PRICE_RISE_WEIGHT = declare(
	"FISCAL_PRICE_RISE_WEIGHT", 0.15, kind="temporary_heuristic", unit="cost per share of coin metal cut",
	source=None, confidence="D", retire=_RETIRE,
	why="What a state counts as lost for each share of its coin's metal it cuts, which raises prices.")
FISCAL_BURDEN_WEIGHT = declare(
	"FISCAL_BURDEN_WEIGHT", 0.1, kind="temporary_heuristic", unit="cost per share of income taken",
	source=None, confidence="D", retire=_RETIRE,
	why="What a state counts as lost for each share of its taxpayers' income it takes more, which wears down "
		"their compliance.")
RATE_RAISE_STEP = declare(
	"RATE_RAISE_STEP", 0.25, kind="temporary_heuristic", unit="share of the present rate",
	source=None, confidence="D", retire=_RETIRE,
	why="The most a state raises the rate of each of its forms collected in coin in one year when it covers a shortfall "
		"that way. The only consequence of a higher rate that exists is the burden the state counts (FISCAL_BURDEN_WEIGHT); "
		"Complaints/627 files the missing ones.")
KIND_DEMAND_RATE_STEP = declare(
	"KIND_DEMAND_RATE_STEP", 0.25, kind="temporary_heuristic", unit="share of the present rate",
	source=None, confidence="D", retire=_RETIRE,
	why="The most a state raises the rate of its forms paid in kind in one year when it demands more in kind.")
