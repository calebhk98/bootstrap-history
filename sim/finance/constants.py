"""The declared numbers of the finance module: what lenders extend, what arrears cost, what a default does.

Amounts that are physical (a count of labour hours) are declared as hours and read as money through the
module's `priced`; the engine's forwarders keep the priced names the older code still reads."""
from sim.constants import declare

CREDIT_LINE_EARNING_MULTIPLE = declare(
    "CREDIT_LINE_EARNING_MULTIPLE", 0.5, kind="temporary_heuristic",
    unit="denarii of credit per denarii of standing yearly earning",
    source=None, confidence="D",
    why="How many years of standing income a lender extends to a "
        "complete stranger with nothing else vouching for them. No "
        "attested Roman credit-scoring source; a real figure needs a "
        "model of what a moneylender could actually observe and enforce "
        "against a given borrower's income, which this engine does not "
        "have.")

CREDIT_LINE_LABOUR_HOURS_PER_REPUTATION_POINT = declare(
    "CREDIT_LINE_LABOUR_HOURS_PER_REPUTATION_POINT", 5040.0, kind="temporary_heuristic",
    unit="labour hours of credit per reputation point", source=None, confidence="D",
    why='How much a point of reputation (itself a heuristic score, see '
        'STANDING_* above) is worth in raw borrowing power. Doubly removed from'
        ' any measurement: reputation is invented and this conversion rate is '
        'invented on top of it. A lender advances against expected repayment '
        'from labour, so the line is a count of labour hours; it follows what '
        'labour costs in the coin, not the coin itself.')

CREDIT_LINE_LABOUR_HOURS_PER_FOREST_HA = declare(
    "CREDIT_LINE_LABOUR_HOURS_PER_FOREST_HA", 2420.0, kind="temporary_heuristic",
    unit="labour hours of credit per hectare of owned forest", source=None,
    confidence="D",
    why="Amount of labour, not of coin: it was a book-denarii figure and now follows what labour costs. "
        "Forest is real collateral, so it counts toward credit the way "
        "FOREST_COST_PER_HA says it cost to buy; the per-hectare figure "
        "here is not tied back to that purchase price by any explicit "
        "loan-to-value ratio, just a plausible-feeling fraction of it.")

CREDIT_LINE_FLOOR_UPKEEP_BUFFER_SHARE = declare(
    "CREDIT_LINE_FLOOR_UPKEEP_BUFFER_SHARE", 0.5, kind="temporary_heuristic",
    unit="fraction of upkeep added to the running-tab floor",
    source=None, confidence="D",
    why="Extra headroom above bare living costs that ordinary "
        "tradesmen and landlords will still carry you for, on top of "
        "living_cost() itself - large enough that the floor does not "
        "sit exactly on the edge of insolvency, tuned rather than "
        "derived from any attested trade-credit practice.")

CREDIT_SURPLUS_YEARS_MULTIPLE = declare(
    "CREDIT_SURPLUS_YEARS_MULTIPLE", 5.0,
    kind="temporary_heuristic", unit="years of income/surplus",
    source=None, confidence="D",
    why="How many years of turnover (here) or of net surplus "
        "(funding_capacity(), below) a lender is willing to advance "
        "against - the bound that stops a large patron-name credit line "
        "turning into unpayable debt for a household with modest "
        "income. Chosen, per the comment this replaces, to leave the "
        "game's own opening decision unaffected, not fitted to any "
        "lending data.")

DEBT_RATE_REPUTATION_DISCOUNT_CAP = declare(
    "DEBT_RATE_REPUTATION_DISCOUNT_CAP", 0.03, kind="temporary_heuristic",
    unit="fraction off the base annual rate (maximum)", source=None,
    confidence="D",
    why="Ceiling on how much sheer personal reputation, independent of "
        "any named patron, can cheapen credit. Tuned so reputation "
        "alone cannot out-discount every patronage tier combined.")

