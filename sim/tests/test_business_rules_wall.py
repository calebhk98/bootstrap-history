"""Wall: a plant's crew and takings product are computed by the business rules and nowhere else in the engine.

The founder's `venture_hands`, `venture_foreman`, `venture_crew_by_trade` and `venture_real_earnings` and the actors'
`concern_staff` and `concern_takings` are adapters: each must call the shared rule, and no other module may call the
kernel's crew functions (that is how a second implementation would start)."""

QUICK_TOPIC = True

import ast
import os
import unittest

from .test_business_wall import ROOT, called_name, scanned_files

KERNEL_CREW_FUNCTIONS = frozenset(("crew_people", "derived_crew_hours", "crew_by_trade", "crew_is_fallback"))


def calls_in_function(relative, function_name):
	with open(os.path.join(ROOT, relative), encoding="utf-8") as handle:
		tree = ast.parse(handle.read())
	for node in ast.walk(tree):
		if isinstance(node, ast.FunctionDef) and node.name == function_name:
			return {called_name(call) for call in ast.walk(node) if isinstance(call, ast.Call)} - {None}
	raise AssertionError("%s has no %s" % (relative, function_name))


def kernel_crew_calls(tree):
	"""Lines that call a kernel crew function through `plant_figures`, or import one by name."""
	lines = []
	for node in ast.walk(tree):
		if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr in KERNEL_CREW_FUNCTIONS
				and isinstance(node.func.value, ast.Name) and node.func.value.id == "plant_figures"):
			lines.append(node.lineno)
		elif isinstance(node, ast.ImportFrom) and any(alias.name in KERNEL_CREW_FUNCTIONS for alias in node.names):
			lines.append(node.lineno)
	return lines


class BusinessRulesWallTests(unittest.TestCase):
	def test_only_the_business_rules_call_the_kernel_crew_functions(self):
		offenders = []
		for path, relative in scanned_files():
			if relative.startswith("sim/world/"):
				continue
			with open(path, encoding="utf-8") as handle:
				offenders.extend("%s:%s" % (relative, line) for line in kernel_crew_calls(ast.parse(handle.read())))
		self.assertEqual(offenders, [], "a crew is computed by sim/agents/business_crew_rule.py; call it instead")

	def test_the_founder_and_the_actors_take_their_crew_from_the_one_rule(self):
		for function_name, rule in (("venture_hands", "hands"), ("venture_hands_founder_staffed", "founder_staffed_hands"),
									("venture_crew_by_trade", "crew_by_trade"), ("venture_foreman", "foreman"),
									("concern_staff_by_trade", "staff_by_trade")):
			self.assertIn(rule, calls_in_function("sim/engine/projects_ventures.py", function_name),
						  "%s must call %s" % (function_name, rule))
		self.assertIn("concern_staff_by_trade", calls_in_function("sim/engine/agents_port.py", "concern_staff"))

	def test_the_founder_and_the_actors_take_their_takings_from_the_one_product(self):
		self.assertIn("takings_of_size", calls_in_function("sim/engine/projects_venture_quotes.py", "venture_real_earnings"))
		self.assertIn("takings_of_size", calls_in_function("sim/engine/agents_port.py", "concern_takings"))

	def test_the_detector_sees_a_deliberate_second_crew_rule(self):
		tree = ast.parse("def f(x):\n    return plant_figures.crew_people(1, 2, None, 3)\n")
		self.assertEqual(len(kernel_crew_calls(tree)), 1)


if __name__ == "__main__":
	unittest.main()
