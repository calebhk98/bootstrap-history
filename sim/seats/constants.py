"""The heuristics of a programme its founder has left: how long it lasts, what it forgets, and the deputies that carry it."""
from sim.constants import declare

SANITATION_LIFE_EXTENSION_YEARS = declare(
    "SANITATION_LIFE_EXTENSION_YEARS", 0.12, kind="temporary_heuristic",
    unit="years added per year of founder mortality roll",
    source=None, confidence="D",
    why="Extra expected lifespan per year once sanitation and "
        "antisepsis are known - 'you at least do not die of a septic "
        "cut'. A real effect in kind (antisepsis measurably cut "
        "mortality), invented in this specific magnitude; a real "
        "figure needs an actual survival-curve shift rather than a "
        "flat annual bonus.")
DISSOLUTION_YEARS_BEFORE_FORGETTING = declare(
    "DISSOLUTION_YEARS_BEFORE_FORGETTING", 3, kind="temporary_heuristic",
    unit="years", source=None, confidence="D",
    why="Years a founderless programme sits stalled before it starts "
        "actively forgetting technologies - a brief gap is not yet "
        "dissolution. Round number, not measured.")
DISSOLUTION_FORGET_FRACTION_DIVISOR = declare(
    "DISSOLUTION_FORGET_FRACTION_DIVISOR", 6, kind="temporary_heuristic",
    unit="dimensionless (divisor; forgets roughly a sixth)",
    source=None, confidence="D",
    why="How large a bite a dissolving programme's forgetting takes "
        "each qualifying year - roughly a sixth of what remains "
        "losable. Tuned so full dissolution over "
        "DISSOLUTION_YEARS_UNTIL_END years is gradual, not "
        "instantaneous; not measured.")
DEPUTIES_CARRY_THE_WORK_FROM = declare(
    "DEPUTIES_CARRY_THE_WORK_FROM", 0.5, kind="temporary_heuristic",
    unit="deputies (continuous level of directors_extra)", source=None,
    confidence="D",
    why="How many deputies it takes before a programme can go on "
        "without its founder; below it the deputies still do real "
        "work but the dissolution clock keeps running. One rule, "
        "read by the death notice, the clock, hiring and `state`. "
        "Round number, not measured.")
DISSOLUTION_YEARS_UNTIL_END = declare(
    "DISSOLUTION_YEARS_UNTIL_END", 12, kind="temporary_heuristic",
    unit="years", source=None, confidence="D",
    why="Years a founderless, deputy-less programme can dissolve "
        "before the run ends outright - stated directly to the player "
        "('the programme goes on without you... over twelve years' / "
        "'the run ends at twelve'), so this number is quoted in "
        "several log messages as well as enforced here. Round number, "
        "not measured.")