DEBT_RATE_REPUTATION_SCALE = declare(
    "DEBT_RATE_REPUTATION_SCALE", 3000.0, kind="temporary_heuristic",
    unit="reputation points per percentage point of discount",
    source=None, confidence="D",
    why="How fast reputation converts into a cheaper interest rate, "
        "against DEBT_RATE_REPUTATION_DISCOUNT_CAP above. Reputation's "
        "own scale is itself invented (see STANDING_* above), so this "
        "is a heuristic layered on a heuristic.")

CREDIT_FREEZE_YEARS_AFTER_HALT = declare(
    "CREDIT_FREEZE_YEARS_AFTER_HALT", 5, kind="temporary_heuristic",
    unit="years", source=None, confidence="D",
    why="How long nobody will fund new work after projects are halted "
        "for exhausted credit. A real figure needs a model of how "
        "quickly a specific lending community forgives a specific "
        "default; this is a tuned, round number chosen to feel like a "
        "real but recoverable setback.")

CREDITOR_SEIZURE_VALUE_MULTIPLE = declare(
    "CREDITOR_SEIZURE_VALUE_MULTIPLE", 2.0, kind="temporary_heuristic",
    unit="years of upkeep recovered per concern seized", source=None,
    confidence="D",
    why="What creditors recover, in cash, for seizing and selling a "
        "concern that costs more than it earns - valued at twice its "
        "annual upkeep rather than any appraised resale value, because "
        "this model has no market for used capital goods. A real "
        "figure needs one.")

HOUSEHOLD_DISPERSAL_ARTISANS_RETENTION = declare(
    "HOUSEHOLD_DISPERSAL_ARTISANS_RETENTION", 0.4, kind="temporary_heuristic",
    unit="fraction of artisans kept after the household disperses",
    source=None, confidence="D",
    why="How many trained artisans stay with a ruined household after "
        "the rest are freed or sold - some core of skilled people is "
        "plausible, but the specific 40% retained is tuned game "
        "balance, not derived from any account of how a Roman household "
        "actually broke up under debt.")

HOUSEHOLD_DISPERSAL_ARTISANS_FLOOR = declare(
    "HOUSEHOLD_DISPERSAL_ARTISANS_FLOOR", 3.0, kind="temporary_heuristic",
    unit="artisans", source=None, confidence="D",
    why="The minimum artisan headcount a dispersed household keeps, so "
        "a small household does not round to zero and become unable to "
        "ever recover. Chosen so recovery stays possible, not measured.")

DEBT_BONDAGE_DEFAULT_TERM_YEARS = declare(
    "DEBT_BONDAGE_DEFAULT_TERM_YEARS", 10.0, kind="temporary_heuristic",
    unit="years", source=None, confidence="D",
    why="Fallback term of debt bondage/service for a civilisation whose "
        "own data does not specify one (civ.get('bondage_years', ...)). "
        "Historical debt-service terms across the systems this method's "
        "own docstring names (Han, Norse, Mexica) varied by circumstance "
        "rather than clustering on a single figure, so this is a round "
        "placeholder, not a citation.")

SETTLEMENT_CAPITAL_RETAINED_FRACTION = declare(
    "SETTLEMENT_CAPITAL_RETAINED_FRACTION", 0.35, kind="temporary_heuristic",
    unit="fraction of the credit limit still owed after settlement",
    source=None, confidence="D",
    why="How much debt survives an insolvency write-off, as a fraction "
        "of the credit limit rather than of the actual arrears - so "
        "settlement always leaves you owing something (a real write-off "
        "rarely erases a debt entirely) without the residue growing "
        "without bound. Tuned, not modelled on any attested bankruptcy "
        "practice.")

SETTLEMENT_REPUTATION_HIT = declare(
    "SETTLEMENT_REPUTATION_HIT", 12.0, kind="temporary_heuristic",
    unit="reputation points", source=None, confidence="D",
    why="How much standing an insolvency write-off costs. Reputation's "
        "own scale is already invented (STANDING_* above); this is a "
        "further tuned penalty on top of it.")

SETTLEMENT_CREDIT_FREEZE_YEARS = declare(
    "SETTLEMENT_CREDIT_FREEZE_YEARS", 12, kind="temporary_heuristic",
    unit="years", source=None, confidence="D",
    why="How long nobody extends fresh credit after a write-off - "
        "longer than CREDIT_FREEZE_YEARS_AFTER_HALT because an actual "
        "default is worse than a temporary halt, but the specific "
        "figure is tuned game feel, not a lending-market estimate.")

