"""The declared numbers of the hazards module."""
from sim.constants import declare

KNOWLEDGE_RESIDUE_AFTER_CLOSURE = declare(
    "KNOWLEDGE_RESIDUE_AFTER_CLOSURE", 0.3, kind="temporary_heuristic",
    unit="dimensionless (fraction of a counter's relief kept)",
    source=None, confidence="D",
    why="Share of a hazard counter's relief that survives closing the "
        "institution that delivered it: people who learned the "
        "procedure and a public that saw it work remain, stockpiles "
        "and trained staff do not. Not derived from a decay model.")
MILITARY_WAR_RELIEF_CAP = declare(
    "MILITARY_WAR_RELIEF_CAP", 0.30, kind="temporary_heuristic",
    unit="dimensionless (fraction of war output-shock relieved at "
         "military_leverage=1.0)", source=None, confidence="D",
    why="Ceiling on how much a founder's own military work softens an "
        "output-crushing war - matched to endowment_land's own share "
        "in HAZARD_COUNTERS['output_factor'] rather than exceeding it, "
        "so land and an army are comparable hedges and neither dwarfs "
        "the other (see this method's own docstring). A relative "
        "calibration against another already-tuned figure, not a "
        "measured relief rate.")
STAFF_LOSS_HAZARD_ANNUAL_CHANCE = declare(
    "STAFF_LOSS_HAZARD_ANNUAL_CHANCE", 0.32, kind="temporary_heuristic",
    unit="dimensionless (yearly probability while the hazard's window "
         "is open)", source=None, confidence="D",
    why="Chance, in any given year of a staff_loss hazard's dated "
        "window, that it actually strikes this year rather than "
        "passing quietly - a multi-year plague window does not bite "
        "every single year of it. Tuned so the hazard is likely but "
        "not certain within its window; not fitted to any attested "
        "epidemic-year distribution.")
PLAGUE_CASH_LOSS_SHARE = declare(
    "PLAGUE_CASH_LOSS_SHARE", 0.6, kind="temporary_heuristic",
    unit="dimensionless (fraction of the staff-loss fraction)",
    source=None, confidence="D",
    why="How much capital a staff-loss hazard also takes, as a "
        "multiple of the staff fraction lost - a plague empties the "
        "market as well as the workshop (see comment above). Tuned to "
        "make the cash loss proportionate to the staff loss, not "
        "measured against any attested plague-year revenue collapse.")
SACK_TAKE_STRENGTH = declare(
    "SACK_TAKE_STRENGTH", 0.60, kind="temporary_heuristic",
    unit="dimensionless (share of fully portable, visible, unguarded wealth)", source=None,
    confidence="D",
    why="Share of fully exposed wealth a sack takes - the largest single "
        "theft in this file. What is actually taken is this share scaled "
        "by theft_exposure: portability of each kind of holding, guarding "
        "and visibility, with the state's order failed. Tuned, not "
        "measured against any attested sacking's proceeds.")
SACK_STAFF_RETENTION = declare(
    "SACK_STAFF_RETENTION", 0.55, kind="temporary_heuristic",
    unit="dimensionless (fraction of artisans/scholars/hired staff "
         "kept)", source=None, confidence="D",
    why="Fraction of artisans, scholars and every hired trade kept "
        "after a sack - applied uniformly across every trade so a "
        "sack is not gentler to hired staff than the plague family is "
        "(see comment above). Tuned, not measured.")
REAL_EROSION_CASH_LOSS_SHARE = declare(
    "REAL_EROSION_CASH_LOSS_SHARE", 0.85, kind="temporary_heuristic",
    unit="dimensionless (fraction of the debasement rate)",
    source=None, confidence="D",
    why="How much of a currency debasement's rate also bites the "
        "cash actually held, on top of the money_real devaluation "
        "applied to everything - debasement destroys held coin faster "
        "than it destroys quoted labour/material costs (see this "
        "branch's own comment). Tuned, not measured against any "
        "attested debasement episode's real losses.")
