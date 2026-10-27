"""The numbers the start gate, the bounty and the bribe are tuned with (temporary heuristics, each with its reason).

A figure priced in labour hours is declared as hours; the module multiplies it by the money one unskilled hour is
worth (the view `money_per_labour_hour`) where it is used."""
from sim.constants import declare

BRIBE_MEMORY_DECAY = declare(
    "BRIBE_MEMORY_DECAY", 0.7, kind="temporary_heuristic",
    unit="fraction of bribes_ytd carried into the running total",
    source=None, confidence="D",
    why="How much of what has already been spent buying protection "
        "this year still counts when a new bribe is offered - past "
        "advocacy fades rather than vanishing outright or lasting "
        "forever. Tuned decay, not measured against any real "
        "patronage-buying persistence.")
BRIBE_PROTECTION_CAP = declare(
    "BRIBE_PROTECTION_CAP", 0.30, kind="temporary_heuristic",
    unit="protection points (0-1 scale)", source=None, confidence="D",
    why="The most protection money alone can buy, however much is "
        "spent - a break tester spent a million denarii for the "
        "identical result a hundred bought, and this is why: what a "
        "man cannot be paid to do more of, he cannot be paid more "
        "for. Tuned ceiling, not measured.")
BRIBE_INCOME_SHARE = declare(
    "BRIBE_INCOME_SHARE", 0.6, kind="temporary_heuristic",
    unit="fraction of revenue", source=None, confidence="D",
    why="The income scale bribery is measured against - what counts "
        "as a serious sum is relative to this share of revenue, not a "
        "flat denarii figure, so a rich household is not bought off "
        "as cheaply as a poor one. Tuned scale, not measured.")
BRIBE_LABOUR_HOURS_PER_SCANDAL_POINT = declare(
    "BRIBE_LABOUR_HOURS_PER_SCANDAL_POINT", 6050.0, kind="temporary_heuristic",
    unit="labour hours per point of household.scandal, at bribability=1", source=None, confidence="D",
    why='What it costs to erase one point of scandal outright. Scandal itself '
        'has no independent source model for who spreads it or how fast (the '
        'same gap STANDING_SCANDAL_PENALTY_PER_POINT in the polity module notes), so '
        'this conversion rate is a placeholder for that whole missing '
        'mechanism, not a measured price of silence. An official accepts a '
        'payment worth the work and risk he gives up, so the sum is the hours '
        'of unskilled labour it buys.')
BOUNTY_ELIGIBLE_COST_ADVANTAGE = declare(
    "BOUNTY_ELIGIBLE_COST_ADVANTAGE", 0.95, kind="temporary_heuristic",
    unit="dimensionless (civ_cost_factor)", source=None, confidence="D",
    why="A civilisation whose own cost multiplier for a technology is "
        "below this is treated as measurably good at it, and so able "
        "to recognise a bounty's success even outside the fixed "
        "craft-category allow-list (see this function's own comment "
        "on the Norse shipbuilding case this fixed). Tuned threshold "
        "for 'measurably good', not derived from any real skill "
        "assessment.")
BOUNTY_PRICE_MULTIPLIER = declare(
    "BOUNTY_PRICE_MULTIPLIER", 2.5, kind="temporary_heuristic",
    unit="dimensionless multiplier on this society's own build cost",
    source=None, confidence="D",
    why="How far over the odds a public prize pays - converting "
        "denarii into someone else's hours is a real trade a founder "
        "would want to make, and it should cost a real premium to "
        "make it. Tuned so a bounty is a genuine but expensive "
        "shortcut, not measured against any real prize-versus-wage "
        "ratio.")
PURCHASABLE_SUBSTITUTE_QUALITY_DISCOUNT = declare(
    "PURCHASABLE_SUBSTITUTE_QUALITY_DISCOUNT", 0.9, kind="temporary_heuristic",
    unit="dimensionless multiplier on the option's stated quality",
    source=None, confidence="D",
    why="A substitution option that is a purchasable commodity rather "
        "than something built or known scores slightly below its "
        "stated quality - buying a fuel or a vessel off the market is "
        "not quite as good as having built the specific thing the "
        "tree names. Tuned discount, not measured.")
