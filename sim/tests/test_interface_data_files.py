"""The interface module reads the commands and figures the mods declare in data from the mods directory the content module names,
and checks every state path with the rule the game handed it (OpenInterface), not with a rule of its own."""
QUICK_TOPIC = True

import json
import os
import shutil
import tempfile
import unittest

from sim.content.api import ModError
from sim.interface.api import OpenInterface, policy_defaults
from sim.interface.module import Interface
from sim.tests import module_harness

MOD = "test_paths_a1b2"


def write_mod(directory, ui_files):
	os.makedirs(os.path.join(directory, MOD, "data", "ui"))
	with open(os.path.join(directory, MOD, "mod.json"), "w") as handle:
		json.dump({"id": MOD, "name": MOD, "version": "1.0.0", "dependencies": [], "conflicts": []}, handle)
	for name, document in ui_files.items():
		with open(os.path.join(directory, MOD, "data", "ui", name), "w") as handle:
			json.dump(document, handle)


READ_COMMAND = {"commands": {MOD + ":look": {"kind": "read", "summary": "s", "description": "d", "shows": [{"label": "pop", "path": "population.total"}]}}}
POLICY_COMMAND = {"commands": {MOD + ":pulse": {"kind": "policy", "summary": "s", "description": "d", "hook": "year_end", "default": False,
                                                "when": [{"path": "capital", "op": ">", "value": 1}], "do": [{"cmd": "status"}]}}}
FIGURE = {"figures": {MOD + ":size": {"label": "Size", "value": "population.total"}}}


class InterfaceDataFiles(unittest.TestCase):
	def setUp(self):
		self.directory = tempfile.mkdtemp()
		self.checked = []

	def tearDown(self):
		shutil.rmtree(self.directory)

	def module(self, check=None):
		module = module_harness.build(Interface, views={"mods_directory": self.directory}, module_id="interface")
		module.open_interface(OpenInterface(check or (lambda state_path, where: self.checked.append(state_path))))
		return module

	def test_a_mods_command_is_read_from_the_directory_the_content_module_names(self):
		write_mod(self.directory, {"commands.json": READ_COMMAND})
		self.assertEqual([found.name for found in self.module().data_command_specs()], [MOD + ":look"])

	def test_a_commands_state_path_goes_to_the_rule_the_game_handed_in(self):
		write_mod(self.directory, {"commands.json": READ_COMMAND})
		self.module().data_command_specs()
		self.assertEqual(self.checked, ["population.total"])

	def test_a_rule_that_refuses_a_command_path_refuses_the_command(self):
		write_mod(self.directory, {"commands.json": READ_COMMAND})

		def refuse(state_path, where):
			raise ModError("no")
		with self.assertRaises(ModError):
			self.module(refuse).data_command_specs()

	def test_a_mods_figure_is_read_and_its_value_path_checked(self):
		write_mod(self.directory, {"figures.json": FIGURE})
		self.assertIn(MOD + ":size", self.module().data_figure_specs())
		self.assertIn("population.total", self.checked)

	def test_the_base_games_figures_are_declared_with_no_mod_installed(self):
		shutil.rmtree(self.directory)
		os.makedirs(self.directory)
		self.assertGreater(len(self.module().data_figure_specs()), 0)

	def test_a_rule_that_refuses_a_figure_path_refuses_the_figure(self):
		write_mod(self.directory, {"figures.json": FIGURE})

		def refuse(state_path, where):
			raise ModError("no")
		with self.assertRaises(ModError):
			self.module(refuse).data_figure_specs()

	def test_a_policy_mods_default_comes_through_policy_defaults(self):
		write_mod(self.directory, {"commands.json": POLICY_COMMAND})
		found = policy_defaults(False, self.directory, lambda state_path, where: self.checked.append(state_path))
		self.assertEqual((found[MOD + ":pulse"], self.checked), (False, ["capital"]))


if __name__ == "__main__":
	unittest.main()
