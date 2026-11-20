"""`spin-up-trace --stages`: the text of which goods the settle gaps are made of (sim/markets/spin_up_by_good.py) and of
what the years changed in the economy's mix (sim/markets/spin_up_mix_table.py)."""


def _short(value, pattern="%.4f"):
    return "-" if value is None else pattern % value


def _by_part(table):
    return sorted(table, key=lambda good: (-(table[good]["part"] or 0.0), -(table[good]["move"] or 0.0), good))


def format_by_good(table):
    """The watched goods, largest part of the "prices" gap first: share of the watched spending, largest yearly move over
    the measured years, part of the gap, then trend and saw over the trimmed stage."""
    lines = ["watched goods: over the measured years the share of the watched spending, the largest yearly move and the part "
             "of the prices gap (in the pair of years where it is largest); over the trimmed stage the trend (mean yearly "
             "move) and the saw (mean move about the trend):",
             "  %-22s %8s %8s %8s %8s %8s" % ("good", "share", "move", "part", "trend", "saw")]
    lines.extend("  %-22s %8s %8s %8s %8s %8s" % (good[:22], _short(table[good]["share"]), _short(table[good]["move"]),
                                               _short(table[good]["part"]), _short(table[good]["trend"]), _short(table[good]["saw"]))
                 for good in _by_part(table))
    return "\n".join(lines)


def format_parts(title, parts, count):
    """`title`, then the `count` largest of `parts` ([(good, signed share)]) on one line each."""
    lines = [title]
    lines.extend("  %-22s %+8.4f" % (good[:22], part) for good, part in parts[:count])
    if not parts:
        lines.append("  (no change measured)")
    return "\n".join(lines)


def format_level_parts(parts, count):
    """The `count` goods that moved the price level most in its worst pair of measured years: whether the good's price
    moved or the good entered or left the goods the level counts, and its effect as a share of the level."""
    lines = ["price level by good, in the pair of measured years where the level moved most (a good enters or leaves the "
             "count as its market trades or stops):"]
    lines.extend("  %-22s %-8s %+8.4f" % (good[:22], kind, effect) for good, kind, effect in parts[:count])
    if not parts:
        lines.append("  (no change measured)")
    return "\n".join(lines)


def _hours(value):
    return "%21s" % "-" if value is None else "%10.4g %10.4g" % value


def format_mix(labels, hours, output, recipes):
    """The mix tables: hours hired and idle by trade, output by good at the opening prices, and the recipes whose share of
    a good moved, one column per label."""
    head = " ".join("%21s" % label[:21] for label in labels)
    lines = ["hours by trade, hired and idle:", "  %-22s %s" % ("trade", head)]
    lines.extend("  %-22s %s" % (trade[:22], " ".join(_hours(value) for value in values)) for trade, values in hours)
    lines.extend(["output by good at the opening prices:", "  %-22s %s" % ("good", head)])
    lines.extend("  %-22s %s" % (good[:22], " ".join("%21s" % _short(value, "%.4g") for value in values)) for good, values in output)
    lines.extend(["recipes whose share of a good moved (share of the good made, before yields):", "  %-44s %s" % ("good: recipe", head)])
    for good, rows in recipes:
        lines.extend("  %-44s %s" % (("%s: %s" % (good, recipe_id))[:44], " ".join("%21s" % _short(value, "%.3f") for value in values))
                     for recipe_id, values in rows)
    return "\n".join(lines)


def format_member_level_parts(results):
    """One line per ensemble member: the goods that moved its price level most in its worst pair of measured years."""
    lines = ["price level by member, the goods that moved it most in its worst pair of measured years (share of the level):"]
    for result in results:
        parts = result.get("level_parts") or []
        lines.append("  m%-3d %s" % (result["member"], "; ".join("%s %s %+.4f" % (good, kind, effect) for good, kind, effect in parts)
                                     or "(no change measured)"))
    return "\n".join(lines)


def format_ensemble_by_good(medians):
    """The by-good table of an ensemble: each figure's median across the members ({good: {figure: median}})."""
    return "medians across the members\n" + format_by_good(medians)
