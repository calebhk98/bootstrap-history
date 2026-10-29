"""The sharing module (sim/sharing/): an answer asked inside a view's scope is computed once while the world stamp and the entry's
own inputs are unchanged, and again when any one stamped fact changes; outside a scope nothing is shared except an answer marked
standalone. Complaint 321 is the reason it exists."""
QUICK_TOPIC = True

import types
import unittest

from sim.sharing.module import Sharing
from sim.sharing.rules import memoised
from sim.tests import module_harness


def world_facts():
	"""The facts the stamp reads, as plain values a test changes one at a time."""
	return {"year": 143, "material_prices": {"iron": 5.0}, "material_demand_held": {"iron": 1.0}, "others_trade_stamp": ((), ()),
	        "techniques_version": (0, 0), "operating_version": (0, 0), "techniques_held": frozenset(), "operating": {},
	        "forest_hectares": 1.0, "nitre_beds": {"square_metres": 1.0, "tonnes_per_square_metre": 0.001},
	        "population": types.SimpleNamespace(total=100.0), "real_output_per_head": 1.0, "mine_workings": [],
	        "goods_stock": {"iron": 0.0}}


# the change to each fact that must make a shared answer stale: (fact, new value)
CHANGES_BY_INPUT = {
	"year": ("year", 144),
	"techniques_version": ("techniques_version", (1, 0)),
	"operating_version": ("operating_version", (0, 1)),
	"techniques_held": ("techniques_held", frozenset(["loom"])),
	"operating": ("operating", {"smithy": 1}),
	"forest_hectares": ("forest_hectares", 2.0),
	"nitre_beds": ("nitre_beds", {"square_metres": 2.0, "tonnes_per_square_metre": 0.001}),
	"population": ("population", types.SimpleNamespace(total=101.0)),
	"real_output_per_head": ("real_output_per_head", 1.5),
	"mine_workings": ("mine_workings", ["pit"]),
}
CHANGES_BY_INPUT_OF_A_VIEW_ONLY = {
	"material_prices": ("material_prices", {"iron": 9.0}),
	"material_demand_held": ("material_demand_held", {"iron": 2.0}),
	"others_trade_stamp": ("others_trade_stamp", (((("iron", ((("rival", 3.0),))),),), ())),
}


def build(facts=None):
	"""The module over `facts` (a dict the test may change after the build) and a record of what `done_memo` was asked."""
	facts = facts if facts is not None else world_facts()
	views = {name: (lambda name=name: facts[name]) for name in facts if name != "goods_stock"}
	views["goods_stock"] = lambda commodity: facts["goods_stock"][commodity]
	views["done_memo"] = lambda kind, node_id, compute: compute()
	views["material_pool"] = lambda material: ("iron", 1.0)
	views["project_material_needs"] = lambda node_id: ["iron_ore"]
	module = module_harness.build(Sharing, views=views, module_id="sharing")
	module.facts = facts
	return module


def computations(module, change, standalone=False):
	"""How many times the answer was worked out when asked, `change` applied to the facts, asked again, in one scope."""
	worked = []
	ask = lambda: module.shared_answer(("cap", "smith"), (1,), lambda: worked.append(1) or 5.0, standalone)
	with module.shared_answers({}):
		ask()
		if change is not None:
			fact, value = change
			module.facts[fact] = value
		ask()
	return len(worked)


class MemoRules(unittest.TestCase):
	def test_an_answer_is_reused_while_the_stamp_and_inputs_hold(self):
		scope, worked = {}, []
		for _asker in range(5):
			memoised(scope, ((), (1,)), "bill", (2,), lambda: worked.append(1) or 7.0)
		self.assertEqual(len(worked), 1)

	def test_different_inputs_are_different_answers(self):
		scope = {}
		first = memoised(scope, ((), (1,)), "bill", (2,), lambda: 7.0)
		second = memoised(scope, ((), (1,)), "bill", (3,), lambda: 8.0)
		self.assertEqual((first, second), (7.0, 8.0))

	def test_a_rebuilt_object_in_the_stamp_makes_the_answer_stale(self):
		scope, worked = {}, []
		memoised(scope, (({"iron": 5.0},), ()), "bill", (), lambda: worked.append(1))
		memoised(scope, (({"iron": 5.0},), ()), "bill", (), lambda: worked.append(1))
		self.assertEqual(len(worked), 2)

	def test_an_equal_but_different_object_is_not_a_hit(self):
		scope, worked = {}, []
		prices = {"iron": 5.0}
		memoised(scope, ((prices,), ()), "bill", (), lambda: worked.append(1))
		memoised(scope, ((prices,), ()), "bill", (), lambda: worked.append(1))
		self.assertEqual(len(worked), 1)

	def test_a_world_with_no_stamp_shares_nothing(self):
		scope, worked = {}, []
		for _asker in range(3):
			memoised(scope, None, "bill", (), lambda: worked.append(1))
		self.assertEqual(len(worked), 3)

	def test_two_keys_are_two_answers(self):
		scope = {}
		first = memoised(scope, ((), ()), "a", (), lambda: 1.0)
		second = memoised(scope, ((), ()), "b", (), lambda: 2.0)
		self.assertEqual((first, second), (1.0, 2.0))


