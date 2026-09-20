"""Mechanical AST-based enforcement for authoritative live state ownership.

This test suite guarantees that internal engine code in `sim/engine/` accesses
persistent simulation state through its authoritative subsystem owner:
  - sim.state.household
  - sim.state.projects
  - sim.state.economy
  - sim.state.governance
  - sim.state.founder
  - sim.state.scenario
  - sim.state.population

Enforces:
1. No internal engine code routes project, economy, governance, founder, scenario,
   or population state through `self.household.<field>` or `household.<field>`.
2. No internal engine code accesses pruned forwarding properties on `self` or `sim`.
3. `ForwardingPropertiesMixin` contains exactly 85 backward compatibility properties.
4. AST visitor catches synthetic violation cases reliably with clear error messages.
"""
import ast
import os
from typing import List, Tuple
from .harness import *  # noqa: F401,F403

# Path to the simulation engine source code relative to repository root
ENGINE_RELATIVE_PATH = os.path.join("sim", "engine")

# Files exempt from internal AST scan (schema definitions and compatibility facades)
EXEMPT_SCAN_FILES = {
	"core_properties.py",
	"state.py",
}

# The 23 dead or internal forwarding properties pruned from Sim / ForwardingPropertiesMixin
PRUNED_FORWARDING_PROPERTIES = {
	"atrocity",
	"mine_ready",
	"wages_paid",
	"_material_stock_ledger",
	"_said_autoopen",
	"_said_debasement",
	"_said_deputies",
	"_said_near_limit",
	"_said_output",
	"bribes_ytd",
	"commissioned",
	"director_hours_spent_founder",
	"gov",
	"granted_staff",
	"last_patron_death",
	"last_withdrawal",
	"living_cost_paid",
	"market_pressure",
	"mine_cost_paid",
	"mine_pending",
	"opened_year",
	"stalled",
	"total_spend",
}

# Subsystem fields that MUST NEVER be accessed through household
NON_HOUSEHOLD_FIELDS = {
	# ProjectsState fields
	"active", "done", "done_year", "revealed", "operating", "mothballed",
	"shut_for_staff", "bountied", "granted", "forgotten", "failed_attempts",
	"paid_towards", "trade_hours_used", "opened_year", "stalled",
	# EconomyState fields
	"binding", "economy", "farm_hectares", "farm_stock_kg",
	"forest_ha", "mine_tranches", "mines", "money_real", "nitre_bed_m2",
	"output_factor", "shortages", "throttle", "market_pressure",
	"mine_cost_paid", "mine_pending", "mine_ready", "_material_stock_ledger",
	"_dashboard_history",
	# GovernanceState fields
	"inst_units", "gov",
	# FounderState fields
	"_founder_death_aged", "_founder_death_year", "dead_reason", "founder_alive",
	"life_left", "policy", "living_cost_paid", "director_hours_spent_founder",
	"last_patron_death",
	# ScenarioState fields
	"_said_command_index", "_said_parallelism", "_said_output", "_said_debasement",
	"goal_year", "year",
	# PopulationState fields
	"_food_pop_bonus_applied", "pop_children", "pop_working_age", "pop_elderly",
}


class SubsystemOwnershipASTVisitor(ast.NodeVisitor):
	"""AST visitor checking for forbidden state access patterns."""

	def __init__(self, filename: str):
		self.filename = filename
		self.violations: List[Tuple[str, int, str]] = []

	def visit_Attribute(self, node: ast.Attribute):
		# Pattern 1: <expr>.household.<non_household_field>
		if isinstance(node.value, ast.Attribute) and node.value.attr == "household":
			if node.attr in NON_HOUSEHOLD_FIELDS:
				self.violations.append((
					self.filename,
					node.lineno,
					f"Forbidden cross-subsystem access: '.household.{node.attr}' must use its authoritative subsystem owner"
				))
		# Pattern 2: household.<non_household_field> when household is a variable/parameter
		elif isinstance(node.value, ast.Name) and node.value.id == "household":
			if node.attr in NON_HOUSEHOLD_FIELDS:
				self.violations.append((
					self.filename,
					node.lineno,
					f"Forbidden cross-subsystem access: 'household.{node.attr}' must use its authoritative subsystem owner"
				))

		# Pattern 3: self.<pruned_prop> or sim.<pruned_prop>
		if isinstance(node.value, ast.Name) and node.value.id in ("self", "sim", "s"):
			if node.attr in PRUNED_FORWARDING_PROPERTIES:
				self.violations.append((
					self.filename,
					node.lineno,
					f"Forbidden access to pruned forwarding property '{node.attr}' on '{node.value.id}'"
				))

		self.generic_visit(node)


