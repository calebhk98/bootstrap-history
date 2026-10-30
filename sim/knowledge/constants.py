"""The declared numbers of the knowledge module."""
from sim.constants import declare

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
