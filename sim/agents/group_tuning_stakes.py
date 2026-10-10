"""Provisional numbers behind the stakes of church, army, offices and scholars, each awaiting a derivation."""
from sim.constants import declare

OFFICE_FEE_SHARE_OF_REVENUE = declare(
	"OFFICE_FEE_SHARE_OF_REVENUE", 0.05, kind="temporary_heuristic",
	unit="share of the state's revenue", source=None, confidence="D",
	why="What office-holders keep in fees from the revenue that passes through their hands, beside their "
		"salaries. Stands in for a model of how a state pays its officers (fees, farms of taxes, "
		"perquisites).")
LOYALTY_ADJUSTMENT_RATE = declare(
	"LOYALTY_ADJUSTMENT_RATE", 0.5, kind="temporary_heuristic",
	unit="share of the gap closed per year", source=None, confidence="D",
	why="How fast an army's loyalty moves toward the share of its pay it actually gets. Stands in for a "
		"model of what soldiers owe a paymaster and for how long they wait.")
MUTINY_LOYALTY = declare(
	"MUTINY_LOYALTY", 0.6, kind="temporary_heuristic",
	unit="loyalty (0..1)", source=None, confidence="D",
	why="The loyalty below which an army that has gone unpaid acts on the state: soldiers desert and the "
		"rest take their arrears from the treasury. Stands in for a model of collective action among "
		"armed men.")
DESERTION_RATE = declare(
	"DESERTION_RATE", 0.5, kind="temporary_heuristic",
	unit="share of the army a year at zero loyalty", source=None, confidence="D",
	why="The share of its soldiers an army loses a year when its loyalty is gone; less as loyalty nears "
		"the mutiny line.")
