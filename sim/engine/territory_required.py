"""A civilisation must hold land: the agent economy runs its markets on the tiles a civilisation holds."""


def require_territory(civ, held_tiles):
    """Refuse a civilisation that holds no tiles, naming where its starting claim is declared."""
    if not held_tiles:
        raise ValueError("civilisation %r holds no tiles: the agent economy needs a territory to run its markets on; "
                         "name its starting claim in `home_tiles`" % (civ.get("id"),))
