"""A year's price solves and scans are shared by every concern that asks the same question, so the year's cost
grows with its own activity, not with the number of concerns held (Complaint 581)."""

QUICK_TOPIC = True

import types
import unittest
from unittest import mock

from sim.agents.business import Business
from sim.agents import patent
from sim.agents.registry import ActorRegistry
from sim.diffusion.api import NoteFirstRuns
from sim.diffusion.module import Diffusion
from sim.diffusion.state import DiffusionWorld
from sim.engine import concern_volume, economy_port_actors, prices, tile_ownership
from sim.engine.economy_materials import MaterialSupplyMixin
from sim.engine.state import ActorRecord, ActorsState
from sim.engine.techniques_in_use import TechniquesInUseMixin
from sim.engine.tile_ownership import TileOwnershipMixin
from sim.engine.view_share import ViewShareMixin
from sim.tests import module_harness


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
        original = registry.concerns_of_active_firms
        registry.concerns_of_active_firms = lambda: walks.append(1) or original()
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
        now = {"year": 143}
        in_use = frozenset(["node_a"])
        world = DiffusionWorld()
        module = module_harness.build(
            Diffusion, world=world,
            views={"year": lambda: now["year"], "tree": {"node_a": {"id": "node_a"}}.get,
                   "techniques_granted": lambda: {"node_g"}, "techniques_in_use": lambda: in_use})
        spreads = []

        def spread(in_use_now, granted, first_run, node_of, year):
            spreads.append(year)
            return frozenset(granted) | frozenset(in_use_now)

        def ask():
            module.note_first_runs(NoteFirstRuns(in_use))
            return module.techniques_spread()
        with mock.patch("sim.diffusion.technique_spread.spread_techniques", spread):
            answers = [ask() for _concern in range(30)]
            now["year"] = 144
            ask()
        self.assertEqual(spreads, [143, 144])
        self.assertEqual(answers[0], frozenset(["node_a", "node_g"]))
        self.assertEqual(world.technique_first_run, {"node_a": 143 - 10000})


class StandInWorld(ViewShareMixin, TileOwnershipMixin):
    """The few attributes the shared-answer and tile-ownership mixins read."""

    def real_output_per_head(self):
        return self.state.economy.output_per_head

    def __init__(self):
        self.year = 143
        self.state = types.SimpleNamespace(
            scenario=types.SimpleNamespace(year=143),
            holdings=types.SimpleNamespace(forest_ha=1.0, nitre_bed_m2=1.0, mines=[]),
            projects=types.SimpleNamespace(done=[], operating={}),
            economy=types.SimpleNamespace(output_per_head=1.0, tile_owners={"t1": {"owner": "rome"}, "t2": {"owner": "gaul"}}))
        self.household = types.SimpleNamespace(done_version=0, operating_version=0)
        self.population = types.SimpleNamespace(total=100.0)
        self.civ = {"id": "rome"}
        self.world_map = types.SimpleNamespace(tiles={"t1": 1, "t2": 1})
        self.stores = types.SimpleNamespace(view=lambda _name: types.SimpleNamespace(set=lambda *_arguments: None,
                                                                                       get=lambda _tile: None))

    def tile_owner_map(self):
        return self.state.economy.tile_owners


class StandaloneAnswers(unittest.TestCase):

    def test_a_standalone_answer_is_worked_out_once_outside_a_view(self):
        world, worked = StandInWorld(), []
        for _firm in range(40):
            world._shared_answer(("cap", "smith"), (1,), lambda: worked.append(1) or 5.0, standalone=True)
        self.assertEqual(len(worked), 1)

    def test_a_changed_input_or_a_new_year_works_it_out_again(self):
        world, worked = StandInWorld(), []
        ask = lambda inputs: world._shared_answer(("cap", "smith"), inputs, lambda: worked.append(1) or 5.0, standalone=True)
        ask((1,))
        ask((2,))
        world.state.scenario.year = 144
        ask((2,))
        self.assertEqual(len(worked), 3)

    def test_an_answer_that_is_not_standalone_is_not_shared_outside_a_view(self):
        world, worked = StandInWorld(), []
        for _firm in range(3):
            world._shared_answer(("bill", "x"), (), lambda: worked.append(1) or 1.0)
        self.assertEqual(len(worked), 3)

    def test_a_registry_size_change_leaves_a_view_s_answers_alone(self):
        world, worked = StandInWorld(), []
        world._view_world_stamp = lambda: ((), (1,))
        world._view_scope = {}
        for _firm in range(5):
            world._shared_answer(("bill", "x"), (), lambda: worked.append(1) or 1.0)
        self.assertEqual(len(worked), 1)


