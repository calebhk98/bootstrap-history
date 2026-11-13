"""Which game starts the runner builds before the topics it runs, so their spin-ups are on disk before a topic's
time limit starts. A topic names the civilisations it builds with a module-level `CIVILISATIONS` tuple (empty for a
topic that builds no game); a topic that says nothing may build any start, so every civilisation is warmed for it."""

DEFAULT_CIVILISATION = "rome_100ad"


def civilisations_to_warm(slugs, quick_slugs, declared, every_civilisation):
    """Sorted civilisation ids the topics `slugs` need built; quick topics build no game, and an undeclared topic
    needs `every_civilisation`."""
    needed = set()
    for slug in slugs:
        if slug in quick_slugs:
            continue
        needed.update(declared.get(slug, every_civilisation))
    return sorted(needed)
