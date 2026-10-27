"""The ways' rules as plain functions: what a way costs and how long it takes, why a start is refused, and which ways open in a year."""


def crew_hours_a_year(found_people, crew_hours_per_year, crew_people):
    """The hours a year the people a search found work: each of the crew the work calls for gives an equal share."""
    hours_each = crew_hours_per_year / crew_people
    return found_people * hours_each


def way_money(labour_hours, hourly_rate, material_bills):
    """The labour at the hour's rate, then each material's bill added in the order given."""
    money = labour_hours * hourly_rate
    for bill in material_bills:
        money += bill
    return money


def way_years(labour_hours, crew_hours):
    """The years a crew working `crew_hours` a year takes over `labour_hours`."""
    return labour_hours / crew_hours


def where(tile_a, tile_b):
    """Where a way stands, for a sentence: on one tile (a port) or between two."""
    return "on %s" % tile_a if tile_a == tile_b else "between %s and %s" % (tile_a, tile_b)


def not_held_refusal(held_tiles, tile_a, tile_b):
    """The sentence when either tile is not one the nation holds, else None."""
    if tile_a not in held_tiles or tile_b not in held_tiles:
        return "both tiles must be ones your nation holds."
    return None


def start_refusal(way, place, quote, known, standing, being_built):
    """The sentence when a quoted way cannot be started: its technology unknown, already standing or already being built, else None."""
    if quote["node"] and quote["node"] not in known:
        return "your people do not know how to build a %s yet (%s)." % (way, quote["node"])
    if standing:
        return "a %s already stands %s." % (way, place)
    if being_built:
        return "a %s %s is already being built." % (way, place)
    return None


def pending_way(year, quote):
    """The record of a way paid for and being built."""
    return {"due": year + quote["years"], "trade": quote["trade"], "crew_hours": quote["crew_hours"],
            "engineered": quote["engineered"], "pressed": year}


def open_ways(pending, built_ways, year):
    """Open, in place, the ways whose build time has passed, in key then way order; the crews of those still building lean on
    their trade again once a year. Answers the labour calls to make, in order: ("release" or "press", trade, hours)."""
    calls = []
    for key in sorted(pending):
        for way in sorted(pending[key]):
            build = pending[key][way]
            if build["due"] <= year:
                built = built_ways.setdefault(key, {})
                built[way] = True
                if build["engineered"]:
                    built["engineered"] = True
                calls.append(("release", build["trade"], build["crew_hours"]))
                del pending[key][way]
            elif build["pressed"] < year:
                calls.append(("press", build["trade"], build["crew_hours"]))
                build["pressed"] = year
        if not pending[key]:
            del pending[key]
    return calls
