"""The numbers the production module declares: the revenue ceiling, the workshop and capability factors, institution upkeep
and size, and how fast an industry becomes established. Each is a labelled heuristic to retire."""
from sim.constants import declare

REVENUE_CEILING_LABOUR_HOURS_PER_POP_SCALE = declare(
    "REVENUE_CEILING_LABOUR_HOURS_PER_POP_SCALE", 18100000.0, kind="temporary_heuristic",
    unit="labour hours/year at pop_scale=1, output_per_head=1", source=None,
    confidence="D",
    retire="Complaint 514",
    why="Amount of labour, not of coin. The saturating ceiling on what the engine's estimate of a founder's "
        "concerns may add up to against one civilisation's market. Concerns whose goods the economy trades are "
        "paid by the clearing and no longer pass through it; it still bounds the concerns nobody clears "
        "(services, institutions, workshop output). Measured not to bind in an ordinary run (Complaint 514). "
        "It is kept because the money screen's market deduction (Complaint 216) is read from it; retire both "
        "when those concerns are paid from a clearing or a stated demand.")

SLAVE_LABOUR_PRODUCTIVITY_SHARE = declare(
    "SLAVE_LABOUR_PRODUCTIVITY_SHARE", 0.7, kind="temporary_heuristic",
    unit="fraction of a free worker's output credited per enslaved worker",
    source=None, confidence="D",
    why="How much of a free craft worker's output one enslaved worker "
        "in the household is credited with producing, reused for both "
        "headcount and wage-bill purposes. A real figure needs actual "
        "evidence on relative productivity under coercion versus free "
        "labour for the specific tasks involved, which varied hugely "
        "by trade and is not modelled here; 0.7 is a plausible-feeling "
        "discount, not a measurement.")

WORKSHOP_WAGE_MARKUP_BASE = declare(
    "WORKSHOP_WAGE_MARKUP_BASE", 1.55, kind="temporary_heuristic",
    unit="output denarii per denarius of craft wages", source=None,
    confidence="D",
    why="How much a workshop's output is worth relative to what it "
        "pays its craft staff - deliberately more than a bare 1x wage "
        "pass-through (a workshop has to sell its output for more than "
        "labour cost alone or it could never cover materials, rent or "
        "profit) and, per the comment above, deliberately less than a "
        "2x markup. Chosen to make the mechanism function at all, not "
        "measured against any real workshop's margins.")

CAPABILITY_FACTOR_CEILING_BONUS = declare(
    "CAPABILITY_FACTOR_CEILING_BONUS", 2.0, kind="temporary_heuristic",
    unit="dimensionless multiple on workshop output (asymptote)",
    source=None, confidence="D",
    why="The most that accumulated, unused method can ever multiply a "
        "workshop's output by, as the weighted total saturates. A "
        "tripling-or-more from pure technique with no new workshop or "
        "worker would be implausible; 2x (a doubling) is a tuned "
        "ceiling, not derived from any output-per-technology "
        "measurement.")

CAPABILITY_FACTOR_HALF_SATURATION_REV_LABOUR_HOURS = declare(
    "CAPABILITY_FACTOR_HALF_SATURATION_REV_LABOUR_HOURS", 806000.0,
    kind="temporary_heuristic", unit="labour hours of tier-weighted revenue at half of CAPABILITY_FACTOR_CEILING_BONUS", source=None,
    confidence="D",
    why="Amount of labour, not of coin: it was a book-denarii figure and now follows what labour costs. "
        "How much accumulated tier-weighted method it takes to reach "
        "half the maximum capability bonus - the saturating curve's "
        "own scale. Tuned against playtests (see the comment this "
        "replaces: '40,000 of tier-weighted method roughly doubles "
        "what a workshop makes'), not fitted to any measured "
        "productivity data.")

INSTITUTION_FLOOR = declare(
    "INSTITUTION_FLOOR", 0.20, kind="temporary_heuristic",
    unit="fraction of full upkeep charged with zero enrolment",
    source=None, confidence="D",
    why="What a school costs on the day you found it, as a share of "
        "what it costs once it is full: the building, the lease, and "
        "one teacher, before any scholars arrive. A real figure needs "
        "an itemised fixed-versus-variable cost breakdown for each "
        "capability institution (building/lease/core staff versus "
        "per-head cost), which this file does not have; 20% is a "
        "round, plausible fixed share, not derived from one.")

