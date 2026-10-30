"""A save cannot turn the fog of war off: a save played without fog loaded into a fogged game would show the whole tree."""
from sim.refusal import Refusal


def fog_mismatch(game_has_fog, saved_fog):
    """The refusal when a fogged game is asked to load a save played without fog, else None. `saved_fog` is None for a save that
    does not say."""
    if game_has_fog and saved_fog is False:
        return Refusal("save_fog_mismatch", "that save was played without fog of war and this "
                       "game is being played with it. A save cannot turn the "
                       "fog off; start a new game without it if that is what "
                       "you want.")
    return None
