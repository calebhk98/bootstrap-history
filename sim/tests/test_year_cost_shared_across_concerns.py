"""A year's price solves and scans are shared by every concern that asks the same question, so the year's cost
grows with its own activity, not with the number of concerns held (Complaint 581)."""

QUICK_TOPIC = True

import types
import unittest
from unittest import mock

from sim.agents.business import Business
from sim.agents.registry import ActorRegistry
from sim.engine import concern_volume, prices
from sim.engine.economy_materials import MaterialSupplyMixin
from sim.engine.state import ActorRecord, ActorsState
from sim.engine.techniques_in_use import TechniquesInUseMixin


class ConcernPriceTables(unittest.TestCase):

    def asking(self, held_sets, civilisation):
        world = types.SimpleNamespace(civ=civilisation)
        solves = []

        def solve(held, **_arguments):
            solves.append(frozenset(held))
            return {"grain_kg": 2.0, "dust_kg": 0.0}
        with mock.patch("sim.engine.data.calculated_goods_prices", solve):
            answers = [concern_volume.ConcernVolumeMixin._concern_prices_in_hours(world, held) for held in held_sets]
        return solves, answers

    def test_concerns_asking_about_the_same_techniques_share_one_solve(self):
        civilisation = {"id": "stand_in_civ_one"}
        solves, answers = self.asking([set(["a", "b"]) for _concern in range(40)], civilisation)
        self.assertEqual(len(solves), 1)
        self.assertEqual(answers[0], {"grain_kg": 2.0})
        self.assertTrue(all(answer is answers[0] for answer in answers))

    def test_another_set_of_techniques_is_solved_again(self):
        civilisation = {"id": "stand_in_civ_two"}
        solves, _answers = self.asking([{"a"}, {"a"}, {"a", "b"}, {"a", "b"}], civilisation)
        self.assertEqual(sorted(map(sorted, solves)), [["a"], ["a", "b"]])

    def test_a_changed_civilisation_is_solved_again(self):
        civilisation = {"id": "stand_in_civ_three", "population": 1}
        solves, _answers = self.asking([{"a"}], civilisation)
        civilisation["population"] = 2
        more, _answers = self.asking([{"a"}], civilisation)
        self.assertEqual((len(solves), len(more)), (1, 1))


class TechniquesInReach(unittest.TestCase):

    def test_equal_questions_are_worked_out_once(self):
        entries = {"make_a": {"requires_node": "node_a", "outputs": {"a_kg": 1.0}}}
        worked = []

        def work_out(held, held_gate_nodes, resolvable_materials, production_entries):
            worked.append(1)
            return frozenset(["make_a"])
        with mock.patch.object(prices, "_entries_in_reach", work_out):
            answers = [prices.entries_in_reach(set(["x"]), frozenset(), set(["b_kg"]), entries) for _concern in range(40)]
        self.assertEqual(len(worked), 1)
        self.assertEqual(answers[-1], frozenset(["make_a"]))

    def test_another_catalogue_is_worked_out_again(self):
        worked = []

        def work_out(held, held_gate_nodes, resolvable_materials, production_entries):
            worked.append(1)
            return frozenset()
        with mock.patch.object(prices, "_entries_in_reach", work_out):
            prices.entries_in_reach({"x"}, frozenset(), set(), {"one": {}})
            prices.entries_in_reach({"x"}, frozenset(), set(), {"two": {}})
        self.assertEqual(len(worked), 2)


class ProducerListMemo(unittest.TestCase):

    def world(self, stamp):
        return types.SimpleNamespace(economy=types.SimpleNamespace(producers_stamp=lambda: stamp[0]))

    def test_the_list_is_kept_while_the_producers_are_unchanged(self):
        stamp = [0]
        world = self.world(stamp)
        built = []
        for _concern in range(30):
            MaterialSupplyMixin._producers_memo(world, "producers_by_good", 143, lambda: built.append(1) or {"ore": []})
        self.assertEqual(len(built), 1)
        stamp[0] = 1
        MaterialSupplyMixin._producers_memo(world, "producers_by_good", 143, lambda: built.append(1) or {"ore": []})
        self.assertEqual(len(built), 2)

    def test_an_unanswered_question_is_asked_again(self):
        world = self.world([0])
        asked = []
        for _concern in range(3):
            self.assertIsNone(MaterialSupplyMixin._producers_memo(world, "producers_by_good", 143,
                                                                  lambda: asked.append(1)))
        self.assertEqual(len(asked), 3)


