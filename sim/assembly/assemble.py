"""Build one game's modules: bind every view, point and command to one owner, check every read, hand out needs."""
from typing import Callable, Dict, List, Optional, Sequence, Tuple

from .clock import Clock
from .errors import AssemblyError
from .module import Module
from .needs import Needs, Point
from .operations import Applied, apply_all
from .spec import ModuleSpec, Operations, declared_methods, point_names, view_names
from .views import View


class Assembly:
	def __init__(self, applied: Applied, clock: Clock, removed_views: Dict[str, Tuple[str, ...]],
	             removed_commands: Dict[type, str]):
		self.applied = applied
		self.clock = clock
		self.removed_views = removed_views                        # removed module id -> the views and points it published
		self.removed_commands = removed_commands                  # command class -> the removed module that applied it
		self.modules: Dict[str, Module] = {}
		self.views: Dict[str, View] = {}
		self.points: Dict[str, Point] = {}
		self.view_owner: Dict[str, str] = {}
		self.point_owner: Dict[str, str] = {}
		self.command_owner: Dict[type, str] = {}
		self.handlers: Dict[type, Callable] = {}
		self.unstable: Dict[str, List[Tuple[str, str]]] = {}     # module id -> (mod id, method) overrides outside the spec
		self._phase_handlers: Optional[Dict[str, Callable]] = None

	def provider_of(self, name: str) -> Optional[str]:
		return self.view_owner.get(name) or self.point_owner.get(name)

	def phase_handler(self, name: str) -> Callable:
		"""The bound method that runs the year's phase `name`; KeyError when no module runs it."""
		if self._phase_handlers is None:
			self._phase_handlers = self.phase_handlers()
		return self._phase_handlers[name]

	def phase_handlers(self) -> Dict[str, Callable]:
		handlers: Dict[str, Callable] = {}
		owners: Dict[str, str] = {}
		for module_id, spec in self.applied.specs.items():
			for hook in spec.phases:
				if hook.name in handlers:
					raise AssemblyError("modules %s and %s both run the phase %s" % (owners[hook.name], module_id, hook.name))
				handlers[hook.name] = getattr(self.modules[module_id], hook.method)
				owners[hook.name] = module_id
		return handlers


def _bind_names(assembly: Assembly) -> None:
	for module_id, spec in assembly.applied.specs.items():
		for view in spec.publishes:
			other = assembly.provider_of(view.name)
			if other is not None:
				raise AssemblyError("modules %s and %s both publish %s" % (other, module_id, view.name))
			assembly.view_owner[view.name] = module_id
		for point in spec.extension_points:
			other = assembly.provider_of(point.name)
			if other is not None:
				raise AssemblyError("modules %s and %s both declare %s" % (other, module_id, point.name))
			assembly.point_owner[point.name] = module_id
		for command, _handler in spec.applies:
			other = assembly.command_owner.get(command)
			if other is not None:
				raise AssemblyError("modules %s and %s both apply %s" % (other, module_id, command.__name__))
			assembly.command_owner[command] = module_id


def _removal_note(assembly: Assembly, name: str = "", command: Optional[type] = None) -> str:
	if command is not None:
		removed = [assembly.removed_commands[command]] if command in assembly.removed_commands else []
	else:
		removed = [module_id for module_id, names in assembly.removed_views.items() if name in names]
	if not removed:
		return ""
	return " (module %s provided it; mod %s removed it)" % (removed[0], assembly.applied.removed_by[removed[0]])


def _missing(assembly: Assembly, reader: str, name: str) -> AssemblyError:
	return AssemblyError("%s reads %s, which no module provides%s" % (reader, name, _removal_note(assembly, name)))


def _check_reads(assembly: Assembly) -> None:
	for module_id, spec in assembly.applied.specs.items():
		for name in spec.reads:
			if assembly.provider_of(name) is None:
				raise _missing(assembly, "module %s" % module_id, name)
		for command in spec.sends:
			if command not in assembly.command_owner:
				raise AssemblyError("module %s sends %s, which no module applies%s" % (
					module_id, command.__name__, _removal_note(assembly, command=command)))
		own = {view.name for view in spec.publishes}
		for view in spec.publishes:
			for name in view.inputs:
				if name not in own and name not in spec.reads and name not in spec.optional_reads:
					raise AssemblyError("view %s of module %s depends on %s, which the module does not read" % (view.name, module_id, name))
				if assembly.view_owner.get(name) is None and name not in spec.optional_reads:
					raise _missing(assembly, "view %s of module %s" % (view.name, module_id), name)
	for view, entries in assembly.applied.adjusters.items():
		for mod_id, _function, reads in entries:
			if view not in assembly.view_owner:
				raise AssemblyError("mod %s adjusts the view %s, which no module publishes%s" % (mod_id, view, _removal_note(assembly, view)))
			for name in reads:
				if name in assembly.point_owner:
					raise AssemblyError("mod %s's adjuster of %s reads %s, an extension point; an adjuster reads views only" % (mod_id, view, name))
				if name not in assembly.view_owner:
					raise _missing(assembly, "mod %s's adjuster of %s" % (mod_id, view), name)
	for point, entries in assembly.applied.provided.items():
		if point not in assembly.point_owner:
			raise AssemblyError("mod %s provides to %s, which no module declares%s" % (entries[0][0], point, _removal_note(assembly, point)))


