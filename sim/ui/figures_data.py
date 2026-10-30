"""Figures declared as data (data/ui/figures.json, plus each mod's): a declaration names the state paths it reads, so a mod
adds a figure without touching Python. The interface module collects the declarations; `figure_computer` is the code behind one."""
from sim.engine import ui_port


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


def figure_computer(spec):
    """`compute(sim)` for a figure declared as data."""
    def compute(sim):
        return {"value": read_path(sim, spec["value"]),
                **{part: _read_parts(sim, spec.get(part)) for part in ("components", "flows", "drivers")}}
    return compute
