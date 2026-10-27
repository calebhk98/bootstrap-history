"""The land module's commands and views, each called on the module over plain values (sim/tests/module_harness.py): who holds
a tile and how a transfer is recorded, the owner map's seeding and version, the colonies a seat founds and loses, and what the
geography reads of the game. The rules are test_tile_owners and test_colony_rules."""
QUICK_TOPIC = True

import types
import unittest

from sim.actors.api import FollowTileTransfer
from sim.demography.api import SendSettlers
from sim.geography.api import tile_owners
from sim.hazards.api import RecordWorldEvent
from sim.land import rules
from sim.land.commands import AdvanceColonies, FoundColony, TransferTile
from sim.land.map_views import GeographyInputs
from sim.land.module import Land
from sim.land.state import LandSeat, LandWorld
from sim.ledger.api import PayEdge
from sim.refusal import Refusal
from sim.reporting.api import RecordEvent
from sim.stores.api import WriteStore
from sim.tests import module_harness

MAP = types.SimpleNamespace(tiles={"t1": {}, "t2": {}, "t3": {}, "far_tile": {}, "afghanistan_01": {}})
CHARTER = "ben_settlement_charter"
SPEC = {"settlers": 20, "outfit_hours_per_settler": 50.0}


class Levels:
    """The `control` tile store, written by WriteStore."""

    def __init__(self, **levels):
        self.values = dict(levels)

    def view(self, name):
        return {"default": None, "values": dict(self.values)}

    def write(self, command):
        if command.value is None:
            self.values.pop(command.key, None)
        else:
            self.values[command.key] = command.value


def built(owners=None, levels=None, views=None, seat=None, answers=None):
    levels = levels or Levels()
    plain = {"civilisation": {"id": "home"}, "store": levels.view, "home_tiles_held": ["t1"]}
    plain.update(views or {})
    module = module_harness.build(
        Land, views=plain, answers=dict({WriteStore: levels.write}, **(answers or {})),
        world=LandWorld(tile_owners={tile: {"owner": owner} for tile, owner in (owners or {}).items()}),
        seat=seat if seat is not None else LandSeat())
    module._map_cache = MAP
    return module, levels


