"""What one typed sitting keeps besides the game: the routes a finished game carries in and whether the ending was shown."""
from typing import Iterable, List


class Sitting:
	def __init__(self, carried_route_ids: Iterable[str] = ()) -> None:
		self.carried_route_ids: List[str] = list(carried_route_ids)
		self.said_end = False   # the scoreboard of a game that ended has been printed this sitting