ARREARS_GRACE_YEARS = declare(
    "ARREARS_GRACE_YEARS", 3, kind="temporary_heuristic",
    unit="years", source=None, confidence="D",
    why="How many consecutive years insolvent before new work starts "
        "being restricted at all - creditors care about PERSISTENT "
        "insolvency, not one bad year. Declared as the INT the source "
        "wrote: compared against an integer year-count "
        "(household.insolvent_years) with no fractional meaning, so "
        "widening it to a float would only invite the kind of "
        "int-to-float SAVE_FIELDS drift CLAUDE.md warns about "
        "elsewhere, for no benefit here. Tuned grace period, not "
        "measured.")
ARREARS_CHEAP_PROJECT_FLOOR_LABOUR_HOURS = declare(
    "ARREARS_CHEAP_PROJECT_FLOOR_LABOUR_HOURS", 12100.0, kind="temporary_heuristic",
    unit="labour hours", source=None, confidence="D",
    why='Even deep in persistent arrears, a project costing less than this is '
        "always 'cheap enough to need nobody's permission' - a flat floor under"
        " ARREARS_CHEAP_PROJECT_SURPLUS_MULTIPLE's own surplus-based figure so "
        'a household with zero surplus is not locked out of every project '
        'whatever. Tuned, not measured. How deep a debt a household can carry '
        'is the labour it would take to clear, so the floor is hours of work, '
        'the same burden whatever the coin is worth.')
ARREARS_CHEAP_PROJECT_SURPLUS_MULTIPLE = declare(
    "ARREARS_CHEAP_PROJECT_SURPLUS_MULTIPLE", 2.0, kind="temporary_heuristic",
    unit="years of true surplus", source=None, confidence="D",
    why="While persistently insolvent, a project is 'cheap enough' if "
        "it costs no more than this many years of the household's "
        "actual surplus (revenue minus upkeep, living cost and mine "
        "operating cost) - measured against what is actually LEFT, "
        "not gross turnover, which the fix here specifically corrects "
        "(see this method's own comment on the 11,637-revenue "
        "household this was measured against gross for). Tuned "
        "multiple, not derived.")
ARREARS_HARD_STOP_FLOOR_LABOUR_HOURS = declare(
    "ARREARS_HARD_STOP_FLOOR_LABOUR_HOURS", 80600.0, kind="temporary_heuristic",
    unit="labour hours", source=None, confidence="D",
    why='However cheap a project looks, new work stops outright once the '
        'household is this far underwater - a flat floor under '
        "ARREARS_HARD_STOP_REVENUE_MULTIPLE's revenue-based figure so a "
        'household with negligible revenue is not exempted from the hard stop '
        'entirely. Tuned, not measured. How deep a debt a household can carry '
        'is the labour it would take to clear, so the floor is hours of work, '
        'the same burden whatever the coin is worth.')
ARREARS_HARD_STOP_REVENUE_MULTIPLE = declare(
    "ARREARS_HARD_STOP_REVENUE_MULTIPLE", 2.0, kind="temporary_heuristic",
    unit="years of revenue", source=None, confidence="D",
    why="The debt-to-revenue ratio, in years of gross revenue, past "
        "which new work stops outright regardless of a project's own "
        "cost. Tuned ceiling, not derived from any real lending "
        "standard.")
STATE_WARY_THRESHOLD = declare(
    "STATE_WARY_THRESHOLD", -0.4, kind="temporary_heuristic",
    unit="state_interest score", source=None, confidence="D",
    why="Below this state_interest score, the state is merely wary of "
        "a technology and a local patron's name is enough cover to "
        "proceed. See docs/architecture 03_SOCIAL_POLITICS.md section "
        "4 for the social-approval mechanism this gates; the specific "
        "cutoff is tuned game balance over that mechanism, not itself "
        "derived from a historical record of state reactions.")
STATE_OPPOSED_THRESHOLD = declare(
    "STATE_OPPOSED_THRESHOLD", -1.2, kind="temporary_heuristic",
    unit="state_interest score", source=None, confidence="D",
    why="Below this state_interest score, the state actively opposes "
        "a technology and only senatorial-tier patronage or high "
        "personal protection can proceed anyway. Tuned cutoff, three "
        "times STATE_WARY_THRESHOLD's own magnitude so opposition is a "
        "meaningfully harder wall than wariness, not derived from any "
        "historical record.")
