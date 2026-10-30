"""The assembly's own module: the seat registry's facts, published as views like any module's, and the root operations modules ask
for as commands (root_commands.py), so that readers and askers show in the graph."""
from typing import Any, List

from .module import Module
from .root_commands import AddSeat, MoveSeat, RepriceTree
from .spec import KEYED, ModuleSpec, ViewSpec

FRAMEWORK_ID = "assembly"


class Framework(Module):
	assembly: Any = None   # set by `assemble`

	def view_registered_seats(self) -> List[str]:
		"""The ids of the seats in the registry, in the order they joined."""
		return list(self.assembly.seat_records())

	def view_seat_holds(self, seat_id: str) -> List[str]:
		"""What the seat's record holds that a handover to it would overwrite, as the game's rule says."""
		return self.assembly.holds_rule(self.assembly.seat_records()[seat_id])


	def apply_add_seat(self, command: AddSeat) -> Any:
		return self.assembly.add_seat(command.seat_id, command.template)

	def apply_move_seat(self, command: MoveSeat) -> Any:
		return self.assembly.move_seat(command.from_id, command.to_id)

	def apply_reprice_tree(self, command: RepriceTree) -> None:
		self.assembly.reprice_tree()


def framework_spec() -> ModuleSpec:
	return ModuleSpec(FRAMEWORK_ID, Framework, publishes=(
		ViewSpec("registered_seats", "view_registered_seats", cached=False),
		ViewSpec("seat_holds", "view_seat_holds", kind=KEYED, cached=False)),
		applies=((AddSeat, "apply_add_seat"), (MoveSeat, "apply_move_seat"), (RepriceTree, "apply_reprice_tree")))