SPENDING_DRAW_SHARE_ORDINARY = declare(
    "SPENDING_DRAW_SHARE_ORDINARY", 0.5, kind="temporary_heuristic",
    unit="fraction of the credit line drawable for buy/hire", source=None,
    confidence="D",
    why="A lender advances against unfinished WORK (a `start`) more "
        "readily than against a payroll or a purchase that leaves "
        "nothing half-built to point at - a real distinction, per this "
        "method's own docstring - but the specific half-vs-whole split "
        "is a tuned game-balance choice, not derived from any lending "
        "practice.")

LIVING_COST_STATUS_PER_CAPITAL = declare(
    "LIVING_COST_STATUS_PER_CAPITAL", 0.015, kind="temporary_heuristic",
    unit="fraction of capital spent on appearances per year",
    source=None, confidence="D",
    why="'You cannot look poor and rich': how much of a wealthy "
        "household's own capital its visible standard of living must "
        "track, reused as both the raw status cost and the ceiling on "
        "how far the appearances budget can be trimmed. A real figure "
        "needs an actual model of conspicuous consumption in a "
        "patronage society, not a flat share of capital.")

LIVING_COST_APPEARANCES_SHARE_OF_ROOM = declare(
    "LIVING_COST_APPEARANCES_SHARE_OF_ROOM", 0.75, kind="temporary_heuristic",
    unit="fraction of remaining income", source=None, confidence="D",
    why="How much of what is left after eating, tax, upkeep and wages "
        "a household will spend on keeping up appearances, so status "
        "spending draws down what is left rather than starving the "
        "household outright - see the comment above for the ruined-"
        "household bug this fixed. The specific three-quarters share "
        "is tuned game balance, not derived from any household-budget "
        "study.")

DEBT_SERVICE_SHARE_OF_SURPLUS = declare(
    "DEBT_SERVICE_SHARE_OF_SURPLUS", 0.5, kind="temporary_heuristic",
    unit="fraction of the recurring surplus", source=None, confidence="D",
    why="How much of the yearly surplus may go on arrears interest before "
        "a debt is called unsustainable, leaving the rest to pay the "
        "principal down. A tuned prudence level, not a lender's rule.")

INSOLVENCY_FLOOR_MIN_LABOUR_HOURS = declare(
    "INSOLVENCY_FLOOR_MIN_LABOUR_HOURS", 80600.0, kind="temporary_heuristic",
    unit="labour hours", source=None, confidence="D",
    why="Floor on how deep into arrears a household can sit before insolvency's"
        ' staff bleed can begin, for a household with very low revenue - so a '
        'household earning almost nothing is not bled the instant it dips a '
        'denarius below zero. Round number, not measured. How deep a debt a '
        'household can carry is the labour it would take to clear, so the floor'
        ' is hours of work, the same burden whatever the coin is worth.')

INSOLVENCY_FLOOR_REVENUE_MULTIPLE = declare(
    "INSOLVENCY_FLOOR_REVENUE_MULTIPLE", 2.0, kind="temporary_heuristic",
    unit="years of revenue", source=None, confidence="D",
    why="How many years of revenue a household may sit in arrears "
        "before insolvency's staff bleed can begin, for a household "
        "with meaningful revenue - scales the floor to the "
        "household's own size rather than a flat number. Tuned, not "
        "measured.")

INSOLVENCY_YEARS_BEFORE_BLEED = declare(
    "INSOLVENCY_YEARS_BEFORE_BLEED", 3, kind="temporary_heuristic",
    unit="years", source=None, confidence="D",
    why="Consecutive years of genuine insolvency (income not "
        "covering costs, past INSOLVENCY_FLOOR_MIN/"
        "INSOLVENCY_FLOOR_REVENUE_MULTIPLE) before staff actually "
        "start leaving - a brief dip is not treated the same as "
        "sustained failure. Round number, not measured.")