class ConcernSetVersion(unittest.TestCase):

    def registry(self):
        state = ActorsState()
        state.records["firm:000"] = ActorRecord(kind="firm", business=Business.running(["node_0"]), workforce={})
        return ActorRegistry(state)

    def test_a_size_change_leaves_the_set_version_alone_and_a_new_concern_moves_it(self):
        registry = self.registry()
        before = (registry.version[0], registry.concern_set_version[0])
        registry.note_capacity_change("firm:000")
        self.assertEqual(registry.concern_set_version[0], before[1])
        self.assertGreater(registry.version[0], before[0])
        registry.actors["firm:000"].concerns.add("node_1")
        self.assertGreater(registry.concern_set_version[0], before[1])

    def test_the_techniques_in_use_are_not_worked_out_again_for_a_size_change(self):
        registry = self.registry()
        projects = types.SimpleNamespace(granted=set(), operating={}, done=[])
        world = types.SimpleNamespace(
            household=types.SimpleNamespace(done_version=0, operating_version=0),
            state=types.SimpleNamespace(projects=projects, actors=types.SimpleNamespace(records={"firm:000": 1})),
            actors=registry, concern_set_version=lambda: registry.concern_set_version[0])
        walks = []
        original = registry.active_firms
        registry.active_firms = lambda: walks.append(1) or original()
        first = TechniquesInUseMixin.techniques_in_use(world)
        for _firm in range(25):
            registry.note_capacity_change("firm:000")
            TechniquesInUseMixin.techniques_in_use(world)
        self.assertEqual(len(walks), 1)
        registry.actors["firm:000"].concerns.add("node_1")
        self.assertEqual(TechniquesInUseMixin.techniques_in_use(world), first | {"node_1"})
        self.assertEqual(len(walks), 2)


class SpreadAndLending(unittest.TestCase):

    def test_techniques_spread_is_worked_out_once_a_year_for_the_same_techniques(self):
        economy = types.SimpleNamespace(technique_first_run={}, technique_record_started=False)
        in_use = frozenset(["node_a"])
        world = types.SimpleNamespace(
            state=types.SimpleNamespace(scenario=types.SimpleNamespace(year=143), economy=economy,
                                        projects=types.SimpleNamespace(granted={"node_g"})),
            techniques_in_use=lambda: in_use, nodes={"node_a": {"id": "node_a"}})
        spreads = []

        def spread(in_use_now, granted, first_run, nodes, year):
            spreads.append(year)
            return frozenset(granted) | frozenset(in_use_now)
        with mock.patch("sim.engine.technique_spread.spread_techniques", spread):
            answers = [TechniquesInUseMixin.techniques_spread(world) for _concern in range(30)]
            world.state.scenario.year = 144
            TechniquesInUseMixin.techniques_spread(world)
        self.assertEqual(spreads, [143, 144])
        self.assertEqual(answers[0], frozenset(["node_a", "node_g"]))
        self.assertEqual(economy.technique_first_run, {"node_a": 143 - 10000})

    def test_an_exposure_given_the_lent_share_does_not_read_the_loans_again(self):
        from sim.engine.holdings_exposure import HoldingsExposureMixin
        reads = []
        world = types.SimpleNamespace(lent_share=lambda: reads.append(1) or 0.5)
        actor = types.SimpleNamespace(money=10.0, record=types.SimpleNamespace(stores={}, holdings={}))
        view = HoldingsExposureMixin.actor_exposure(world, actor, lambda material: 1.0, lambda issuer: None, 0.25)
        self.assertEqual(reads, [])
        self.assertAlmostEqual(view.values["loans"], 2.5)


if __name__ == "__main__":
    unittest.main()
