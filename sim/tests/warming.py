"""Which game starts the runner builds before the topics it runs, so their spin-ups are on disk before a topic's
time limit starts. A topic names the civilisations it builds with a module-level `CIVILISATIONS` tuple (empty for a
topic that builds no game); a topic that says nothing is taken to build the default start. A start a topic builds
without declaring is built by that topic, behind the cache's per-key lock (`solve_cache.cached_json`)."""

DEFAULT_CIVILISATION = "rome_100ad"


def civilisations_to_warm(slugs, quick_slugs, declared):
    """Sorted civilisation ids the topics `slugs` need built; quick topics build no game."""
    needed = set()
    for slug in slugs:
        if slug in quick_slugs:
            continue
        needed.update(declared.get(slug, (DEFAULT_CIVILISATION,)))
    return sorted(needed)
