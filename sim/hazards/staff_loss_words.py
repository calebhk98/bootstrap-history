"""How a staff-loss wave is told to the player: what the household's own defences did, and the national toll.

The classification is a rule on the relief the household's works leave (the multiplier on the national rate); the
sentences are built from figures the caller passes. Kinds: `held_off` (relief at most a quarter of the harm),
`softened` (at most three quarters), `plain` (little or no defence, or nothing named that did it).
"""
from typing import Sequence

HELD_OFF_RELIEF_AT_MOST = 0.25
SOFTENED_RELIEF_AT_MOST = 0.75
# a national relief below this share is too small to tell
NATIONAL_RELIEF_WORTH_TELLING = 0.02
# a national toll below this share is not told as a toll
NATIONAL_TOLL_WORTH_TELLING = 0.01


def defence_kind(relief: float, why: Sequence[str]) -> str:
    """`held_off`, `softened` or `plain`, from the multiplier the household's own works leave on the harm."""
    if why and relief <= HELD_OFF_RELIEF_AT_MOST:
        return "held_off"
    if why and relief <= SOFTENED_RELIEF_AT_MOST:
        return "softened"
    return "plain"


def staff_clause(loss: float, relief: float, why: Sequence[str]) -> str:
    """The household's own staff loss, with what did the defending when something did."""
    kind = defence_kind(relief, why)
    if kind == "held_off":
        return "staff -%d%%, held off almost entirely by what you built (%s)" % (loss * 100, "; ".join(why))
    if kind == "softened":
        return "staff -%d%% (softened by %s)" % (loss * 100, "; ".join(why))
    return "staff -%d%%" % (loss * 100)


def national_toll_sentence(raw: float, historical: float, national_relief: float, sources: str) -> str:
    """The sentence on the country's toll, told apart from the household's own; empty when neither the toll nor a
    national relief is worth telling."""
    if raw > NATIONAL_TOLL_WORTH_TELLING:
        softer = (" (the country's own public health has spread far enough to hold this below the "
                  "%d%% this would otherwise have been - %d%% softer; that is medical work you "
                  "built (%s) spreading through the country)"
                  % (round(historical * 100), round(national_relief * 100), sources)
                  if national_relief > NATIONAL_RELIEF_WORTH_TELLING else "")
        return (". Empire-wide, population -%d%%%s - wages (and everything paid in them) stay dear until the "
                "population does, either way" % (raw * 100, softer))
    if national_relief > NATIONAL_RELIEF_WORTH_TELLING and historical > NATIONAL_TOLL_WORTH_TELLING:
        return (". Empire-wide: the country's own public health (medical work you built: %s) has spread far "
                "enough that this, historically a %d%% loss, barely registers" % (sources, round(historical * 100)))
    return ""
