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
        'same gap STANDING_SCANDAL_PENALTY_PER_POINT in economy.py notes), so '
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