def _scan_engine_codebase() -> List[Tuple[str, int, str]]:
	"""Recursively scan sim/engine files for state ownership violations."""
	violations: List[Tuple[str, int, str]] = []
	repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
	target_dir = os.path.join(repo_root, ENGINE_RELATIVE_PATH)

	for root, _dirs, files in os.walk(target_dir):
		# Exclude compatibility proxy actors and JSON protocol entrypoints
		if "actors" in root or "proto" in root:
			continue
		for file_name in files:
			if not file_name.endswith(".py") or file_name in EXEMPT_SCAN_FILES:
				continue
			file_path = os.path.join(root, file_name)
			rel_path = os.path.relpath(file_path, repo_root)
			with open(file_path, "r", encoding="utf-8") as source_fp:
				syntax_tree = ast.parse(source_fp.read(), filename=rel_path)
			visitor = SubsystemOwnershipASTVisitor(rel_path)
			visitor.visit(syntax_tree)
			violations.extend(visitor.violations)

	return violations


def _test_engine_state_ownership_cleanliness():
	"""Verify all internal engine files adhere strictly to subsystem ownership."""
	violations = _scan_engine_codebase()
	if not violations:
		return True, "0 state ownership violations detected across engine codebase"

	error_messages = [f"{v[0]}:{v[1]} - {v[2]}" for v in violations[:10]]
	return False, f"Found {len(violations)} ownership violations:\n" + "\n".join(error_messages)


_ok, _detail = _test_engine_state_ownership_cleanliness()
check("internal engine state ownership cleanliness", _ok, _detail)


def _test_forwarding_properties_count():
	"""Verify core_properties.py defines exactly 85 properties and 0 pruned properties."""
	repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
	props_file = os.path.join(repo_root, ENGINE_RELATIVE_PATH, "core_properties.py")
	with open(props_file, "r", encoding="utf-8") as fp:
		tree = ast.parse(fp.read(), filename=props_file)

	mixin_class = next((node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "ForwardingPropertiesMixin"), None)
	if not mixin_class:
		return False, "ForwardingPropertiesMixin class not found in core_properties.py"

	properties = set()
	for node in mixin_class.body:
		if isinstance(node, ast.FunctionDef):
			has_prop_dec = any(
				(d.id if isinstance(d, ast.Name) else (d.attr if isinstance(d, ast.Attribute) else "")) == "property"
				for d in node.decorator_list
			)
			if has_prop_dec:
				properties.add(node.name)

	if len(properties) != 85:
		return False, f"Expected exactly 85 forwarding properties, found {len(properties)}"

	pruned_present = PRUNED_FORWARDING_PROPERTIES.intersection(properties)
	if pruned_present:
		return False, f"Pruned properties still present in core_properties.py: {pruned_present}"

	return True, "core_properties.py maintains exactly 85 compatibility properties with 0 pruned"


_ok, _detail = _test_forwarding_properties_count()
check("forwarding properties count and composition", _ok, _detail)


def _test_synthetic_violation_detection():
	"""Edge cases (~5 checks): Verify AST visitor detects synthetic ownership violations."""
	test_cases = [
		# Case 1: accessing .household.mines (EconomyState)
		("def f(self):\n\treturn self.household.mines\n", "mines"),
		# Case 2: accessing household.active (ProjectsState)
		("def f(self, household):\n\treturn household.active\n", "active"),
		# Case 3: accessing self.stalled (Pruned ProjectsState property)
		("def f(self):\n\treturn self.stalled\n", "stalled"),
		# Case 4: accessing sim.total_spend (Pruned HouseholdState property)
		("def f(sim):\n\treturn sim.total_spend\n", "total_spend"),
		# Case 5: accessing .household.gov (GovernanceState)
		("def f(self):\n\treturn self.household.gov\n", "gov"),
	]

	for code_snippet, expected_keyword in test_cases:
		tree = ast.parse(code_snippet, filename="<synthetic>")
		visitor = SubsystemOwnershipASTVisitor("<synthetic>")
		visitor.visit(tree)
		if not visitor.violations:
			return False, f"Visitor failed to flag violation in snippet:\n{code_snippet}"
		if not any(expected_keyword in v[2] for v in visitor.violations):
			return False, f"Violation did not mention '{expected_keyword}': {visitor.violations}"

	return True, "AST visitor successfully detects all 5 synthetic violation edge cases"


_ok, _detail = _test_synthetic_violation_detection()
check("AST visitor synthetic violation detection", _ok, _detail)
