"""The numbers the ventures module declares."""
from sim.constants import declare

VENTURE_CAPEX_SHARE_OF_BUILD_COST = declare(
	"VENTURE_CAPEX_SHARE_OF_BUILD_COST", 0.15, kind="temporary_heuristic",
	unit="fraction of project_cost", source=None, confidence="D",
	why="What opening a completed venture's doors costs relative to "
	    "what building it cost - stock, premises, the first year's "
	    "materials. Tuned so opening is a real but secondary "
	    "commitment next to the research itself; not derived from any "
	    "real ratio of working capital to fixed investment.")
VENTURE_CAPEX_MIN_UPKEEP_YEARS = declare(
	"VENTURE_CAPEX_MIN_UPKEEP_YEARS", 1.0, kind="temporary_heuristic",
	unit="years of upkeep", source=None, confidence="D",
	why="A floor under venture_capex so a thing which is cheap to "
	    "invent and expensive to run cannot be opened for nothing: it "
	    "always costs at least one year of its own running upkeep. "
	    "Tuned floor, not measured.")
VENTURE_SUPERVISION = declare(
	"VENTURE_SUPERVISION", 0.25, kind="temporary_heuristic",
	unit="fraction of the build crew", source=None, confidence="D",
	why="What fraction of a concern's BUILD crew (sch/art) its own "
	    "staff must go on owing it in supervision once it is running, "
	    "rather than the whole crew - charging the whole crew every "
	    "year billed the same hands twice and measurably hurt Rome's "
	    "own outcomes (see this constant's own comment). Tuned to "
	    "avoid double-billing, not measured from any real supervisory "
	    "ratio.")
VENTURE_HANDS_PER_REVENUE_LABOUR_HOURS = declare(
	"VENTURE_HANDS_PER_REVENUE_LABOUR_HOURS", 30000.0, kind="temporary_heuristic",
	unit="labour hours per year of revenue per pair of hands", source=None,
	confidence="D",
	why="A floor under venture_supervision's own build-crew share: "
	    "even a concern that took nobody to build (a bottling shed, a "
	    "chaff cutter - 19% of concerns, per this constant's own "
	    "comment) still needs somebody watching it once it earns "
	    "real money, at one pair of hands per this many denarii of "
	    "takings. Tuned so a fleet of loss-free, zero-build concerns "
	    "cannot run itself for nothing (see the Han break-test this "
	    "constant's own comment describes); not a measured "
	    "supervisor-to-revenue ratio for any real enterprise.")
VENTURE_FOREMAN_SHARE = declare(
	"VENTURE_FOREMAN_SHARE", 0.25, kind="temporary_heuristic",
	unit="FTE per concern supervised", source=None, confidence="D",
	why="How much of a skilled specialist's time supervising one "
	    "concern that needs their trade ties up - one specialist can "
	    "oversee at most four ordinary concerns of that kind. Tuned "
	    "game balance, not a measured foreman-to-shop ratio.")