STATE_OPPOSITION_PROTECTION_OVERRIDE = declare(
    "STATE_OPPOSITION_PROTECTION_OVERRIDE", 0.45, kind="temporary_heuristic",
    unit="protection points (0-1 scale)", source=None, confidence="D",
    why="Personal protection above this substitutes for senatorial "
        "patronage when the state actively opposes a technology. "
        "Tuned so protection is a real alternative route, not "
        "measured.")


# ---- progress, completion, rebuild and staffing: the numbers the rest of the project lifecycle is tuned with ----

LAB_CREW_RATE_MULT = declare(
    "LAB_CREW_RATE_MULT", 4.0, kind="temporary_heuristic",
    unit="dimensionless multiple of the node's calibrated pace",
    source=None, confidence="D",
    why="A site can field more hands than its own historically-"
        "calibrated crew, but not without limit - a site has only so "
        "many benches, so extra hands beyond this multiple of the "
        "calibrated pace still go to waste. Tuned ceiling, not "
        "measured against any real crew-size elasticity.")

LAB_MAX_SPAN_FLOOR_YEARS = declare(
    "LAB_MAX_SPAN_FLOOR_YEARS", 40.0, kind="engineering_estimate",
    unit="years",
    source="A working lifetime: the span between becoming competent "
           "at a trade and retiring from it.",
    confidence="C",
    why="No single personal undertaking should be allowed to out-live "
        "the people who began it - past this, the people who "
        "understood the early stages are dead or have moved on, and "
        "continuing is not finishing the same project, it is starting "
        "a new one that happens to reuse the site. Grounded in a real "
        "demographic fact (a working lifetime) rather than tuned to a "
        "gameplay feel, though the exact figure is a round number, "
        "not a measured career-length distribution for any period.")

LAB_MAX_SPAN_MULTIPLE = declare(
    "LAB_MAX_SPAN_MULTIPLE", 4.0, kind="temporary_heuristic",
    unit="dimensionless multiple of the node's own calendar floor",
    source=None, confidence="D",
    why="A node whose own calendar floor already marks it as "
        "diffusion-limited (10+ years, a social process rather than a "
        "personal one) earns proportionately more room to find its "
        "hired trade before being abandoned - up to this multiple of "
        "its own floor, rather than an unbounded wait. Tuned "
        "multiple, not measured.")

RETRY_CALENDAR_CAP = declare(
    "RETRY_CALENDAR_CAP", 0.65, kind="temporary_heuristic",
    unit="fraction of the elapsed calendar time on a failed attempt",
    source=None, confidence="D",
    why="At most this share of the years already spent on a failed "
        "attempt is banked toward the next one - comfortably short of "
        "1.0 so a retried programme is never instantly ready, only "
        "readier than the last one. The diminishing, capped SHAPE "
        "mirrors the risk term above for the same 'never free' brief; "
        "the specific cap is tuned, not measured.")

RETRY_CALENDAR_DECAY = declare(
    "RETRY_CALENDAR_DECAY", 0.5, kind="temporary_heuristic",
    unit="fraction of the remaining calendar gap closed per failure",
    source=None, confidence="D",
    why="Each failure closes half of the gap between what is "
        "currently banked and RETRY_CALENDAR_CAP's own ceiling. Tuned "
        "decay rate, not fitted to any real social-diffusion recovery "
        "curve.")

CONTROL_RELIEF_FACTOR = declare(
    "CONTROL_RELIEF_FACTOR", 0.65, kind="temporary_heuristic",
    unit="fraction of risk remaining after relief (a flat 35% cut)",
    source=None, confidence="D",
    why="A completed process controller cuts a process-control node's "
        "risk by a flat 35%, earned once and never depending on "
        "failed_attempts, so it neither stacks unboundedly with retry "
        "learning nor reaches zero by itself - the brief was explicit "
        "that a real closed-loop controller (Minorsky 1922, "
        "Ziegler-Nichols tuning) genuinely mitigates a hold-at-"
        "setpoint failure mode, but the tension of a hard node like "
        "zone_refining must not be removed outright. The MECHANISM "
        "(control theory relieves this class of failure) is real and "
        "sourced; the specific 35% cut is tuned to leave meaningful "
        "risk, not measured from any real reliability improvement "
        "figure for early control systems.")

