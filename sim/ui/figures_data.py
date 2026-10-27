"""Figures declared as data (data/ui/figures.json, plus each mod's): a declaration names the state paths it reads
and becomes a registered figure, so a mod adds a figure without touching Python."""
from sim.engine import ui_port
from .figures import DEFAULT_DIGITS, FIGURES, register_figure

DATA_FIGURE_IDS = set()


def read_path(sim, path):
    """Follow a dotted path from the sim: attributes, then dict keys; anything callable is called."""
    steps = path.split(".")
    value = sim
    if ui_port.state_path_declared(steps[0]):
        value, steps = ui_port.state_path_root(sim, steps[0]), steps[1:]
    for step in steps:
        value = value[step] if isinstance(value, dict) else getattr(value, step)
        if callable(value):
            if not ui_port.is_readable(value):
                raise ValueError("state path %r reaches %r, which is not marked readable" % (path, step))
            value = value()
    return value


def _read_parts(sim, reads):
    if reads is None:
        return None
    if isinstance(reads, str):
        return dict(read_path(sim, reads))
    return {name: read_path(sim, path) for name, path in reads.items()}


def _computer(spec):
    def compute(sim):
        return {"value": read_path(sim, spec["value"]),
                **{part: _read_parts(sim, spec.get(part)) for part in ("components", "flows", "drivers")}}
    return compute


def register_data_figures(mods_dir=None):
    """(Re)register every declared figure; the ones a previous call registered are dropped first."""
    for figure_id in DATA_FIGURE_IDS:
        FIGURES.pop(figure_id, None)
    DATA_FIGURE_IDS.clear()
    for figure_id, spec in ui_port.load_figure_specs(mods_dir=mods_dir).items():
        register_figure(figure_id, spec["label"], spec.get("unit", ""), spec.get("digits", DEFAULT_DIGITS),
                        _computer(spec))
        DATA_FIGURE_IDS.add(figure_id)
