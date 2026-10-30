"""Which state paths a data file (a figure, a `read` command, a policy condition) may read."""
from sim.content.api import ModError
from . import state_paths
from .readable import is_readable


def check_state_path(state_path: str, where: str) -> None:
    """A state path reads only: no step starts with '_', and its first step, if a method of the Sim, is marked readable."""
    from .core import Sim
    steps = state_path.split(".")
    if any(not step or step.startswith("_") for step in steps):
        raise ModError("%s: state path %r has a private or empty step" % (where, state_path))
    if state_paths.declared(steps[0]):
        return
    first = Sim.__dict__.get(steps[0]) or getattr(Sim, steps[0], None)
    if callable(first) and not is_readable(first):
        raise ModError("%s: state path %r calls %s, which is not marked readable (only attributes, properties "
                       "and @readable methods may be read)" % (where, state_path, steps[0]))
