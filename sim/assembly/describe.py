"""What an assembly is made of, as data: the record a save keeps, and the dependency listing a person reads."""
from typing import Any, Dict, List

from .assemble import Assembly


def record(assembly: Assembly) -> Dict[str, Any]:
	"""Everything that decides which code runs: two games with equal records run the same modules."""
	applied = assembly.applied
	modules = {}
	for module_id, spec in sorted(applied.specs.items()):
		implementation = spec.implementation
		modules[module_id] = {
			"implementation": "%s.%s" % (implementation.__module__, implementation.__qualname__),
			"origin": applied.origin[module_id],
			"replaced_by": applied.replaced_by.get(module_id),
			"layers": [[mod_id, "%s.%s" % (layer.__module__, layer.__qualname__)] for mod_id, layer in applied.layers.get(module_id, [])],
		}
	return {
		"modules": modules,
		"removed": dict(sorted(applied.removed_by.items())),
		"adjusters": {view: [mod_id for mod_id, _function, _reads in entries] for view, entries in sorted(applied.adjusters.items())},
		"provided": {point: [mod_id for mod_id, _function in entries] for point, entries in sorted(applied.provided.items())},
		"withdrawn": dict(sorted(applied.withdrawn.items())),
	}


def dependency_lines(assembly: Assembly) -> List[str]:
	"""One block per module: what it publishes, applies, reads and sends, and the overrides that rely on internals."""
	lines = []
	for module_id, spec in sorted(assembly.applied.specs.items()):
		lines.append(module_id)
		lines.append("  publishes: %s" % ", ".join(view.name for view in spec.publishes))
		lines.append("  applies: %s" % ", ".join(command.__name__ for command, _handler in spec.applies))
		lines.append("  reads: %s" % ", ".join("%s (%s)" % (name, assembly.provider_of(name)) for name in spec.reads))
		if spec.optional_reads:
			lines.append("  reads if present: %s" % ", ".join("%s (%s)" % (name, assembly.provider_of(name) or "absent") for name in spec.optional_reads))
		lines.append("  sends: %s" % ", ".join("%s (%s)" % (command.__name__, assembly.command_owner[command]) for command in spec.sends))
		for mod_id, method in assembly.unstable.get(module_id, []):
			lines.append("  unstable: mod %s overrides %s, which the module does not declare" % (mod_id, method))
	return lines
