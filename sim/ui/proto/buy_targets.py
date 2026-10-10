"""What `buy` can spend on: one table of canonical target, spellings and usage.

The typed parser, the `buy` dispatcher, `quote` and the help text all read
this table, so a new target is added here once.
"""

# canonical target -> (other spellings, usage line)
BUY_TARGETS = {
    "forest": (("coppice", "woodland"), "buy forest <ha>"),
    "nitre": (("nitre_bed", "nitre beds", "saltpetre"), "buy nitre <m2>"),
    "farm": (("food",), "buy farm <ha>"),
    "housing": (("houses",), "buy housing <n>"),
    "school": (("trade_school", "trade school"), "buy school <trade> <n>"),
    "material": (("stock",), "buy material <name> <tonnes>"),
    "mine": (("mines",), "buy mine <material> <tonnes_per_year>"),
    "living_stock": (("livestock", "breeding_stock"), "buy living_stock <material> <units> [<partner>]"),
    "slaves": (("people",), "buy slaves <n>"),
    "manumit": (("manumission", "free"), "buy manumit <n>"),
}

# canonical target -> (dimension, the unit the engine takes its quantity in); the player may type another unit of the dimension
TARGET_QUANTITY = {
    "forest": ("area", "hectare"),
    "nitre": ("area", "square_metre"),
    "farm": ("area", "hectare"),
    "material": ("mass", "tonne"),
    "mine": ("mass", "tonne"),
}

_CANONICAL_BY_SPELLING = {
    spelling: target
    for target, (spellings, _usage) in BUY_TARGETS.items()
    for spelling in (target,) + tuple(spellings)}


def canonical_target(word):
    """The canonical buy target a typed word names, or None."""
    return _CANONICAL_BY_SPELLING.get(str(word or "").strip().lower())


def usage_lines():
    return [usage for _spellings, usage in BUY_TARGETS.values()]


def target_names():
    return list(BUY_TARGETS)