INSOLVENCY_BLEED_CAP = declare(
    "INSOLVENCY_BLEED_CAP", 0.15, kind="temporary_heuristic",
    unit="dimensionless (maximum fraction of staff lost per year)",
    source=None, confidence="D",
    why="Ceiling on how much of the artisan pool insolvency can bleed "
        "in a single year, however long the household has been "
        "insolvent - a floor against the doom loop this mechanism "
        "replaced (see comment above: a Norse run once sat insolvent "
        "for 495 years, bleeding without limit). Tuned, not measured.")

INSOLVENCY_BLEED_RATE = declare(
    "INSOLVENCY_BLEED_RATE", 0.04, kind="temporary_heuristic",
    unit="dimensionless (fraction of staff lost per insolvent year)",
    source=None, confidence="D",
    why="How fast the insolvency bleed grows with consecutive "
        "insolvent years, capped at INSOLVENCY_BLEED_CAP. Tuned, not "
        "measured.")

INSOLVENCY_ARTISAN_FLOOR = declare(
    "INSOLVENCY_ARTISAN_FLOOR", 3.0, kind="temporary_heuristic",
    unit="artisans", source=None, confidence="D",
    why="Minimum artisans an insolvent household keeps, however long "
        "it bleeds - a household that has shed everything else can "
        "still climb back rather than being erased outright. Round "
        "number, not measured.")

INSOLVENCY_SCHOLAR_FLOOR = declare(
    "INSOLVENCY_SCHOLAR_FLOOR", 1.0, kind="temporary_heuristic",
    unit="scholars", source=None, confidence="D",
    why="Minimum scholars an insolvent household keeps, for the same "
        "reason as INSOLVENCY_ARTISAN_FLOOR. Round number, not "
        "measured.")

INSOLVENCY_SCHOLAR_BLEED_DISCOUNT = declare(
    "INSOLVENCY_SCHOLAR_BLEED_DISCOUNT", 0.6, kind="temporary_heuristic",
    unit="dimensionless (fraction of the artisan bleed rate applied "
         "to scholars)", source=None, confidence="D",
    why="Scholars bleed slower than artisans under insolvency - "
        "tuned so a household in arrears keeps more of its scarce, "
        "harder-to-replace literate staff; not measured.")

BONDAGE_LABOUR_SHARE = declare(
    "BONDAGE_LABOUR_SHARE", 0.75, kind="temporary_heuristic",
    unit="dimensionless (share of a founder-year's hours)",
    source=None, confidence="D",
    why="Share of a founder's yearly hours treated as owed labour "
        "while serving out a debt-bondage term. Tuned to leave some "
        "hours for the founder's own affairs even in bondage; not "
        "measured.")

BONDAGE_WAGE_MARKUP = declare(
    "BONDAGE_WAGE_MARKUP", 1.2, kind="temporary_heuristic",
    unit="dimensionless multiplier", source=None, confidence="D",
    why="Markup on the plain labourer wage used to value bonded "
        "labour toward debt repayment - bonded labour is valued a "
        "little above the cheapest free-market rate. Tuned, not "
        "measured.")

LENDING_HORIZON_YEARS = declare(
    "LENDING_HORIZON_YEARS", 10.0, kind="temporary_heuristic",
    unit="years of household saving", source=None, confidence="D",
    why="How many years of what households save stand as funds lenders hold in loanable form. Stands "
        "in for an accumulating stock of savings with its own losses and uses.")

BACKGROUND_BORROWING_SHARE = declare(
    "BACKGROUND_BORROWING_SHARE", 0.5, kind="temporary_heuristic",
    unit="share of the funds households' saving supports", source=None, confidence="D",
    why="What the economy the simulation does not model actor by actor (farmers, traders, landlords) "
        "borrows against the same savings. Stands in for those borrowers.")

LENDABLE_RESERVE_SHARE = declare(
    "LENDABLE_RESERVE_SHARE", 0.1, kind="temporary_heuristic",
    unit="share of the state's reserve beyond a year's need", source=None, confidence="D",
    why="How much of its spare reserve a state puts into the loanable pool (the rest stays as coin and "
        "bullion). Stands in for a treasury's investment policy.")
