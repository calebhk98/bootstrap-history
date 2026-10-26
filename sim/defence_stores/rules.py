"""What a defence needs in hand, as plain functions: powder in a magazine and a garrison present (Complaint 245), and the
food a running work hands out."""


def counter_spec(node, kind, label):
    """The `hazard_counters` entry of a node for this kind and label, else {}."""
    for counter in ((node.get("mechanics") or {}).get("hazard_counters") or ()):
        if counter["kind"] == kind and counter["label"] == label:
            return counter
    return {}


def venture_garrison(garrison, units):
    """{trade: people} an open concern holds as its garrison, at `units` times its founding size."""
    return {trade: people * units for trade, people in sorted((garrison or {}).items()) if people > 0.0}


def garrison_share(needed, claims, employed):
    """(share of the garrison present, the trade most short or None): employed people of each trade against what
    every garrison in force claims of it, shared out evenly."""
    if not needed:
        return 1.0, None
    share, short_trade = 1.0, None
    for trade, people in needed.items():
        claim = max(claims.get(trade, 0.0), people)
        present = min(1.0, employed.get(trade, 0.0) / claim)
        if present < share:
            share, short_trade = present, trade
    return share, short_trade


def magazine_share(magazine, held_units_of):
    """(share of the magazine held, the material most short or None)."""
    share, short_material = 1.0, None
    for material, units in sorted((magazine or {}).items()):
        held = min(1.0, held_units_of(material) / units) if units > 0.0 else 1.0
        if held < share:
            share, short_material = held, material
    return share, short_material


def supply_gap(magazine, short_material, garrison, short_trade):
    """(share in force, words for what is short or None) of a counter's magazine and garrison."""
    if magazine <= garrison and short_material:
        return magazine, "its magazine of %s is %s" % (short_material, "empty" if magazine <= 0.0 else "short")
    if short_trade:
        return garrison, "no %s garrison is present" % short_trade if garrison <= 0.0 else (
            "its %s garrison is short" % short_trade)
    return 1.0, None


def relief_kcal_per_day(handouts, days_per_year):
    """Food energy a day over the whole nation that open works hand out: `handouts` are (kilograms a year, kcal per kilogram)."""
    return sum(kilograms * kcal_per_kg for kilograms, kcal_per_kg in handouts) / days_per_year
