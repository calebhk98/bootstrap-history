"""Provisional numbers behind strata, each awaiting a derivation."""
from sim.constants import declare

STRATUM_WORKING_SHARE = declare(
	"STRATUM_WORKING_SHARE", 0.4, kind="temporary_heuristic",
	unit="share of a stratum's members earning a wage", source=None, confidence="D",
	why="Working-age members in paid work; stands in for the age structure and household "
		"labour supply of the body of people (the demography package holds the real structure).")
STRATUM_OTHER_NEED_FOOD_MULTIPLE = declare(
	"STRATUM_OTHER_NEED_FOOD_MULTIPLE", 0.5, kind="temporary_heuristic",
	unit="food baskets per person-year", source=None, confidence="D",
	why="What the third tier of needs (goods beyond food and housing) costs per head, as a "
		"multiple of the food basket; stands in for the demand system's own budget.")
STRATUM_SAVINGS_BUFFER_YEARS = declare(
	"STRATUM_SAVINGS_BUFFER_YEARS", 0.25, kind="temporary_heuristic",
	unit="years of food and housing", source=None, confidence="D",
	why="Savings a stratum keeps before it spends on goods beyond food and housing or on "
		"schooling; stands in for precautionary saving.")
STRATUM_EDUCATION_SHARE = declare(
	"STRATUM_EDUCATION_SHARE", 0.2, kind="temporary_heuristic",
	unit="share of the surplus over needs", source=None, confidence="D",
	why="Part of what a stratum has left after its needs that it spends on schooling its "
		"children; stands in for a model of what education costs and returns.")
LITERACY_CEILING = declare(
	"LITERACY_CEILING", 0.95, kind="temporary_heuristic",
	unit="share of members", source=None, confidence="D",
	why="The literate share no amount of schooling lifts a stratum above.")
LITERACY_GAIN_RATE = declare(
	"LITERACY_GAIN_RATE", 0.05, kind="temporary_heuristic",
	unit="share of the gap to the ceiling per year at full funding", source=None, confidence="D",
	why="How fast funded schooling raises literacy; the lag stands in for a generation of children.")
LITERACY_DECAY_RATE = declare(
	"LITERACY_DECAY_RATE", 0.02, kind="temporary_heuristic",
	unit="share of literate members lost per year when unfunded", source=None, confidence="D",
	why="How fast literacy fades when nobody is taught; slower than it is gained.")
EDUCATION_EFFORT_SCALE = declare(
	"EDUCATION_EFFORT_SCALE", 0.1, kind="temporary_heuristic",
	unit="food baskets per person-year", source=None, confidence="D",
	why="Schooling spend per head at which funding counts as about six tenths; stands in for "
		"the cost of teachers and time.")
BIRTH_RATE = declare(
	"BIRTH_RATE", 0.036, kind="temporary_heuristic",
	unit="births per member per year at the subsistence welfare ratio", source=None, confidence="D",
	why="Births at a welfare ratio of one; stands in for the demography package's fertility.")
DEATH_RATE = declare(
	"DEATH_RATE", 0.034, kind="temporary_heuristic",
	unit="deaths per member per year with food met", source=None, confidence="D",
	why="Deaths when food is met; stands in for the demography package's mortality.")
BIRTH_WELFARE_RESPONSE = declare(
	"BIRTH_WELFARE_RESPONSE", 0.3, kind="temporary_heuristic",
	unit="share of the birth rate", source=None, confidence="D",
	why="How far births rise above (and fall below) the base as welfare moves away from one; "
		"bounded and gentle, as a Malthusian positive check is.")
FAMINE_DEATH_RATE = declare(
	"FAMINE_DEATH_RATE", 0.25, kind="temporary_heuristic",
	unit="extra deaths per member per year at a total food shortfall", source=None, confidence="D",
	why="Deaths rise steeply with the unmet share of food; stands in for a model of "
		"malnutrition and disease.")
GROWTH_LAG_SHARE = declare(
	"GROWTH_LAG_SHARE", 0.5, kind="temporary_heuristic",
	unit="share of the gap to the target growth closed per year", source=None, confidence="D",
	why="Population growth responds to welfare with a lag.")
BONDED_BIRTH_SHARE = declare(
	"BONDED_BIRTH_SHARE", 0.3, kind="temporary_heuristic",
	unit="share of the ordinary birth rate", source=None, confidence="D",
	why="Bonded members raise few children of their own; stands in for family separation "
		"and the keeper's control of births.")