SACK_DIRECTORS_RETENTION = declare(
    "SACK_DIRECTORS_RETENTION", 0.65, kind="temporary_heuristic",
    unit="dimensionless (fraction of deputy directors kept)",
    source=None, confidence="D",
    why="Fraction of deputy directors kept after a sack - higher than "
        "SACK_STAFF_RETENTION on the reasoning that the institutions "
        "producing deputies are more resilient than ordinary staff on "
        "the ground. Tuned, not measured.")
PATRON_DEATH_ANNUAL_CHANCE = declare(
    "PATRON_DEATH_ANNUAL_CHANCE", 0.05, kind="temporary_heuristic",
    unit="dimensionless (yearly probability, local patron only)",
    source=None, confidence="D",
    why="Yearly chance a local patron dies, prompting the need to "
        "court an heir - invented frequency, not fitted to any "
        "attested mortality rate for a Roman patronal relationship.")
PATRON_DEATH_COOLDOWN_YEARS = declare(
    "PATRON_DEATH_COOLDOWN_YEARS", 25, kind="temporary_heuristic",
    unit="years", source=None, confidence="D",
    why="Minimum gap between one patron's death and the next roll - a "
        "patron dies once and then you have courted his heir; the "
        "cooling-off keeps this from repeating within an implausibly "
        "short span. Round number, not measured.")
PATRON_DEATH_SCANDAL = declare(
    "PATRON_DEATH_SCANDAL", 4, kind="temporary_heuristic",
    unit="scandal points", source=None, confidence="D",
    why="Scandal a patron's death and the scramble to court his heir "
        "generates. Tuned to be a real but minor bump; not measured.")
PATRON_DEATH_PROTECTION_RETENTION = declare(
    "PATRON_DEATH_PROTECTION_RETENTION", 0.6, kind="temporary_heuristic",
    unit="dimensionless (fraction of protection kept)", source=None,
    confidence="D",
    why="Fraction of protection kept when a patron dies - losing most "
        "of your cover until a new patron relationship is established. "
        "Tuned, not measured.")
PATRON_DEATH_COURTING_GIFT_LABOUR_HOURS = declare(
    "PATRON_DEATH_COURTING_GIFT_LABOUR_HOURS", 16100.0, kind="temporary_heuristic",
    unit="labour hours at price_index=1.0", source=None, confidence="D",
    why="Amount of labour, not of coin: it was a book-denarii figure and now follows what labour costs. "
        "Cost of courting a dead patron's heir afresh, at this "
        "society's own price level. Invented figure, not sourced to "
        "any attested gift-giving custom.")
PATRON_DEATH_RECOVERY_NOTE = (
    ". The dip lasts until the next year-end recount of protection, when "
    "the patron's office passes to his heir and the offices and standing "
    "you hold count again; the scandal is a one-off, not a yearly trend. "
    "By hand, 'bribe <amount>' courts the heir and buys scandal down.")
FIRE_ANNUAL_CHANCE = declare(
    "FIRE_ANNUAL_CHANCE", 0.03, kind="temporary_heuristic",
    unit="dimensionless (yearly probability)", source=None,
    confidence="D",
    why="Yearly chance of a fire in the household's own quarter - a "
        "tester playing Han China counted nine fires in Luoyang's "
        "insula district in a hundred years, which this rate is "
        "roughly consistent with, but the figure itself was chosen "
        "rather than fitted to an urban-fire record.")
FIRE_CAPITAL_LOSS = declare(
    "FIRE_CAPITAL_LOSS", 0.18, kind="temporary_heuristic",
    unit="dimensionless (fraction of capital)", source=None,
    confidence="D",
    why="Fraction of capital a fire destroys. Tuned to be a real but "
        "recoverable setback; not measured against any attested urban "
        "fire's losses.")
BANDITRY_ANNUAL_CHANCE = declare(
    "BANDITRY_ANNUAL_CHANCE", 0.02, kind="temporary_heuristic",
    unit="dimensionless (yearly probability)", source=None,
    confidence="D",
    why="Yearly chance banditry or a frontier war disrupts supply. "
        "Invented frequency, not fitted to any attested record.")
