"""The interface module: which commands and figures a game offers, from the game itself and from its mods.

Four providers answer its two extension points: the shipped commands and figures (the tables sim/ui fills when it loads),
and the data the installed mods declare. A mod's code adds its own by providing to the points. The merged answer is made once
per game, on first use, since it asks sim/ui for the code behind each declaration."""
from typing import List, Optional

from sim.assembly.api import Module

from .declarations import PATCH, POLICY, SHIPPED, CommandDeclaration, Declared, FigureDeclaration
from .rules import SHIPPED_OWNER, declare, entry_fields


class Interface(Module):

	_declared: Optional[Declared] = None

	def declared(self) -> Declared:
		"""The game's commands and figures; a word or figure name declared twice is an error naming both owners."""
		if self._declared is None:
			self._declared = declare(self.needs.interface_commands(), self.needs.interface_figures())
		return self._declared

	def provide_shipped_commands(self) -> List[CommandDeclaration]:
		from sim.ui.api import shipped_commands
		return [CommandDeclaration(SHIPPED_OWNER, entry["name"], SHIPPED, entry, entry["handler"]) for entry in shipped_commands()]

	def provide_data_commands(self) -> List[CommandDeclaration]:
		"""The commands, patches and policies the installed mods declare in data/ui/commands.json."""
		from sim.ui.api import data_command_handler
		found: List[CommandDeclaration] = []
		for declaration in self.needs.data_command_specs():
			spec, name = declaration.spec, declaration.name
			if spec.get("override") is True or spec.get("remove") is True:
				found.append(CommandDeclaration(declaration.mod_id, name, PATCH, spec=spec))
			elif spec["kind"] == POLICY:
				found.append(CommandDeclaration(declaration.mod_id, name, POLICY, spec=spec))
			else:
				found.append(CommandDeclaration(declaration.mod_id, name, spec["kind"], entry_fields(spec, name),
				                                data_command_handler(spec["kind"], name, spec), spec))
		return found

	def provide_shipped_figures(self) -> List[FigureDeclaration]:
		from sim.ui.api import shipped_figures
		return [FigureDeclaration(SHIPPED_OWNER, entry["name"], entry["label"], entry["unit"], entry["digits"], entry["compute"],
		                          entry["since"]) for entry in shipped_figures()]

	def provide_data_figures(self) -> List[FigureDeclaration]:
		"""The figures the base game and the installed mods declare as data (data/ui/figures.json)."""
		from sim.ui.api import DEFAULT_DIGITS, figure_computer
		return [FigureDeclaration(figure_id.split(":")[0] if ":" in figure_id else SHIPPED_OWNER, figure_id, spec["label"],
		                          spec.get("unit", ""), spec.get("digits", DEFAULT_DIGITS), figure_computer(spec))
		        for figure_id, spec in self.needs.data_figure_specs().items()]
