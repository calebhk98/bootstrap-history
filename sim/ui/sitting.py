"""What one typed sitting keeps besides the game: the routes a finished game carries in and whether the ending was shown."""
from typing import Iterable, List


class Sitting:
    """The state of one typed sitting that outlives a single game: the known-route ids carried into the next game, and
    whether the scoreboard of an ended game has been shown."""

    def __init__(self, carried_route_ids: Iterable[str] = ()) -> None:
        self.carried_route_ids: List[str] = list(carried_route_ids)
        self.said_end = False   # the scoreboard of a game that ended has been printed this sitting
