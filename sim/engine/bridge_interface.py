"""Bridge entries the interface module reads: the command and figure declarations the engine loads from data files."""
from . import bridge_land
from .bridge import bridge_view
from .ui_commands import load_command_specs
from .ui_data import load_figure_specs


@bridge_view("data_command_specs")
def data_command_specs(sim):
    """[CommandSpec] the installed mods declare (data/ui/commands.json), in mod load order."""
    return load_command_specs(mods_dir=bridge_land.MODS_DIR)


@bridge_view("data_figure_specs")
def data_figure_specs(sim):
    """{figure id: declaration} of the base game and the installed mods (data/ui/figures.json)."""
    return load_figure_specs(mods_dir=bridge_land.MODS_DIR)