MOBILITY_RATE = declare(
	"MOBILITY_RATE", 0.02, kind="temporary_heuristic",
	unit="share of members per year at full pressure", source=None, confidence="D",
	why="The most of a stratum that changes stratum in a year; stands in for the churn of "
		"careers, marriages and fortunes.")
BONDAGE_EXIT_RATE = declare(
	"BONDAGE_EXIT_RATE", 0.005, kind="temporary_heuristic",
	unit="share of bonded members per year at full literacy pressure", source=None, confidence="D",
	why="Release from bondage (manumission, purchase of freedom); depends on literacy only, "
		"since a keeper's ration is the bonded member's whole welfare.")
RISE_WELFARE = declare(
	"RISE_WELFARE", 2.0, kind="temporary_heuristic",
	unit="welfare ratio", source=None, confidence="D",
	why="Welfare ratio at which half of the pressure to rise is felt.")
FALL_WELFARE = declare(
	"FALL_WELFARE", 0.8, kind="temporary_heuristic",
	unit="welfare ratio", source=None, confidence="D",
	why="Welfare ratio below which half of the pressure to fall is felt.")
WELFARE_WIDTH = declare(
	"WELFARE_WIDTH", 0.3, kind="temporary_heuristic",
	unit="welfare ratio", source=None, confidence="D",
	why="Softness of the welfare thresholds, so mobility changes smoothly, never at a cliff.")
RISE_LITERACY = declare(
	"RISE_LITERACY", 0.3, kind="temporary_heuristic",
	unit="share of members", source=None, confidence="D",
	why="Literacy at which half of the pressure to rise is felt.")
LITERACY_WIDTH = declare(
	"LITERACY_WIDTH", 0.1, kind="temporary_heuristic",
	unit="share of members", source=None, confidence="D",
	why="Softness of the literacy threshold.")

# ---- the default split of a country into strata when its profile declares none
DEFAULT_RICH_SHARE = declare(
	"DEFAULT_RICH_SHARE", 0.01, kind="temporary_heuristic",
	unit="share of population", source=None, confidence="D",
	why="People living on rents and profits when a profile states no strata.")
DEFAULT_RICH_PROPERTY_SHARE = declare(
	"DEFAULT_RICH_PROPERTY_SHARE", 0.3, kind="temporary_heuristic",
	unit="share of society output", source=None, confidence="D",
	why="What the propertied receive when a profile states no strata.")
DEFAULT_MERCHANT_SHARE_OF_URBAN = declare(
	"DEFAULT_MERCHANT_SHARE_OF_URBAN", 0.1, kind="temporary_heuristic",
	unit="share of the urban population", source=None, confidence="D",
	why="Urban people in trade and finance when a profile states no strata.")
DEFAULT_ARTISAN_SHARE_OF_URBAN = declare(
	"DEFAULT_ARTISAN_SHARE_OF_URBAN", 0.5, kind="temporary_heuristic",
	unit="share of the urban population", source=None, confidence="D",
	why="Urban people in skilled crafts when a profile states no strata.")
DEFAULT_POOR_SHARE = declare(
	"DEFAULT_POOR_SHARE", 0.1, kind="temporary_heuristic",
	unit="share of population", source=None, confidence="D",
	why="People without steady work when a profile states no strata.")
DEFAULT_POOR_WORK_SHARE = declare(
	"DEFAULT_POOR_WORK_SHARE", 0.2, kind="temporary_heuristic",
	unit="share of members earning a wage", source=None, confidence="D",
	why="Work the poor find; less than the working share of the rest.")
DEFAULT_BONDED_SHARE = declare(
	"DEFAULT_BONDED_SHARE", 0.1, kind="temporary_heuristic",
	unit="share of population", source=None, confidence="D",
	why="People in bondage when a profile states that debt bondage exists and no strata.")

HOUSING_FLOOR_AREA_PER_PERSON_M2 = declare(
	"HOUSING_FLOOR_AREA_PER_PERSON_M2", 10.0, kind="temporary_heuristic",
	unit="m2 of dwelling per person", source=None, confidence="D",
	why="Floor space one person lives in, which with the masonry labour per square metre prices a "
		"body of people's housing. Stands in for a dwelling stock with rents set by the market.")
