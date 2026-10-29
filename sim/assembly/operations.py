"""Apply the mods' operations to the shipped module set, in mod load order, and say who did what."""
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

from .errors import AssemblyError
from .spec import ModuleSpec, Operations, handler_of, point_names, view_names

SHIPPED = "shipped"
SEPARATOR = ":"


def namespaced(mod_id: str, name: str) -> bool:
	return name.startswith(mod_id + SEPARATOR)


def _check_replacement(old: ModuleSpec, new: ModuleSpec, mod_id: str) -> None:
	missing = [name for name in view_names(old) if name not in view_names(new)]
	missing += [command.__name__ for command in handler_of(old) if command not in handler_of(new)]
	missing += [name for name in point_names(old) if name not in point_names(new)]
	if missing:
		raise AssemblyError("mod %s replaces module %s but does not provide %s" % (mod_id, old.module_id, ", ".join(missing)))


class Applied:
	"""The module set after every mod's operations, with the origin of each change."""

	def __init__(self, shipped: Sequence[ModuleSpec]):
		self.specs: Dict[str, ModuleSpec] = {}
		self.origin: Dict[str, str] = {}             # module id -> "shipped" or the mod that added it
		self.replaced_by: Dict[str, str] = {}
		self.removed_by: Dict[str, str] = {}
		self.layers: Dict[str, List[Tuple[str, type]]] = {}
		self.adjusters: Dict[str, List[Tuple[str, Callable, Tuple[str, ...]]]] = {}
		self.provided: Dict[str, List[Tuple[str, Callable]]] = {}
		self.withdrawn: Dict[str, str] = {}          # "<module_id>.<name>" -> the mod that withdrew it
		self.phases: List[Any] = []                  # the mods' year phases, in mod load order
		self.kernels: Dict[str, Tuple[str, Callable]] = {}   # kernel name -> (the mod replacing it, its function)
		self.mods: List[str] = []                            # every mod with operations, in load order
		self.mod_reads: Dict[str, Tuple[str, ...]] = {}      # mod id -> the views its code declared it reads
		self.mod_sends: Dict[str, Tuple[type, ...]] = {}     # mod id -> the command classes its code declared it sends
		for spec in shipped:
			if spec.module_id in self.specs:
				raise AssemblyError("two shipped modules are both called %s" % spec.module_id)
			self.specs[spec.module_id] = spec
			self.origin[spec.module_id] = SHIPPED

	def _existing(self, module_id: str, mod_id: str, verb: str) -> ModuleSpec:
		if module_id in self.removed_by:
			raise AssemblyError("mod %s %s module %s, which mod %s removed" % (mod_id, verb, module_id, self.removed_by[module_id]))
		if module_id not in self.specs:
			raise AssemblyError("mod %s %s module %s, which does not exist" % (mod_id, verb, module_id))
		return self.specs[module_id]

	def apply(self, operations: Operations, related: Callable[[str, str], bool]) -> None:
		mod_id = operations.mod_id
		self.mods.append(mod_id)
		for spec in operations.added:
			if not namespaced(mod_id, spec.module_id):
				raise AssemblyError("mod %s adds module %s; a mod's module is named %s%s<name>" % (mod_id, spec.module_id, mod_id, SEPARATOR))
			if spec.module_id in self.specs:
				raise AssemblyError("mod %s adds module %s twice" % (mod_id, spec.module_id))
			self.specs[spec.module_id] = spec
			self.origin[spec.module_id] = mod_id
		for module_id, spec in operations.replaced.items():
			old = self._existing(module_id, mod_id, "replaces")
			earlier = self.replaced_by.get(module_id)
			if earlier is not None and earlier != mod_id and not related(earlier, mod_id):
				raise AssemblyError("mods %s and %s both replace module %s; make one depend on the other to choose" % (earlier, mod_id, module_id))
			if spec.module_id != module_id:
				raise AssemblyError("mod %s replaces module %s with a spec named %s" % (mod_id, module_id, spec.module_id))
			_check_replacement(old, spec, mod_id)
			self.specs[module_id] = spec
			self.replaced_by[module_id] = mod_id
			self.layers.pop(module_id, None)             # layers were written against the implementation it replaces
		for module_id in operations.removed:
			self._existing(module_id, mod_id, "removes")
			del self.specs[module_id]
			self.removed_by[module_id] = mod_id
			self.layers.pop(module_id, None)
		for module_id, classes in operations.layers.items():
			self._existing(module_id, mod_id, "extends")
			self.layers.setdefault(module_id, []).extend((mod_id, layer) for layer in classes)
		for view, entries in operations.adjusters.items():
			self.adjusters.setdefault(view, []).extend((mod_id, function, reads) for function, reads in entries)
		for point, functions in operations.provided.items():
			self.provided.setdefault(point, []).extend((mod_id, function) for function in functions)
		for name in operations.withdrawn:
			self.withdrawn[name] = mod_id
		self.phases.extend(operations.phases)
		if operations.reads or operations.sends:
			self.mod_reads[mod_id], self.mod_sends[mod_id] = tuple(operations.reads), tuple(operations.sends)
		for name, function in operations.kernels.items():
			if name in self.kernels:
				raise AssemblyError("mods %s and %s both replace the kernel %s" % (self.kernels[name][0], mod_id, name))
			self.kernels[name] = (mod_id, function)


def apply_all(shipped: Sequence[ModuleSpec], operations: Sequence[Operations],
              related: Optional[Callable[[str, str], bool]] = None) -> Applied:
	applied = Applied(shipped)
	for entry in operations:
		applied.apply(entry, related or (lambda _first, _second: False))
	return applied
