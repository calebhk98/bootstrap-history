"""The ways a capital good can be built: its own build bill first, then its `build_alternatives` in order
(data/production/_SCHEMA.md). A plant is built the first way whose materials the society has. Nothing here
names a material or a recipe."""


def builds(capital_good):
    """[(build_materials, build_labour_hours, service_life_years)] in preference order."""
    life = capital_good.get("service_life_years")
    ways = [(capital_good.get("build_materials") or {}, capital_good.get("build_labour_hours") or {}, life)]
    for alternative in capital_good.get("build_alternatives") or ():
        ways.append((alternative.get("build_materials") or {}, alternative.get("build_labour_hours") or {},
                     alternative.get("service_life_years", life)))
    return ways


def first_buildable(capital_good, priced):
    """The first build whose materials are all in `priced`, or None."""
    return next((way for way in builds(capital_good) if all(material in priced for material in way[0])), None)


def materials_needed(capital_good, resolved):
    """The materials a capital good depends on given what is `resolved`: those of the first build all of whose
    materials are resolved, else of the build with the fewest still missing (the preferred one on a tie)."""
    ways = builds(capital_good)
    best = min(ways, key=lambda way: sum(1 for material in way[0] if material not in resolved))
    return best[0].keys()