class TheOwnerMap(unittest.TestCase):
    def test_a_transfer_answers_the_previous_owner_and_moves_the_tile_at_the_given_level(self):
        module, levels = built({"t1": "home", "t2": "home"})
        previous = module.transfer_tile(TransferTile("t1", "rival", "test", "garrisoned"))
        self.assertEqual(previous, "home")
        self.assertEqual(module.world.tile_owners, {"t1": {"owner": "rival"}, "t2": {"owner": "home"}})
        self.assertEqual(levels.values, {"t1": "garrisoned"})

    def test_releasing_a_tile_leaves_it_unowned_and_clears_its_level(self):
        module, levels = built({"t1": "rival"}, Levels(t1="garrisoned"))
        previous = module.transfer_tile(TransferTile("t1", None, "test"))
        self.assertEqual(previous, "rival")
        self.assertNotIn("t1", module.world.tile_owners)
        self.assertEqual(levels.values, {})

    def test_a_transfer_is_written_to_the_world_event_log_with_its_cause_and_both_owners(self):
        module, _levels = built({"t1": "home"})
        module.transfer_tile(TransferTile("t1", "rival", "a treaty", "garrisoned"))
        self.assertEqual(module_harness.sent(module)[-1], RecordWorldEvent(
            "tile_transfer", actors=("home", "rival"), tiles=("t1",), cause="a treaty",
            facts={"from_owner": "home", "to_owner": "rival", "control": "garrisoned"}))

    def test_the_countries_that_lost_and_gained_a_tile_are_told_before_the_event_is_written(self):
        module, _levels = built({"t1": "home"})
        module.transfer_tile(TransferTile("t1", "rival", "a treaty"))
        sent = module_harness.sent(module)
        self.assertEqual(sent[-2], FollowTileTransfer("t1", "home", "rival"))
        self.assertIsInstance(sent[-1], RecordWorldEvent)

    def test_a_tile_off_the_map_is_refused_by_the_rule(self):
        module, _levels = built({"t1": "home"})
        with self.assertRaises(tile_owners.TileOwnerError):
            module.transfer_tile(TransferTile("nowhere", "rival", "test"))

    def test_the_tile_control_is_the_control_stores_value(self):
        module, _levels = built({"t1": "home", "t2": "home"}, Levels(t1="garrisoned"))
        self.assertEqual((module.tile_control("t1"), module.tile_control("t2")), ("garrisoned", None))

    def test_the_owners_of_tiles_and_the_tiles_of_owners(self):
        module, _levels = built({"t1": "home", "t2": "gaul", "t3": "home"})
        self.assertEqual((module.tile_owner("t2"), module.tile_owner("far_tile")), ("gaul", None))
        self.assertEqual((module.tiles_owned_by("home"), module.tiles_owned_by("nobody")), (["t1", "t3"], []))

    def test_the_home_tiles_are_the_civilisations_own_tiles_among_the_owned(self):
        module, _levels = built({"t1": "home", "t2": "gaul"}, views={"civilisation": {"id": "home", "home_tiles": ["t1", "t2"]}})
        self.assertEqual(module.home_tiles_held(), ["t1"])

    def test_a_transfer_changes_the_version_and_the_lists_the_owners_memo_keeps(self):
        module, _levels = built({"t1": "home", "t2": "gaul"}, views={"civilisation": {"id": "home", "home_tiles": ["t1", "t2"]}})
        version = module.home_tiles_held_version()
        self.assertEqual(module.home_tiles_held_version(), version)
        self.assertEqual(module.tiles_owned_by("gaul"), ["t2"])
        module.transfer_tile(TransferTile("t2", "home", "test"))
        self.assertNotEqual(module.home_tiles_held_version(), version)
        self.assertEqual((module.home_tiles_held(), module.tiles_owned_by("gaul")), (["t1", "t2"], []))

    def test_an_empty_owner_map_is_seeded_from_the_civilisation_files_and_its_levels_written(self):
        module, levels = built(views={"civilisation": {"id": "home", "home_tiles": ["t1"]}, "partners_in_agent_economy": ["gaul"],
                                      "civilisation_record": {"gaul": {"id": "gaul", "home_tiles": ["t1", "t2"]}}})
        self.assertEqual(module.tile_owner_map(), {"t1": {"owner": "home"}, "t2": {"owner": "gaul"}})
        self.assertEqual(module.world.tile_claim_conflicts, [{"tile": "t1", "owner": "home", "claimant": "gaul"}])
        self.assertEqual(levels.values, {"t1": tile_owners.seed_level(), "t2": tile_owners.seed_level()})

    def test_the_problems_name_a_tile_two_seats_both_list_and_an_unknown_level(self):
        module, _levels = built({"t1": "first"}, Levels(t1="no_such_level"), views={"seat_list": {"joined": ["first", "second"]}})
        module.seat_slot_of = lambda seat_id: LandSeat(colonies=[{"tile": "t1"}])
        causes = sorted(problem["cause"] for problem in module.tile_ownership_problems())
        self.assertEqual(causes, ["double_claim", "owned_by_other", "unknown_control"])


class FoundingAColony(unittest.TestCase):
    def founder(self, owner=None, by_land=("far_tile",), by_sea=("far_tile",), working_age=500.0, spendable=1000.0, cost=50.0,
                chosen=(CHARTER, SPEC)):
        module, levels = built({"t1": "home"} if owner is None else {"t1": "home", "far_tile": owner}, views={
            "year": 100, "plain_number": lambda value, digits=0: "%d" % value, "money_text": lambda amount, grouped=False: "money",
            "working_age": working_age, "spending_power": lambda kind: spendable})
        module.settlement_candidates = lambda by_sea_route=False: list(by_sea if by_sea_route else by_land)
        module.settlement_spec = lambda by_sea=False: chosen
        module.settlement_outfit_cost = lambda spec, tile_id=None: cost
        module.clock.act_as("founder")
        return module, levels

    def test_a_founded_colony_is_paid_for_takes_its_settlers_and_holds_its_tile_at_the_settlement_level(self):
        module, levels = self.founder()
        answer = module.found_colony(FoundColony("far_tile"))
        self.assertEqual((answer["tile"], answer["settlers"], answer["cost"]), ("far_tile", 20.0, 50.0))
        self.assertEqual(module.seat.colonies, [{"tile": "far_tile", "founded_year": 100, "by": CHARTER,
                                                 "children": 0.0, "working_age": 20.0, "elderly": 0.0}])
        self.assertEqual(module.tile_owner("far_tile"), "founder")
        self.assertEqual(levels.values["far_tile"], tile_owners.settlement_level())
        kinds = [type(command) for command in module_harness.sent(module)]
        self.assertEqual(kinds[:2], [PayEdge, SendSettlers])
        self.assertEqual(kinds[-1], RecordEvent)
        self.assertEqual(module_harness.sent(module)[1], SendSettlers(20.0))

    def test_each_cause_of_refusal_pays_moves_and_records_nothing(self):
        for label, cause, arguments in (("a tile already held", "tile_held", dict(owner="someone")),
                                        ("a tile settlers cannot reach", "unreachable", dict(by_land=(), by_sea=())),
                                        ("no known work", "no_settlement_work", dict(chosen=None)),
                                        ("too few working people", "too_few_people", dict(working_age=10.0)),
                                        ("an outfit past what can be raised", "cannot_afford", dict(spendable=10.0))):
            with self.subTest(label):
                module, _levels = self.founder(**arguments)
                answer = module.found_colony(FoundColony("far_tile"))
                self.assertIsInstance(answer, Refusal)
                self.assertEqual(answer.cause, cause)
                self.assertEqual((module.seat.colonies, module_harness.sent(module)), ([], []))

    def test_a_tile_reachable_only_by_sea_asks_for_a_work_that_crosses_the_sea(self):
        module, _levels = self.founder(by_land=(), by_sea=("far_tile",))
        asked = []
        module.settlement_spec = lambda by_sea=False: asked.append(by_sea) or (CHARTER, SPEC)
        module.found_colony(FoundColony("far_tile"))
        self.assertEqual(asked, [True])