BANDITRY_TAKE_STRENGTH = declare(
    "BANDITRY_TAKE_STRENGTH", 0.10, kind="temporary_heuristic",
    unit="dimensionless (share of fully portable, visible, unguarded wealth)", source=None,
    confidence="D",
    why="Share of fully exposed wealth a bandit year takes. What is "
        "actually taken is this share scaled by theft_exposure: "
        "portability of each kind of holding, guarding, visibility and "
        "the state's order. Tuned, not measured.")
CORPUS_HEDGE_LOSS_CHANCE_NONE = declare(
    "CORPUS_HEDGE_LOSS_CHANCE_NONE", 0.80, kind="temporary_heuristic",
    unit="dimensionless (probability a sack takes any corpus at all)",
    source=None, confidence="D",
    why="Chance a sack takes any of the corpus with no written hedge "
        "at all - the founder's own head and workshop are the only "
        "copy. Tuned to make an unhedged corpus genuinely dangerous "
        "to hold; not measured.")
CORPUS_HEDGE_FRACTION_LOST_NONE = declare(
    "CORPUS_HEDGE_FRACTION_LOST_NONE", 0.40, kind="temporary_heuristic",
    unit="dimensionless (fraction of losable technologies taken)",
    source=None, confidence="D",
    why="If a sack does take from an unhedged corpus, how much of "
        "what is still losable it takes - largest of the three "
        "states. Tuned, not measured.")
OUTPUT_RECOVERY_RATE = declare(
    "OUTPUT_RECOVERY_RATE", 0.006, kind="temporary_heuristic",
    unit="dimensionless per year (base recovery toward output_factor "
         "1.0)", source=None, confidence="D",
    why="Base yearly recovery rate of output_factor after a war or "
        "other output shock, doubled at full military leverage (see "
        "comment above) - an armed empire recovers roughly twice as "
        "fast as an unarmed one, not instantly. Tuned to make a war's "
        "damage linger for decades, not measured against any attested "
        "postwar recovery rate.")

_HAZARD_COUNTER_WHY = (
    "How much of this hazard one mitigating technology removes, "
    "compounding with every other counter for the same hazard and "
    "never reaching zero on its own (no amount of sanitation stops a "
    "plague; it decides how many people are still alive after). The "
    "MECHANISM this technology relieves this hazard through is real "
    "and named at its own declaration; the specific fraction removed "
    "is tuned game balance sized so the hazard remains real even "
    "fully countered, not measured against any historical mortality, "
    "sack or currency-debasement reduction.")
HAZARD_EROSION_OWN_GOLD = declare(
    "HAZARD_EROSION_OWN_GOLD", 0.55, kind="temporary_heuristic",
    unit="fraction of real-erosion hazard removed",
    source="your own gold, dug not minted", confidence="D",
    why=_HAZARD_COUNTER_WHY)
HAZARD_EROSION_OWN_SILVER = declare(
    "HAZARD_EROSION_OWN_SILVER", 0.35, kind="temporary_heuristic",
    unit="fraction of real-erosion hazard removed",
    source="your own silver", confidence="D", why=_HAZARD_COUNTER_WHY)

HAZARD_TIMELINE_BEGIN_NOW_MULT = 1.5
HAZARD_TIMELINE_WARN_TAGS = frozenset(
    {"happening now", "too late to hedge", "stopgap only", "begin hedge now"})
CLOSURE_REASON_WORDS = {
    "staff": "for want of staff",
    "manual": "by your choice",
    "loss_making": "because it was losing money",
    "creditor_seizure": "after creditors seized it",
}
HAZARD_KINDS = ("staff_loss", "sack_chance", "output_factor", "real_erosion")
ADVICE_WORDS = {"staff_loss": "clean water, quarantine, and eventually inoculation",
                "sack_chance": "walls, firearms, powerful friends, and copies of your work kept somewhere else",
                "output_factor": "land and power of your own, not depending on trade a war can cut, and a state that can fight back",
                "real_erosion": "metal you dug yourself, land, and a way to prove what a coin contains"}