def _check_view_cycles(assembly: Assembly) -> None:
	"""Declared view inputs must not form a cycle: a view's freshness is the freshness of its inputs."""
	inputs = {view.name: [name for name in view.inputs if name in assembly.view_owner]
	          for spec in assembly.applied.specs.values() for view in spec.publishes}
	state: Dict[str, int] = {}                      # 1 while on the walk, 2 when finished

	def walk(name: str, trail: List[str]) -> None:
		if state.get(name) == 2:
			return
		if state.get(name) == 1:
			cycle = trail[trail.index(name):] + [name]
			raise AssemblyError("view inputs form a cycle: %s" % " -> ".join(cycle))
		state[name] = 1
		for following in inputs.get(name, []):
			walk(following, trail + [name])
		state[name] = 2
	for name in sorted(inputs):
		walk(name, [])


def _implementation(assembly: Assembly, module_id: str, spec: ModuleSpec) -> type:
	if not (isinstance(spec.implementation, type) and issubclass(spec.implementation, Module)):
		raise AssemblyError("module %s: its implementation must derive from sim.assembly.api.Module" % module_id)
	built = spec.implementation
	declared = set(declared_methods(spec))
	for mod_id, layer in assembly.applied.layers.get(module_id, []):
		for name, value in vars(layer).items():
			if callable(value) and not name.startswith("__") and name not in declared:
				assembly.unstable.setdefault(module_id, []).append((mod_id, name))
		built = type("%s+%s" % (built.__name__, layer.__name__), (layer, built), {})
	missing = [name for name in declared if not callable(getattr(built, name, None))]
	if missing:
		raise AssemblyError("module %s declares %s but its implementation has no such method" % (module_id, ", ".join(sorted(missing))))
	return built


def _instantiate(assembly: Assembly) -> None:
	for module_id, spec in assembly.applied.specs.items():
		instance = _implementation(assembly, module_id, spec)()
		instance.module_id = module_id
		instance.clock = assembly.clock
		assembly.modules[module_id] = instance
	for module_id, spec in assembly.applied.specs.items():
		for view_spec in spec.publishes:
			assembly.views[view_spec.name] = View(view_spec, module_id, getattr(assembly.modules[module_id], view_spec.compute), assembly.clock)
		for point_spec in spec.extension_points:
			assembly.points[point_spec.name] = Point(point_spec.name, point_spec.combine)
		for command, handler in spec.applies:
			assembly.handlers[command] = getattr(assembly.modules[module_id], handler)


def _needs_for(assembly: Assembly, module_id: str, names: Sequence[str], optional: Sequence[str], sends: Sequence[type]) -> Needs:
	needs = Needs(module_id, assembly.handlers, frozenset(sends))
	for name in list(names) + list(optional):
		setattr(needs, name, assembly.views.get(name) or assembly.points.get(name))
	return needs


def _wire(assembly: Assembly) -> None:
	for module_id, spec in assembly.applied.specs.items():
		own = [view.name for view in spec.publishes] + [point.name for point in spec.extension_points]
		assembly.modules[module_id].needs = _needs_for(assembly, module_id, list(spec.reads) + own, spec.optional_reads, spec.sends)
	for name, view in assembly.views.items():
		view.inputs = [assembly.views[input_name] for input_name in view.spec.inputs if input_name in assembly.views]
		for _mod_id, function, reads in assembly.applied.adjusters.get(name, []):
			needs = _needs_for(assembly, "an adjuster of %s" % name, reads, (), ())
			view.adjusters.append((function, needs, [assembly.views[read] for read in reads]))
	for name, entries in assembly.applied.provided.items():
		assembly.points[name].providers.extend(function for _mod_id, function in entries)


def assemble(shipped: Sequence[ModuleSpec], operations: Sequence[Operations] = (),
             related: Optional[Callable[[str, str], bool]] = None, shadow_every: int = 0) -> Assembly:
	"""The game's modules: the shipped set changed by each mod's operations in load order; AssemblyError names the parties."""
	every_spec = {spec.module_id: spec for spec in shipped}
	for entry in operations:
		every_spec.update({spec.module_id: spec for spec in entry.added})
	applied = apply_all(shipped, operations, related)
	removed = {module_id: every_spec[module_id] for module_id in applied.removed_by if module_id in every_spec}
	assembly = Assembly(applied, Clock(shadow_every), {module_id: view_names(spec) + point_names(spec) for module_id, spec in removed.items()},
	                    {command: module_id for module_id, spec in removed.items() for command, _handler in spec.applies})
	_bind_names(assembly)
	_check_reads(assembly)
	_check_view_cycles(assembly)
	_instantiate(assembly)
	_wire(assembly)
	for module in assembly.modules.values():
		module.setup()
	return assembly
