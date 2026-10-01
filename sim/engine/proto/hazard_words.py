"""Plain words for a hazard's figures, shared by `risk` and `why` so one figure reads one way."""
from .util import _pct, _wrap


def figure_words(kind, value):
    """What a hazard's after-defences figure means, in the unit it is in."""
    if kind == "staff_loss":
        return "a wave takes %s of your staff" % _pct(value)
    if kind == "sack_chance":
        return "a %s chance a year that a site is sacked" % _pct(value)
    if kind == "output_factor":
        return "output falls to %s of normal" % _pct(value)
    return "the coin loses %s of its value" % _pct(value)


def why_standing_lines(out):
    """What finishing the thing adds to reputation and scandal."""
    effect = out.get("standing_effect")
    if not effect:
        return []
    parts = ["reputation +%.1f" % effect["reputation"]]
    if effect["scandal"] > 0.004:
        parts.append("scandal +%.1f" % effect["scandal"])
    return ["", _wrap("ON COMPLETION: %s (scandal falls a tenth a year on its own; "
                      "'state' shows how much is dangerous)" % ", ".join(parts))]


def why_hazard_lines(out):
    """Before and after, for each hazard ahead this would soften."""
    effects = out.get("hazard_effect")
    if not effects:
        return []
    lines = ["", "HAZARDS IT WOULD SOFTEN (at today's conditions, the same figures `risk` prints)"]
    for effect in effects:
        lines.append(_wrap("%s (%s-%s): %s with it running, against %s today" % (
            effect["name"], effect["years"][0], effect["years"][1],
            figure_words(effect["kind"], effect["with_it"]), _pct(effect["now"])), indent="  "))
    return lines


def advice_header(kind, advice, hazard, indent="  "):
    """The first line of a hazard's exposure on `risk`: the after-defences
    figure in its own unit, against what it would be with nothing built."""
    name = kind.replace("_", " ")
    after = hazard.get("%s_after_what_you_have_built" % kind)
    if after is None:
        after = hazard.get(kind) if kind == "real_erosion" else None
    if kind == "staff_loss" and after is not None:
        before = hazard.get("staff_loss_before_what_you_have_built", hazard.get(kind))
        line = "%s%s: %s" % (indent, name, figure_words(kind, after))
        if _pct(before) != _pct(after):
            line += " (%s before what you have built)" % _pct(before)
        national = hazard.get("national_public_health")
        if national:
            line += "\n%s  the country's own public health already takes %s off the historical %s, from medical work you built: %s" % (
                indent, _pct(national["share_removed"]), _pct(hazard.get(kind)),
                ", ".join(national["from"]) or "none named")
        return line
    if kind == "sack_chance" and after is not None:
        return "%s%s: %s (%s with nothing built)" % (
            indent, name, figure_words(kind, after), _pct(hazard.get(kind)))
    if kind == "output_factor" and after is not None:
        return "%s%s: %s in the worst year (%s with nothing built)" % (
            indent, name, figure_words(kind, after), _pct(hazard.get(kind)))
    return "%s%s: what you have built lets %s of the harm through" % (
        indent, name, _pct(advice.get("you_currently_take")))
