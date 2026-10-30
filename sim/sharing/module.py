"""The sharing module: answers that a view of the world asks many times in a turn, computed once while the world they read
is unchanged. An actor's turn prices the same projects and the same trades once per firm, though the answer is a fact about
the world, not about the actor asking. A view that asks many questions opens a scope (`shared_answers`); outside a scope
nothing is shared, except an answer marked standalone, which the module keeps in one table of its own (never saved)."""
import contextlib
from typing import Any, Callable, Dict, Iterator, Optional

from sim.assembly.api import Module

from . import rules, stamp


class Sharing(Module):

	def setup(self) -> None:
		self._scope: Optional[Dict[str, Any]] = None
		self._standalone_scope: Dict[str, Any] = {}

	@contextlib.contextmanager
	def shared_answers(self, table: Dict[str, Any]) -> Iterator[None]:
		"""A context in which the answers asked of the world are shared through `table` (a dict the view owns)."""
		opened, self._scope = self._scope, table
		try:
			yield
		finally:
			self._scope = opened

	def shared_answer(self, key: Any, inputs: Any, compute: Callable[[], Any], standalone: bool = False) -> Any:
		"""`compute()` reused while the world stamp holds and `inputs` (what the answer reads that the stamp does not) equal
		those it was computed with."""
		if self._scope is not None:
			return rules.memoised(self._scope, stamp.view_stamp(self.needs), key, inputs, compute)
		if not standalone:
			return compute()
		return rules.memoised(self._standalone_scope, stamp.standalone_stamp(self.needs), key, inputs, compute)

	def shared_bill(self, node_id: str, compute: Callable[[], Any]) -> Any:
		"""The node's material bill, reused while the world stamp and the node's stock hold."""
		if self._scope is None:
			return compute()
		stock = tuple(self.needs.goods_stock[commodity] for commodity in self._bill_commodities(node_id))
		return self.shared_answer(("bill", node_id), stock, compute)

	def _bill_commodities(self, node_id: str) -> tuple:
		"""The commodities a node's bill draws on; these change only with the done set."""
		needs = self.needs
		return needs.done_memo("bill_keys", node_id, lambda: tuple(sorted({
			needs.material_pool[material][0] for material in needs.project_material_needs[node_id]})))
