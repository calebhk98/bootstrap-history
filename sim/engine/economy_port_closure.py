"""Which opening prices stand: a good is priced only when it can be made at that start."""


def makeable_prices(prices, production, recipes):
    """`prices` without the goods that cannot be made at the start. A good some production entry makes is kept
    only when a recipe the society can run makes it and every input of that recipe is itself kept (a missing
    input is not free). A good no entry makes (raw, imported, found) keeps its price."""
    makers_anywhere = {good for entry_id, entry in production.items()
                       if not entry_id.startswith("_") and isinstance(entry, dict)
                       for good in (entry.get("outputs") or {})}
    kept = dict(prices)
    changed = True
    while changed:
        changed = False
        for good in sorted(kept):
            if good not in makers_anywhere:
                continue
            if not any(good in recipe.outputs and all(item in kept for item in recipe.inputs)
                       for recipe in recipes.values()):
                del kept[good]
                changed = True
    return kept
