"""Capacity remedies: the commands that would end each shortage the screen names."""

import math
import re

# The commands a remedy sentence quotes, pulled out of the sentence itself so
# the sentence stays the one place a remedy is worded.
_QUOTED_COMMAND = re.compile(r"'((?:buy|quote|hire|train) [^']+)'")


def _material_remedy(sim, row):
    text = sim.shortage_remedy(row["material"])
    return {"shortage": row["material"],
            "short": "%s t/year" % "{:,.0f}".format(-row["surplus_t_per_yr"]),
            "commands": _QUOTED_COMMAND.findall(text), "how": text}


def _trade_remedy(sim, row):
    hours_short = row["demand_hours_this_year"] - row["supply_hours_this_year"]
    people = max(1, math.ceil(hours_short / sim.HOURS_PER_PERSON_YEAR))
    trade = row["trade"]
    commands = ["%s %s %d" % ("hire" if sim.trade_available(trade) else "train", trade, people)]
    homeless = people - max(0, math.floor(sim.household_room()))
    if homeless > 0:
        commands.append("buy housing %d" % homeless)
    return {"shortage": trade, "short": "%s hours/year" % "{:,.0f}".format(hours_short),
            "commands": commands,
            "how": "%d more %s would cover it%s" % (
                people, trade, "; the household has room for fewer, so house them too" if homeless > 0 else "")}


def capacity_remedies(sim, material_rows, trade_rows):
    """One row per short material or oversubscribed trade, worst first, each
    with the commands that would fix it. Material wording comes from
    `shortage_remedy`."""
    rows = [_material_remedy(sim, row) for row in material_rows if row["surplus_t_per_yr"] < 0]
    rows += [_trade_remedy(sim, row) for row in trade_rows if row.get("oversubscribed")]
    return rows


def render_remedies(rows):
    """Lines for the capacity screen: each shortage, then what to type."""
    if not rows:
        return []
    lines = ["", "  WHAT WOULD FIX EACH SHORTAGE"]
    for row in rows:
        lines.append("    %s (short %s): %s" % (row["shortage"], row["short"], "; ".join(row["commands"])
                                                if row["commands"] else row["how"]))
    return lines