DIFFUSION_LIMITED_YEARS_THRESHOLD = declare(
    "DIFFUSION_LIMITED_YEARS_THRESHOLD", 5, kind="temporary_heuristic",
    unit="years (node['yrs'])", source=None, confidence="D",
    why="A node whose own calendar floor is at least this many years "
        "is treated as diffusion-limited (a social process reputation "
        "can shrink) rather than a physical curing or drying time "
        "reputation has no business touching. Declared as the INT the "
        "source wrote, compared directly against node['yrs'] (itself "
        "always a whole number of years in the tree data): no reason "
        "to widen it. Tuned cutoff, not measured.")

CALENDAR_FLOOR_MIN_YEARS = declare(
    "CALENDAR_FLOOR_MIN_YEARS", 2.0, kind="temporary_heuristic",
    unit="years", source=None, confidence="D",
    why="However much reputation shrinks a diffusion-limited node's "
        "calendar floor, it never falls below this - some minimum "
        "social process still has to happen. Tuned floor, not "
        "measured.")

CALENDAR_FLOOR_REPUTATION_SCALE = declare(
    "CALENDAR_FLOOR_REPUTATION_SCALE", 90.0, kind="temporary_heuristic",
    unit="reputation points per doubling of diffusion speed",
    source=None, confidence="D",
    why="How much reputation it takes to roughly halve a diffusion-"
        "limited node's calendar floor - a civilisation that already "
        "does a hundred complicated things does not start the "
        "hundred-and-first's social diffusion from zero credibility. "
        "Tuned to a similar order of magnitude as economy.py's "
        "REPUTATION_EASE_SCALE (120.0) for a related but distinct "
        "effect; not fitted to any measured diffusion-speed curve.")

MINOR_FAILURE_SHARE = declare(
    "MINOR_FAILURE_SHARE", 0.05, kind="temporary_heuristic",
    unit="fraction of funding capacity", source=None, confidence="D",
    why="A failed attempt that costs less than this share of what the "
        "player could fund is reported as one compact line; only the "
        "presentation depends on it, not the loss itself.")

GOAL_PATH_FAILURE_WEIGHT = declare(
    "GOAL_PATH_FAILURE_WEIGHT", 2.0, kind="temporary_heuristic",
    unit="multiplier on the loss share", source=None, confidence="D",
    why="A failure on the goal's own prerequisite road blocks the goal, "
        "so its loss counts for more when deciding how loudly to say "
        "it. Presentation only.")

FAILURE_RESET_SHARE = declare(
    "FAILURE_RESET_SHARE", 0.4, kind="temporary_heuristic",
    unit="fraction of founder-hours and of total cost", source=None,
    confidence="D",
    why="What a failed attempt costs and leaves still to do: forty "
        "per cent of the node's founder-hours are to do again, and "
        "forty per cent of its total cost (money-scaled) is lost - "
        "the SAME figure used for both, and used again to build the "
        "log message's own '%d%%' so the number cannot drift from "
        "what the arithmetic actually charges (see this method's own "
        "comment on the '40, NOT 60' bug, where the message once said "
        "sixty while the code charged forty). Tuned penalty, not "
        "measured against any real cost of a failed technical "
        "programme.")

REPUTATION_GAIN_BASE = declare(
    "REPUTATION_GAIN_BASE", 0.6, kind="temporary_heuristic",
    unit="reputation points, per completed technology", source=None,
    confidence="D",
    why="The baseline standing any completed technology earns, before "
        "state interest or visible revenue add anything further. "
        "Tuned game balance, not measured.")

REPUTATION_GAIN_STATE_INTEREST_COEFFICIENT = declare(
    "REPUTATION_GAIN_STATE_INTEREST_COEFFICIENT", 0.5, kind="temporary_heuristic",
    unit="reputation points per point of positive state_interest",
    source=None, confidence="D",
    why="How much extra standing a technology the state actually "
        "welcomes earns, on top of REPUTATION_GAIN_BASE - only the "
        "positive side of state_interest counts here (state "
        "opposition is priced elsewhere, in start_reason's own "
        "gates, not by shrinking a reward). Tuned, not measured.")