INSTITUTION_PLACES_FALLBACK_UPKEEP_LABOUR_HOURS_PER_HEAD = declare(
    "INSTITUTION_PLACES_FALLBACK_UPKEEP_LABOUR_HOURS_PER_HEAD", 250.0,
    kind="temporary_heuristic", unit="labour hours of upkeep per head",
    source=None, confidence="D",
    why="For an institution not in INSTITUTION_PLACES, how many "
        "denarii of upkeep one person's worth of capacity is assumed "
        "to cost, so an arbitrary institution still scales with "
        "headcount instead of defaulting to zero places. 'About a "
        "wage a head' per the comment this replaces - the right ORDER "
        "of magnitude for a building whose cost is its people, not a "
        "specific attested wage.")

YEARS_STAFF_TAKE_TO_MASTER = declare(
    "YEARS_STAFF_TAKE_TO_MASTER", 5.0, kind="temporary_heuristic",
    unit="years of a founding-size concern's whole staff", source=None, confidence="D",
    why="Experience equal to this many years of one founding-size concern's staff makes depth one half. "
        "Skill with a new technique is learned on the job over years (Bessen 2003, Lowell weaving), and the "
        "figure scales with the concern's own staff so it is not a per-technology value; the years are a "
        "round guess, not a measurement.")

RAMP_SHARE_AT_FULL_DEPTH = declare(
    "RAMP_SHARE_AT_FULL_DEPTH", 0.34, kind="temporary_heuristic",
    unit="share of the configured ramp years left", source=None, confidence="D",
    why="A concern opened where the technique is fully established still has to find its custom, so its ramp "
        "never vanishes; a third of the first-of-its-kind ramp is a guess at the customer-finding part.")

RISK_SHARE_AT_FULL_DEPTH = declare(
    "RISK_SHARE_AT_FULL_DEPTH", 0.5, kind="temporary_heuristic",
    unit="share of the bare node risk left", source="Levitt, List and Syverson 2013, NBER w18017",
    confidence="D",
    why="Defects halve for each tenfold of cumulative output in the car plant they studied; taken as the "
        "most that running a technique everywhere can take off a node's risk. A diagnosed failed attempt "
        "adds to the same stock, so failing and being established are one lesson.")

LITERACY_GENERAL_FLOOR = declare(
    "LITERACY_GENERAL_FLOOR", 0.02, kind="temporary_heuristic",
    unit="fraction of population", source=None, confidence="D",
    why="The lowest literacy_general this ceiling will ever divide by, "
        "so a society with almost nobody literate still gets a real "
        "(tiny, not undefined or infinite) school-expansion ceiling "
        "rather than a division that blows up. Tuned floor, not a "
        "measured minimum literacy for any real society.")

INSTITUTION_CEILING_POP_EXPONENT = declare(
    "INSTITUTION_CEILING_POP_EXPONENT", 0.5, kind="temporary_heuristic",
    unit="dimensionless exponent", source=None, confidence="D",
    why="Sub-linear (square-root) growth of how many units of an "
        "institution the population/literacy base can fill, matching "
        "this file's other diminishing-returns curves. Reused for "
        "both the population term and the literacy-ratio term on "
        "schools/academies. Tuned shape, not fitted.")

SCHOOL_CEILING_BASE_UNITS = declare(
    "SCHOOL_CEILING_BASE_UNITS", 6.0, kind="temporary_heuristic",
    unit="units, at pop_scale=1.0 and reference literacy",
    source=None, confidence="D",
    why="How many units of a school or academy network a full-size, "
        "reference-literacy civilisation can fill. Tuned game "
        "balance, not measured against any real schooling capacity.")

WORKSHOP_CEILING_BASE_UNITS = declare(
    "WORKSHOP_CEILING_BASE_UNITS", 4.0, kind="temporary_heuristic",
    unit="units, at pop_scale=1.0", source=None, confidence="D",
    why="As SCHOOL_CEILING_BASE_UNITS, for institutions bounded by "
        "population and craftsmen rather than literacy (workshops, "
        "collegia, a freedman staff).")

INSTITUTION_EXPANSION_CONVEXITY = declare(
    "INSTITUTION_EXPANSION_CONVEXITY", 0.5, kind="temporary_heuristic",
    unit="dimensionless", source=None, confidence="D",
    why="How much dearer each further unit of a scalable institution "
        "is, past the first: 0.5 means the tenth unit's marginal "
        "founding cost is 5.5 times the first's. The convex SHAPE is a "
        "real claim (a second school draws on the same small literate "
        "pool the first one already drew down); the steepness itself "
        "is tuned to make a founder pursue the population/literacy "
        "ceiling rather than brute-force spending, not fitted to any "
        "real institution's actual expansion cost.")
