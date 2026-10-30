"""The project order: which projects the household's hours serve first. Saved with the game, changed by three commands."""
from typing import Tuple

from . import order_rules
from .commands import PutProjectFirst, ReorderProjects, RestoreProjectOrder

ORDER = "order"        # the project order changed


class ProjectOrder:
	def project_order(self) -> Tuple[str, ...]:
		return tuple(self.world.order)

	def apply_put_project_first(self, command: PutProjectFirst) -> None:
		self.world.order = order_rules.put_first(self.world.order, command.node_id)
		self.bump(ORDER)

	def apply_reorder_projects(self, command: ReorderProjects) -> None:
		self.world.order = order_rules.place_sequence(self.world.order, self.seat.active, command.node_ids)
		self.bump(ORDER)

	def apply_restore_project_order(self, command: RestoreProjectOrder) -> None:
		self.world.order = list(command.order)
		self.bump(ORDER)
