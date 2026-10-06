"""The figure declarations of the base game and every mod (data/ui/figures.json), merged in mod load order.

A figure is declared by id with a label, unit, digits and the state paths it reads (`sim/ui/figures_data.py`
turns a declaration into a registered figure). A mod's ids are `<mod_id>:<name>`; a base id is never replaced.
"""
import os
from typing import Any, Dict, Optional

from sim.json_files import read_json

from .mods import get_ordered_mods
from .mods_base import ModError
from .mods_ids import check_new_id
from .readable import is_readable
from .tree_source import ROOT

FIGURES_FILE = os.path.join("data", "ui", "figures.json")
READ_PARTS = ("components", "flows", "drivers")


def check_state_path(state_path: str, where: str) -> None:
    """A state path reads only: no step starts with '_', and its first step, if a method of the Sim, is marked readable."""
    from .core import Sim
    steps = state_path.split(".")
    if any(not step or step.startswith("_") for step in steps):
        raise ModError("%s: state path %r has a private or empty step" % (where, state_path))
    first = Sim.__dict__.get(steps[0]) or getattr(Sim, steps[0], None)
    if callable(first) and not is_readable(first):
        raise ModError("%s: state path %r calls %s, which is not marked readable (only attributes, properties "
                       "and @readable methods may be read)" % (where, state_path, steps[0]))


def _check_figure(figure_id: str, spec: Any, path: str) -> None:
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


def load_figure_specs(root: str = ROOT, mods_dir: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
    """{figure id: declaration} from the base file, then each mod's, in load order."""
    mods_dir = mods_dir or os.path.join(root, "mods")
    specs: Dict[str, Dict[str, Any]] = {}
    sources = [(None, os.path.join(root, FIGURES_FILE))] + [
        (manifest, os.path.join(manifest.directory, FIGURES_FILE)) for manifest in get_ordered_mods(mods_dir)]
    for manifest, path in sources:
        if not os.path.isfile(path):
            continue
        for figure_id, spec in (read_json(path).get("figures") or {}).items():
            if manifest is not None:
                check_new_id(manifest, figure_id, False, path)
            if figure_id in specs:
                raise ModError("figure %s of %s is already defined" % (figure_id, path))
            _check_figure(figure_id, spec, path)
            specs[figure_id] = spec
    return specs
