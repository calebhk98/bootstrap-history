"""The figure declarations of the base game and every mod (data/ui/figures.json), merged in mod load order.

A figure is declared by id with a label, unit, digits and the state paths it reads (`sim/ui/figures_data.py`
turns a declaration into a registered figure). A mod's ids are `<mod_id>:<name>`; a base id is never replaced.
The state paths are checked by the function the game hands in with `OpenInterface`.
"""
import os
from typing import Any, Dict

from sim.content.api import ModError, check_new_id, get_ordered_mods
from sim.default_civilisation import REPOSITORY_ROOT as ROOT
from sim.json_files import read_json

from .command_data import StatePathCheck

FIGURES_FILE = os.path.join("data", "ui", "figures.json")
READ_PARTS = ("components", "flows", "drivers")


def _check_figure(figure_id: str, spec: Any, path: str, check_state_path: StatePathCheck) -> None:
	if not isinstance(spec, dict) or not isinstance(spec.get("label"), str):
		raise ModError("%s: figure %s needs a string 'label'" % (path, figure_id))
	if not isinstance(spec.get("value"), str):
		raise ModError("%s: figure %s needs 'value', a state path such as 'population.total'" % (path, figure_id))
	for part in READ_PARTS:
		reads = spec.get(part)
		if reads is None or isinstance(reads, str):
			continue
		if not isinstance(reads, dict) or not all(isinstance(read, str) for read in reads.values()):
			raise ModError("%s: figure %s field %r must be a state path or {label: state path}"
						   % (path, figure_id, part))
	reads = [spec["value"]]
	for part in READ_PARTS:
		entry = spec.get(part)
		reads += [entry] if isinstance(entry, str) else list((entry or {}).values())
	for state_path in reads:
		check_state_path(state_path, "%s: figure %s" % (path, figure_id))
	if "digits" in spec and not isinstance(spec["digits"], int):
		raise ModError("%s: figure %s field 'digits' must be an integer" % (path, figure_id))


def load_figure_specs(mods_dir: str, check_state_path: StatePathCheck) -> Dict[str, Dict[str, Any]]:
	"""{figure id: declaration} from the base file, then each mod's, in load order."""
	specs: Dict[str, Dict[str, Any]] = {}
	sources = [(None, os.path.join(ROOT, FIGURES_FILE))] + [
		(manifest, os.path.join(manifest.directory, FIGURES_FILE)) for manifest in get_ordered_mods(mods_dir)]
	for manifest, path in sources:
		if not os.path.isfile(path):
			continue
		for figure_id, spec in (read_json(path).get("figures") or {}).items():
			if manifest is not None:
				check_new_id(manifest, figure_id, False, path)
			if figure_id in specs:
				raise ModError("figure %s of %s is already defined" % (figure_id, path))
			_check_figure(figure_id, spec, path, check_state_path)
			specs[figure_id] = spec
	return specs
