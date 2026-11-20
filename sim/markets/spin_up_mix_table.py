"""What the spin-up's years changed in the economy's mix, for `spin-up-trace --stages`: the first year, the trough of the
first stage and the last year side by side, read from each replayed row's "mix" (sim/economy/spin_up_mix.py). Pure."""


def trough(rows):
    """The first-stage row with the least real output (the earliest of equals); None when no first-stage row states one."""
    first = [row for row in rows if row.get("stage") == "first" and row.get("real_output") is not None]
    return min(first, key=lambda row: row["real_output"]) if first else None


def marked_rows(rows):
    """[(label, row)] for the first year, the trough (`trough`, left out when it is the first or the last year) and the
    last year; nothing for no rows."""
    if not rows:
        return []
    marked = [("first year", rows[0])]
    lowest = trough(rows)
    if lowest is not None and lowest is not rows[0] and lowest is not rows[-1]:
        marked.append(("trough (%s %d)" % (lowest["stage"], lowest["year"]), lowest))
    if rows[-1] is not rows[0]:
        marked.append(("last year", rows[-1]))
    return marked


def largest_first(mixes, name, count, size=lambda value: value):
    """[(key, [its value in each of `mixes`, None where a mix lacks it])] for the `count` keys of the mix figure `name`
    whose `size` is largest in any of the mixes, largest first."""
    keys = sorted({key for mix in mixes for key in mix[name]})
    keys.sort(key=lambda key: -max(size(mix[name][key]) for mix in mixes if key in mix[name]))
    return [(key, [mix[name].get(key) for mix in mixes]) for key in keys[:count]]


def recipe_shares(made):
    """{good: {recipe: its share of the good made}} from {good: {recipe: quantity}}; a good nothing made is left out."""
    shares = {}
    for good, by_recipe in made.items():
        total = sum(by_recipe.values())
        if total > 0.0:
            shares[good] = {recipe_id: quantity / total for recipe_id, quantity in by_recipe.items()}
    return shares


def recipes_that_moved(mixes, count, least=0.1):
    """[(good, [(recipe, [its share of the good in each of `mixes`, None where the good was not made])])] for the `count`
    goods several recipes make whose split moved most between the mixes (the largest change of one recipe's share, at
    least `least`), most moved first; a good's recipes by their largest share."""
    shares = [recipe_shares(mix["made_by_recipe"]) for mix in mixes]
    moved = {}
    for good in sorted({good for each in shares for good in each}):
        recipes = sorted({recipe_id for each in shares for recipe_id in each.get(good, {})})
        spans = []
        for recipe_id in recipes:
            stated = [each[good].get(recipe_id, 0.0) for each in shares if good in each]
            spans.append(max(stated) - min(stated))
        if spans and max(spans) >= least:
            moved[good] = (max(spans), recipes)
    table = []
    for good in sorted(moved, key=lambda good: (-moved[good][0], good))[:count]:
        rows = [(recipe_id, [each[good].get(recipe_id, 0.0) if good in each else None for each in shares]) for recipe_id in moved[good][1]]
        rows.sort(key=lambda row: -max(value or 0.0 for value in row[1]))
        table.append((good, rows))
    return table
