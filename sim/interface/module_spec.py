"""The interface module's spec (sim/assembly).

It reads the declarations the engine loads from data (the mods' data/ui/commands.json, the base game's and the mods'
data/ui/figures.json) through two bridge views, and answers its own two points with them and with the tables the UI ships; a
mod's code adds commands and figures by providing to the points."""
from sim.assembly.api import LIST, ExtensionPoint, ModuleSpec, Provision, ViewSpec

from .module import Interface

MODULE_SPECS = (ModuleSpec(
	"interface", Interface,
	# constant for the game once made (the mod set is fixed at assembly), so no channel
	publishes=(ViewSpec("interface_declared", "declared"),),
	reads=("data_command_specs", "data_figure_specs"),
	extension_points=(ExtensionPoint("interface_commands", LIST),   # () -> [CommandDeclaration]
	                  ExtensionPoint("interface_figures", LIST)),   # () -> [FigureDeclaration]
	provides=(Provision("interface_commands", "provide_shipped_commands", "shipped"),
	          Provision("interface_commands", "provide_data_commands", "data"),
	          Provision("interface_figures", "provide_shipped_figures", "shipped"),
	          Provision("interface_figures", "provide_data_figures", "data")),
),)