REPUTATION_GAIN_REVENUE_BONUS = declare(
    "REPUTATION_GAIN_REVENUE_BONUS", 1.2, kind="temporary_heuristic",
    unit="reputation points, if the node earns any revenue",
    source=None, confidence="D",
    why="Visible, useful, revenue-earning work builds standing faster "
        "than obscure laboratory work of equal difficulty - a real "
        "and annoying fact about how credibility accrues (this "
        "method's own comment), captured here as a flat bonus rather "
        "than a function of the revenue's actual size. Tuned, not "
        "measured.")

REBUILD_RETAINED_CEILING = declare(
    "REBUILD_RETAINED_CEILING", 0.75, kind="temporary_heuristic",
    unit="fraction of a node's work, money and calendar", source=None,
    confidence="D",
    why="The most of a forgotten node a rebuild can ever skip however "
        "much survives: even with a copy, practitioners and plant, the "
        "knowledge has to be re-established in the society. Tuned "
        "ceiling; the share below it is derived from state.")

COST_TAIL_SETTLE_SHARE = declare(
    "COST_TAIL_SETTLE_SHARE", 0.001, kind="temporary_heuristic",
    unit="fraction of the project's bill", source=None, confidence="D",
    why="How small a remainder, after the work and the calendar floor are "
        "done, counts as rounding and is paid at once rather than waiting "
        "a further year. Tuned, not measured.")

STAFFING_CLOSURE_SLACK = declare(
    "STAFFING_CLOSURE_SLACK", 0.5, kind="temporary_heuristic",
    unit="people (scholars or craftsmen)", source=None, confidence="D",
    why="Hysteresis band on the staffing-closure rule: a concern only "
        "closes when the shortfall is a real half-a-pair-of-hands or "
        "more, not any exact crossing of the line - attrition wobbles "
        "the balance every year, and an exact comparison closed and "
        "reopened the same concern almost every turn for centuries "
        "(see concerns_to_close_for_staffing). Shared with "
        "staffing_closure_warnings, which measures room against the "
        "same band so a warning and the actual closure rule can never "
        "disagree about where the line is. Tuned to stop the flapping, "
        "not measured.")

STAFFING_WARNING_BAND = declare(
    "STAFFING_WARNING_BAND", 5.0, kind="temporary_heuristic",
    unit="people (scholars or craftsmen) of headroom", source=None,
    confidence="D",
    why="How much slack has to remain before a running concern is "
        "worth warning about at all - a player asked, in their own "
        "words, to see 'power grid supervision is within 5 craftsmen "
        "of closure' before it happens. Tuned to give a year or two "
        "of real warning, not measured against any real staffing "
        "turnover rate.")

STAFFING_NO_SLACK_BAND = declare(
    "STAFFING_NO_SLACK_BAND", 1.0, kind="temporary_heuristic",
    unit="people (scholars or craftsmen) of headroom", source=None,
    confidence="D",
    why="Below this much headroom, the warning sharpens from 'N spare' "
        "to 'losing just one more closes it outright' - room this thin "
        "means one ordinary attrition event, not a policy failure or "
        "bad luck, is what actually closes the concern. Tuned to mark "
        "the point where the arithmetic really does mean one person, "
        "not measured.")

AUTO_OPEN_DEEP_ARREARS_CREDIT_SHARE = declare(
    "AUTO_OPEN_DEEP_ARREARS_CREDIT_SHARE", 0.5, kind="temporary_heuristic",
    unit="fraction of credit_limit", source=None, confidence="D",
    why="Beyond this share of the credit line owed, a household is "
        "'deep in arrears' for purposes of gating NEW institutional "
        "bleed (not ordinary net-positive concerns, which answer for "
        "themselves on payback period). Tuned to stop the optimizer "
        "borrowing to the hilt (the 'ABANDONED 1 works...two hundred "
        "and six times' history this function's own comment "
        "describes) without recreating the earlier catch-22 where a "
        "household already in the red could never open the shop that "
        "would dig it out.")