class TheColoniesYear(unittest.TestCase):
    def advanced(self, people, burden=0.5):
        module, levels = built({"afghanistan_01": "founder", "t1": "home"}, Levels(afghanistan_01=tile_owners.settlement_level()),
                               views={"disease_burden": burden, "seat_list": {"joined": ["founder"]}})
        colony = dict({"tile": "afghanistan_01", "founded_year": 100, "by": CHARTER}, **people)
        module.seat = LandSeat(colonies=[colony])
        module.seat_slot_of = lambda seat_id: module.seat
        module.clock.act_as("founder")
        module.advance_colonies(AdvanceColonies(120))
        return module, levels

    def test_a_colony_whose_people_die_out_is_lost_and_its_tile_freed_and_the_log_says_so(self):
        module, levels = self.advanced({"children": 0.0, "working_age": 0.0, "elderly": 0.0})
        self.assertEqual(module.seat.colonies, [])
        self.assertIsNone(module.tile_owner("afghanistan_01"))
        event = module_harness.sent(module)[-1]
        self.assertEqual((event.kind, event.facts, event.year), ("colony_died_out", {"tile": "afghanistan_01"}, 120))

    def test_a_colony_that_lives_on_is_kept_with_its_tile(self):
        module, _levels = self.advanced({"children": 50.0, "working_age": 200.0, "elderly": 10.0})
        self.assertEqual(len(module.seat.colonies), 1)
        self.assertEqual(module.tile_owner("afghanistan_01"), "founder")


class WhatTheGeographyReads(unittest.TestCase):
    def test_it_reads_the_held_technologies_the_ways_built_and_the_civilisation_through_the_views(self):
        module, _levels = built(views={"held_techniques": lambda include_starting: {"a"} if include_starting else set(),
                                       "built_ways": {"t1|t2": {"road": True}} , "pop_scale": 2.0,
                                       "civilisation_record": {"gaul": {"id": "gaul"}}})
        world = GeographyInputs(module)
        self.assertEqual((world.held_nodes, world.pop_scale, world.civ), ({"a"}, 2.0, {"id": "home"}))
        self.assertIs(world.world_map, MAP)
        self.assertEqual(world.civilisation("gaul"), {"id": "gaul"})
        self.assertIsNone(world.civilisation("nobody"))

    def test_the_ways_built_are_the_worlds_record_in_place(self):
        module, _levels = built()
        module.world.improvements["t1|t2"] = {"road": True}
        self.assertIs(module.built_ways(), module.world.improvements)

    def test_a_tile_known_is_one_the_map_has(self):
        module, _levels = built()
        self.assertEqual((module.tile_known("t1"), module.tile_known("elsewhere")), (True, False))


class TheTerritoryRule(unittest.TestCase):
    def test_a_civilisation_that_holds_no_tile_is_refused_naming_where_its_claim_is_declared(self):
        with self.assertRaises(ValueError):
            rules.require_territory({"id": "nowhere"}, [])
        rules.require_territory({"id": "somewhere"}, ["t1"])


if __name__ == "__main__":
    unittest.main()