class HomeTilesHeld(unittest.TestCase):

    def test_the_owner_map_is_read_once_until_a_tile_changes_hands(self):
        world, reads = StandInWorld(), []
        original = tile_ownership.tiles_held
        with mock.patch.object(tile_ownership, "tiles_held",
                               lambda *arguments: reads.append(1) or original(*arguments)), \
                mock.patch.object(tile_ownership.world_events, "record", lambda *_arguments, **_keywords: None):
            for _call in range(30):
                self.assertEqual(world.home_tiles_held(), ["t1"])
                self.assertEqual(world.tiles_owned_by("gaul"), ["t2"])
            self.assertEqual(len(reads), 1)
            version = world.tile_owner_version()
            world.transfer_tile("t2", "rome")
            self.assertNotEqual(world.tile_owner_version(), version)
            self.assertEqual(world.home_tiles_held(), ["t1", "t2"])
            self.assertEqual(world.tiles_owned_by("gaul"), [])
            self.assertEqual(len(reads), 2)


class PatentHolders(unittest.TestCase):

    def registry(self):
        state = ActorsState()
        for number in range(3):
            state.records["firm:00%d" % number] = ActorRecord(kind="firm", business=Business.running(["node_0"]), workforce={})
        return ActorRegistry(state)

    def test_holders_are_found_from_an_index_that_changes_only_with_a_patent(self):
        registry = self.registry()
        self.assertEqual(registry.patent_holders("loom"), [])
        index = registry.__dict__["_patent_index"]
        for _question in range(20):
            registry.patent_holders("loom")
        self.assertIs(registry.__dict__["_patent_index"], index)
        registry.actors["firm:001"].record.patents["loom"] = {"granted": 1, "expires": 9, "licensees": []}
        self.assertEqual([actor.actor_id for actor in registry.patent_holders("loom")], ["firm:001"])
        self.assertIsNot(registry.__dict__["_patent_index"], index)

    def test_an_actor_that_holds_nothing_leaves_the_index_alone(self):
        registry = self.registry()
        registry.patent_holders("loom")
        index = registry.__dict__["_patent_index"]
        registry.add("firm:009", ActorRecord(kind="firm", business=Business.running(["node_0"]), workforce={}))
        registry.patent_holders("loom")
        self.assertIs(registry.__dict__["_patent_index"], index)

    def test_the_lowest_id_among_live_holders_gets_the_entry(self):
        registry = self.registry()
        for number, expires in ((0, 5), (1, 20), (2, 20)):
            registry.actors["firm:00%d" % number].record.patents["loom"] = {"granted": 1, "expires": expires, "licensees": []}
        entry = patent.entry_among(registry.patent_holders("loom"), "loom", 10)
        self.assertEqual(entry["holder"], "firm:001")
        self.assertIsNone(patent.entry_among(registry.patent_holders("loom"), "loom", 30))

    def test_the_concerns_of_active_firms_follow_the_holders(self):
        registry = self.registry()
        registry.actors["firm:001"].concerns.add("node_1")
        self.assertEqual(registry.concerns_of_active_firms(), {"node_0", "node_1"})
        for number in range(3):
            registry.actors["firm:00%d" % number].record.exited_year = 100
        self.assertEqual(registry.concerns_of_active_firms(), set())


class ActorsOfAKind(unittest.TestCase):

    def test_a_new_actor_joins_its_kind_in_id_order_without_a_rescan(self):
        state = ActorsState()
        for name in ("firm:003", "firm:001"):
            state.records[name] = ActorRecord(kind="firm", business=Business.running(["node_0"]), workforce={})
        registry = ActorRegistry(state)
        self.assertEqual([actor.actor_id for actor in registry.of_kind("firm")], ["firm:001", "firm:003"])
        kept = registry._by_kind["firm"]
        registry.add("firm:002", ActorRecord(kind="firm", business=Business.running(["node_0"]), workforce={}))
        self.assertIs(registry._by_kind["firm"], kept)
        self.assertEqual([actor.actor_id for actor in registry.of_kind("firm")], ["firm:001", "firm:002", "firm:003"])


class NotedSales(unittest.TestCase):

    class CountingList(list):
        scans = 0

        def __iter__(self):
            type(self).scans += 1
            return super().__iter__()

    def test_each_note_is_a_lookup_not_a_scan_of_the_sales(self):
        sales, index = self.CountingList(), [None, 0, {}]
        for number in range(60):
            economy_port_actors.note_sale(sales, "firm:%03d" % number, "wheat", 1.0, None, index)
        economy_port_actors.note_sale(sales, "firm:007", "wheat", 2.0, [("node_a", 1.0)], index)
        self.assertLessEqual(self.CountingList.scans, 2)
        self.assertEqual(len(sales), 60)
        seventh = [sale for sale in list(sales) if sale["seller"] == "firm:007"][0]
        self.assertEqual((seventh["tonnes"], seventh["concerns"]), (3.0, [["node_a", 1.0]]))

    def test_a_list_rebuilt_elsewhere_is_indexed_again(self):
        sales, index = [], [None, 0, {}]
        economy_port_actors.note_sale(sales, "a", "wheat", 1.0, None, index)
        rebuilt = [dict(sale) for sale in sales]
        economy_port_actors.note_sale(rebuilt, "a", "wheat", 1.0, None, index)
        self.assertEqual([sale["tonnes"] for sale in rebuilt], [2.0])


if __name__ == "__main__":
    unittest.main()
