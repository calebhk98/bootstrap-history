"""Provisional numbers behind actor decisions, each awaiting a derivation."""
from sim.constants import declare

UNIT_GAIN = declare(
	"UNIT_GAIN", 1.0, kind="temporary_heuristic",
	unit="gain units per trait", source=None, confidence="D",
	why="A trait with no declared magnitude counts as one unit of its "
		"dimension. Replace by per-node declared gains.")
VALUE_HORIZON_YEARS = declare(
	"VALUE_HORIZON_YEARS", 15.0, kind="temporary_heuristic",
	unit="years", source=None, confidence="D",
	why="Years of a concern's margin an entrant counts when deciding "
		"whether entry pays; stands in for a cost-of-capital derivation.")
GOVERNMENT_WORTH_SHARE_PER_GAIN = declare(
	"GOVERNMENT_WORTH_SHARE_PER_GAIN", 2.0e-6, kind="temporary_heuristic",
	unit="share of annual state revenue per weighted gain unit", source=None,
	confidence="D",
	why="What one unit of weighted gain is worth to a state, as a share of "
		"its yearly revenue. Stands in for a model of what armies, roads "
		"and prestige return.")
ADMINISTRATIVE_SPAN = declare(
	"ADMINISTRATIVE_SPAN", 5000.0, kind="temporary_heuristic",
	unit="people governed per official at full state capacity", source=None,
	confidence="D",
	why="How many people one paid official can keep on the rolls and the "
		"assessments; a state with less capacity keeps proportionally fewer "
		"officials. Stands in for a model of what administration is for "
		"(census, assessment, courts, posts).")
LEVY_RATE_CEILING = declare(
	"LEVY_RATE_CEILING", 0.3, kind="temporary_heuristic",
	unit="share of a taxpayer's income", source=None, confidence="D",
	why="The most of one visible taxpayer's income the state can take in a "
		"year however large its shortfall; beyond it taxpayers hide, flee or "
		"stop earning. Stands in for a model of evasion and of what a "
		"taxpayer does when the claim on him is ruinous.")
ARMY_ADJUSTMENT_RATE = declare(
	"ARMY_ADJUSTMENT_RATE", 0.1, kind="temporary_heuristic",
	unit="share of the standing army per year", source=None, confidence="D",
	why="The most a state raises or disbands of its standing army in a "
		"year toward the size it wants and can pay. Stands in for recruiting, "
		"training and demobilisation as processes.")
COPY_EFFORT_SHARE = declare(
	"COPY_EFFORT_SHARE", 0.4, kind="temporary_heuristic",
	unit="share of the original work", source=None, confidence="D",
	why="Work needed to copy a demonstrated invention relative to making "
		"it first; the example removes the search, not the making.")
COPY_TIME_SHARE = declare(
	"COPY_TIME_SHARE", 0.6, kind="temporary_heuristic",
	unit="share of the original calendar floor", source=None, confidence="D",
	why="Calendar time to copy relative to the original build time.")
COPY_RISK_SHARE = declare(
	"COPY_RISK_SHARE", 0.6, kind="temporary_heuristic",
	unit="share of the original failure risk", source=None, confidence="D",
	why="A copier fails less often than the pioneer but not never.")
HIRING_PREMIUM = declare(
	"HIRING_PREMIUM", 0.5, kind="temporary_heuristic",
	unit="extra share of wage", source=None, confidence="D",
	why="Extra cost of hours in a trade the actor does not already staff.")
SECRET_EXPOSURE = declare(
	"SECRET_EXPOSURE", 0.25, kind="temporary_heuristic",
	unit="share of full visibility", source=None, confidence="D",
	why="How much of a finished invention outsiders learn when it is not "
		"in public use.")
OBSERVATION_RANGE_KM = declare(
	"OBSERVATION_RANGE_KM", 800.0, kind="temporary_heuristic",
	unit="km", source=None, confidence="D",
	why="Distance at which what the founder does is half as visible.")
PROOF_YEARS = declare(
	"PROOF_YEARS", 3, kind="temporary_heuristic",
	unit="years", source=None, confidence="D",
	why="Years a concern must run at a profit before outsiders believe it.")
ENTREPRENEURIAL_CAPITAL_SHARE = declare(
	"ENTREPRENEURIAL_CAPITAL_SHARE", 1.0e-4, kind="temporary_heuristic",
	unit="share of annual society output", source=None, confidence="D",
	why="Capital the society can pool for one new entrant; stands in for a "
		"savings and credit model.")
ENTRY_STAKE_BUFFER = declare(
	"ENTRY_STAKE_BUFFER", 1.5, kind="temporary_heuristic",
	unit="multiple of copy cost", source=None, confidence="D",
	why="Working capital an entrant is funded with beyond the copy cost.")
EXIT_LOSS_YEARS = declare(
	"EXIT_LOSS_YEARS", 3, kind="temporary_heuristic",
	unit="years", source=None, confidence="D",
	why="Consecutive loss-making years after which a firm closes.")
ATTENTION_SPAN = declare(
	"ATTENTION_SPAN", 12, kind="temporary_heuristic",
	unit="inventions per actor per year", source=None, confidence="D",
	why="How many of the most promising inventions an actor works out a "
		"copying plan for in a year; stands in for limited attention and "
		"keeps the yearly evaluation bounded.")
EXPANSION_RATE = declare(
	"EXPANSION_RATE", 0.5, kind="temporary_heuristic",
	unit="share of present capacity per year", source=None, confidence="D",
	why="The most capacity a firm adds to a concern in a year, however good the return; stands in for "
		"the time to build plant and to find and train the people.")
MANAGEMENT_SPAN_EXPONENT = declare(
	"MANAGEMENT_SPAN_EXPONENT", 0.15, kind="temporary_heuristic",
	unit="exponent of capacity on the wage bill beyond the people hired", source=None, confidence="D",
	why="Wages of a concern run at several times its founding size grow faster than its staff: the "
		"overseers and managers a larger concern needs. Stands in for a model of span of control.")