AUTO_OPEN_INSTITUTION_ARREARS_SHARE = declare(
    "AUTO_OPEN_INSTITUTION_ARREARS_SHARE", 0.75, kind="temporary_heuristic",
    unit="fraction of credit_limit", source=None, confidence="D",
    why="A second, slightly looser arrears threshold specifically for "
        "whether an institution may open against what it could RAISE "
        "rather than only what it is currently clearing. Tuned "
        "alongside AUTO_OPEN_DEEP_ARREARS_CREDIT_SHARE as one of 'two "
        "guards' against the same borrow-to-the-hilt failure mode; not "
        "measured.")

AUTO_OPEN_SURPLUS_SHARE_FOR_BLEED = declare(
    "AUTO_OPEN_SURPLUS_SHARE_FOR_BLEED", 0.5, kind="temporary_heuristic",
    unit="fraction of this year's real surplus", source=None,
    confidence="D",
    why="How much of this year's actual surplus (not credit) may be "
        "committed to a new institution's standing bleed. Tuned "
        "caution, not measured.")

AUTO_OPEN_CREDIT_LINE_BLEED_SHARE = declare(
    "AUTO_OPEN_CREDIT_LINE_BLEED_SHARE", 0.10, kind="temporary_heuristic",
    unit="fraction of credit_limit", source=None, confidence="D",
    why="The borrowing allowance ON TOP OF real surplus that lets a "
        "household cross the 'no institution ever affordable because "
        "there is no institution yet' deadlock (workshop_first "
        "bleeding 900/yr against a surplus that was negative BECAUSE "
        "there was no workshop - see this function's own long "
        "comment). Deliberately small and deliberately excluded from "
        "the later expansion-ladder loop, which spends real cash flow "
        "only. Tuned bootstrap allowance, not measured.")

AUTO_EXPAND_MIN_ROOM_UNITS = declare(
    "AUTO_EXPAND_MIN_ROOM_UNITS", 0.05, kind="temporary_heuristic",
    unit="units", source=None, confidence="D",
    why="Below this much room left under an institution's unit "
        "ceiling, expanding it further is not worth the bookkeeping - "
        "an epsilon-scale floor on a real decision (whether to spend "
        "an expansion step), not a display threshold. Tuned, not "
        "measured.")

AUTO_EXPAND_MIN_OCCUPANCY = declare(
    "AUTO_EXPAND_MIN_OCCUPANCY", 0.85, kind="temporary_heuristic",
    unit="fraction of institution_places", source=None, confidence="D",
    why="An institution is not expanded automatically until it is "
        "already this full - a household with room to spare is not "
        "short of more of it, whatever it could technically still "
        "borrow. Tuned occupancy trigger, not measured.")

AUTO_EXPAND_SURPLUS_SHARE = declare(
    "AUTO_EXPAND_SURPLUS_SHARE", 0.25, kind="temporary_heuristic",
    unit="fraction of this year's real surplus", source=None,
    confidence="D",
    why="At most a quarter of this year's real surplus may fund "
        "discretionary institutional GROWTH (as opposed to the "
        "bootstrap allowance that opens the first unit at all) - "
        "growth is optional, so it is capped tighter than survival "
        "spending. Tuned, not measured.")

AUTO_EXPAND_MIN_STEP_UNITS = declare(
    "AUTO_EXPAND_MIN_STEP_UNITS", 0.1, kind="temporary_heuristic",
    unit="units", source=None, confidence="D",
    why="The smallest expansion step worth actually taking in a "
        "single year - below this the bookkeeping is not worth it. "
        "Tuned, not measured.")

AUTO_OPEN_PAYBACK_LIMIT_YEARS = declare(
    "AUTO_OPEN_PAYBACK_LIMIT_YEARS", 3.0, kind="temporary_heuristic",
    unit="years", source=None, confidence="D",
    why="While deep in arrears, only a concern whose own capex clears "
        "inside this many years of its net revenue is offered at all - "
        "a concern that pays for its own door within a season or two "
        "is not the ABANDONED-206 failure mode (large capex against "
        "small net, borrowed to the hilt) this gate exists to stop. "
        "Tuned payback ceiling, not measured against any real lending "
        "standard.")