class SharedAnswers(unittest.TestCase):
	def test_outside_a_scope_nothing_is_shared(self):
		module, worked = build(), []
		for _asker in range(2):
			module.shared_answer("k", (), lambda: worked.append(1))
		self.assertEqual(len(worked), 2)

	def test_inside_a_scope_forty_askers_work_it_out_once(self):
		module, worked = build(), []
		with module.shared_answers({}):
			answers = {module.shared_answer("k", (), lambda: worked.append(1) or 5.0) for _asker in range(40)}
		self.assertEqual((len(worked), len(answers)), (1, 1))

	def test_a_standalone_answer_is_shared_outside_a_scope(self):
		module, worked = build(), []
		for _asker in range(40):
			module.shared_answer("k", (1,), lambda: worked.append(1) or 5.0, standalone=True)
		self.assertEqual(len(worked), 1)

	def test_a_standalone_answer_with_a_new_input_is_worked_out_again(self):
		module, worked = build(), []
		for inputs in ((1,), (2,)):
			module.shared_answer("k", inputs, lambda: worked.append(1) or 5.0, standalone=True)
		self.assertEqual(len(worked), 2)

	def test_two_scopes_do_not_share_a_table(self):
		module, worked = build(), []
		for _view in range(2):
			with module.shared_answers({}):
				module.shared_answer("k", (), lambda: worked.append(1))
		self.assertEqual(len(worked), 2)

	def test_the_same_table_shares_across_two_openings(self):
		module, worked, table = build(), [], {}
		for _opening in range(2):
			with module.shared_answers(table):
				module.shared_answer("k", (), lambda: worked.append(1))
		self.assertEqual(len(worked), 1)

	def test_nested_scopes_hand_back_the_outer_scope(self):
		module, worked = build(), []
		with module.shared_answers({}):
			module.shared_answer("k", (), lambda: worked.append(1))
			with module.shared_answers({}):
				module.shared_answer("k", (), lambda: worked.append(1))
			module.shared_answer("k", (), lambda: worked.append(1))
		self.assertEqual(len(worked), 2)

	def test_a_scope_is_closed_when_the_asking_fails(self):
		module, worked = build(), []
		with self.assertRaises(ValueError):
			with module.shared_answers({}):
				raise ValueError("pricing failed")
		module.shared_answer("k", (), lambda: worked.append(1))
		module.shared_answer("k", (), lambda: worked.append(1))
		self.assertEqual(len(worked), 2)

	def test_a_world_with_no_demand_table_shares_nothing(self):
		module = build()
		module.facts["material_demand_held"] = None
		self.assertEqual(computations(module, None), 2)

	def test_the_answer_is_what_compute_returned(self):
		module = build()
		with module.shared_answers({}):
			self.assertEqual((module.shared_answer("k", (), lambda: 12.5), module.shared_answer("k", (), lambda: 99.0)), (12.5, 12.5))


class SharedBills(unittest.TestCase):
	def test_a_bill_is_reused_while_the_nodes_stock_holds(self):
		module, worked = build(), []
		with module.shared_answers({}):
			for _asker in range(5):
				module.shared_bill("furnace", lambda: worked.append(1) or 3.0)
		self.assertEqual(len(worked), 1)

	def test_a_bill_is_recomputed_when_the_stock_it_draws_on_moved(self):
		module, worked = build(), []
		with module.shared_answers({}):
			module.shared_bill("furnace", lambda: worked.append(1))
			module.facts["goods_stock"]["iron"] = 1.0e6
			module.shared_bill("furnace", lambda: worked.append(1))
		self.assertEqual(len(worked), 2)

	def test_outside_a_scope_every_bill_is_computed(self):
		module, worked = build(), []
		for _asker in range(2):
			module.shared_bill("furnace", lambda: worked.append(1))
		self.assertEqual(len(worked), 2)

	def test_two_nodes_are_two_bills(self):
		module = build()
		with module.shared_answers({}):
			self.assertEqual((module.shared_bill("a", lambda: 1.0), module.shared_bill("b", lambda: 2.0)), (1.0, 2.0))


class StampInputs(unittest.TestCase):
	"""Each fact the stamp reads makes a shared answer stale when it changes."""


def _stale_in_a_view(change):
	def test(self):
		self.assertEqual(computations(build(), change), 2)
	return test


def _stale_standalone(change):
	def test(self):
		module, worked = build(), []
		ask = lambda: module.shared_answer(("cap", "smith"), (1,), lambda: worked.append(1) or 5.0, standalone=True)
		ask()
		module.facts[change[0]] = change[1]
		ask()
		self.assertEqual(len(worked), 2)
	return test


def _not_read_standalone(change):
	def test(self):
		module, worked = build(), []
		ask = lambda: module.shared_answer(("cap", "smith"), (1,), lambda: worked.append(1) or 5.0, standalone=True)
		ask()
		module.facts[change[0]] = change[1]
		ask()
		self.assertEqual(len(worked), 1)
	return test


for _name, _change in {**CHANGES_BY_INPUT, **CHANGES_BY_INPUT_OF_A_VIEW_ONLY}.items():
	setattr(StampInputs, "test_a_changed_%s_makes_a_view_answer_stale" % _name, _stale_in_a_view(_change))
for _name, _change in CHANGES_BY_INPUT.items():
	setattr(StampInputs, "test_a_changed_%s_makes_a_standalone_answer_stale" % _name, _stale_standalone(_change))
for _name, _change in CHANGES_BY_INPUT_OF_A_VIEW_ONLY.items():
	setattr(StampInputs, "test_a_changed_%s_leaves_a_standalone_answer_alone" % _name, _not_read_standalone(_change))


class StampAnswers(unittest.TestCase):
	def test_an_unchanged_world_is_a_hit(self):
		self.assertEqual(computations(build(), None), 1)


if __name__ == "__main__":
	unittest.main()
