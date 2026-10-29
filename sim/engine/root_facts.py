"""Properties the `Sim` states on itself: the facts it composes with, each answering from the view or the scenario record that owns it."""
import operator


def view_fact(view_name, key=None, set_command=None):
    """Reads view `view_name` (its `key` when given); assigning sends `set_command(value)` when there is one."""
    def read(sim):
        value = sim.view(view_name)()
        return value if key is None else value[key]

    def write(sim, value):
        sim.send(set_command(value))
    return property(read, None if set_command is None else write)


def scenario_fact(path, set_command=None):
    """Reads the scenario module's record at `path`; assigning sends `set_command(value)` when there is one."""
    read = operator.attrgetter("_scenario." + path)

    def write(sim, value):
        sim.send(set_command(value))
    return property(read, None if set_command is None else write)


def horizon_end_year(sim):
    """The year the horizon ends, once a front end has set it (no attribute before)."""
    if sim._scenario.end_year is None:
        raise AttributeError("end_year")
    return sim._scenario.end_year