RESTORE_COST_MIN_UPKEEP_YEARS = declare(
    "RESTORE_COST_MIN_UPKEEP_YEARS", 2.0, kind="temporary_heuristic",
    unit="years of upkeep", source=None, confidence="D",
    why="A floor under restore's cost from the node's own upkeep, not "
        "only a share of build cost - thirty per cent of a cheap-to-"
        "build node is nothing, and this closed the hole where a "
        "cheap node could be mothballed and restored every tick for "
        "free (see this function's own comment). Twice what mines' "
        "own mothball-reversal already implies is not free either; "
        "tuned, not measured.")

FOUNDER_IS_WORTH = declare(
    "FOUNDER_IS_WORTH", 1.0, kind="temporary_heuristic",
    unit="craftsman-equivalent FTE", source=None, confidence="D",
    why="The founder counts as one ordinary pair of hands for "
        "purposes of running a small concern themselves, so an empty "
        "household is never locked out of opening its first shop (see "
        "this constant's own comment: 'no hands, so no concern; no "
        "concern, so no income; no income, so no hands'). A modelling "
        "necessity rather than a measured claim about one person's "
        "output.")

STARTER_FOUNDING_MIN_UNITS = declare(
    "STARTER_FOUNDING_MIN_UNITS", 0.2, kind="temporary_heuristic",
    unit="units", source=None, confidence="D",
    why="The smallest a first founding of a scalable institution may "
        "be asked for - below a fifth of the ordinary size there would "
        "be nothing left standing between 'a schoolroom' and 'no "
        "school at all'. A floor on the bridge that let a founder open "
        "a place smaller than the full historically-calibrated size "
        "when they could not yet afford the whole of it (see this "
        "table's own history in running()'s docstring); tuned, not "
        "measured.")

STAFF_CLOSURE_DISCOUNT = declare(
    "STAFF_CLOSURE_DISCOUNT", 0.1, kind="temporary_heuristic",
    unit="fraction of the full fee", source=None, confidence="D",
    why="What reopening a concern costs, within STAFF_CLOSURE_GRACE "
        "years of the staffing rule shutting it, relative to the full "
        "capex or restoration fee - the premises are still standing "
        "and the stock is still on the shelves, so only a tenth is "
        "owed, not the whole thing. Shared between open_venture and "
        "restore_work so a player is quoted the same discount from "
        "either verb. Tuned figure, not measured against any real "
        "cost of re-staffing an idle shop.")

STAFF_CLOSURE_GRACE = declare(
    "STAFF_CLOSURE_GRACE", 6, kind="temporary_heuristic",
    unit="years", source=None, confidence="D",
    why="How long a concern the staffing rule shut stands with its "
        "stock and lease intact before it counts as truly abandoned "
        "rather than merely unstaffed - past this, reopening costs "
        "the full price rather than STAFF_CLOSURE_DISCOUNT's tenth. "
        "Declared as the INT the source wrote, not 6.0: it is "
        "compared against and printed alongside self.year - _shut[k] "
        "(whole years) with %d formatting, so there is no reason to "
        "widen it to a float. Tuned game-balance window, not measured "
        "against any real reopening timeline.")

RESTORE_COST_SHARE_OF_BUILD = declare(
    "RESTORE_COST_SHARE_OF_BUILD", 0.3, kind="temporary_heuristic",
    unit="fraction of project_cost", source=None, confidence="D",
    why="What restoring a mothballed work (or hinting at its cost in "
        "start_reason's mothball message) costs relative to building "
        "it from nothing - you already know how, so it is cheaper "
        "than starting over. Shared between restore_work and "
        "start_reason's own mothball hint so the two can never quote "
        "different figures for the same thing. Tuned discount, not "
        "measured.")


OPPOSITION_COST_PER_UNIT = declare(
    "OPPOSITION_COST_PER_UNIT", 0.25, kind="temporary_heuristic",
    unit="fraction of cost added per unit of state opposition",
    source=None, confidence="D",
    why="How much bribes, delay and working through a front man add to "
        "a project's cost per unit of state_interest() opposition. "
        "state_interest() itself has no independent calibration against "
        "attested bribery or delay costs, so this conversion rate is "
        "tuned to feel like a real friction, not measured from one.")
