"""The wage views and the views under them that are cached: each writer of what a view reads writes, the view is read again, and the
value is the fresh one. The writers are the clock's seat replacement, the scenario's two commands, the land module's hand-over of a
tile, the agriculture module's farm land, the market memory's write notice, `Economy.change_setup`, the repricing of the money and
the workforce's `move_base`; the workforce views are read through the shipped workforce spec over a stand-in that reports its
changes on one channel."""
QUICK_TOPIC = True

import dataclasses
import gc
import random
import unittest
from types import SimpleNamespace
from unittest import mock

from sim.agriculture.commands import SetFarmLand
from sim.agriculture.farm_state import FARM_LAND
from sim.assembly.api import Operations, assemble
from sim.economy import market_memory
from sim.economy.economy import Economy
from sim.labour.api import CAREER_YEARS, wages
from sim.economy.api import HOUSEHOLD_TIME_PREFERENCE
from sim.land.commands import TransferTile
from sim.land.module_spec import MODULE_SPECS as LAND_SPECS
from sim.land.ownership import OWNERS
from sim.markets.channels import MEMORY
from sim.markets.market_objects import MarketObjects
from sim.markets.module_spec import MODULE_SPECS as MARKETS_SPECS
from sim.scenario.api import OpenScenario, RecordOpeningLiteracy, ScenarioSources
from sim.scenario.module import CIVILISATION, Scenario
from sim.tests import agriculture_stand_in, assembly_fixture, land_host, module_harness, workforce_assembly
from sim.workforce.commands_people import MoveBase
from sim.workforce.module_spec import MODULE_SPECS as WORKFORCE_SPECS
from sim.workforce.state import BASE_TILE, WorkforceSeat, WorkforceSociety

RECORDS = {"digger": SimpleNamespace(family="earth", training_years=0.0, extra={"fallback": True}),
           "smith": SimpleNamespace(family="metal", training_years=4.0, extra={})}
HOME, TOWN = "france_05", "spain_03"      # two tiles of the base map; the household starts at TOWN, which it chose


class SeatReplaced(unittest.TestCase):
    def test_a_seat_put_whole_under_an_id_recomputes_what_was_cached_for_it(self):
        assembly = assembly_fixture.build()
        base, views, clock = assembly.modules["base"], assembly.views, assembly.clock
        base.per_seat = {"a": 5}
        clock.act_as("a")
        self.assertEqual(views["mine"](), 5)
        base.per_seat["a"] = 9           # what a handover does: the id now holds another seat's state, and no channel moved
        self.assertEqual(views["mine"](), 5)
        clock.seat_replaced("a")
        self.assertEqual(views["mine"](), 9)

    def test_replacing_one_seat_leaves_the_other_seats_entries(self):
        assembly = assembly_fixture.build()
        base, views, clock = assembly.modules["base"], assembly.views, assembly.clock
        base.per_seat = {"a": 5, "b": 7}
        clock.act_as("a")
        views["mine"]()
        clock.act_as("b")
        views["mine"]()
        clock.seat_replaced("a")
        views["mine"]()
        self.assertEqual(base.calls.count("mine"), 2)


class ScenarioChannel(unittest.TestCase):
    def opened(self):
        module = module_harness.build(Scenario, module_id="scenario", world=SimpleNamespace(year=100))
        module.open_scenario(OpenScenario(
            civilisation={"id": "rome", "year": 100, "literacy_general": 0.3, "literacy_elite": 0.9},
            configuration={"start_year": 100, "horizon_years": 500}, manual=True, events=False, bounty_set=set(),
            sources=ScenarioSources(load_civilisation=lambda civilisation_id: {}, kit_capital=lambda kit, civ: 0.0,
                                    display_units=lambda: ({}, {}, lambda: {})), dice=random.Random(1)))
        return module

    def test_opening_the_scenario_moves_the_civilisation_channel(self):
        module = module_harness.build(Scenario, module_id="scenario", world=SimpleNamespace(year=100))
        before = module.clock.counter("scenario", CIVILISATION, False)
        module.open_scenario(OpenScenario(
            civilisation={"id": "rome", "year": 100}, configuration={"start_year": 100, "horizon_years": 500}, manual=True, events=False,
            bounty_set=set(), sources=ScenarioSources(load_civilisation=lambda civilisation_id: {}, kit_capital=lambda kit, civ: 0.0,
                                                      display_units=lambda: ({}, {}, lambda: {})), dice=random.Random(1)))
        self.assertNotEqual(module.clock.counter("scenario", CIVILISATION, False), before)

    def test_moving_the_opening_literacy_off_the_civilisation_moves_the_channel(self):
        module = self.opened()
        before = module.clock.counter("scenario", CIVILISATION, False)
        module.record_opening_literacy(RecordOpeningLiteracy(0.25, 0.85))
        self.assertNotEqual(module.clock.counter("scenario", CIVILISATION, False), before)
        self.assertNotIn("literacy_general", module.civilisation_of_game())


class LandOwnersChannel(unittest.TestCase):
    def land(self):
        civilisation = {"id": "rome", "home_tiles": [HOME, TOWN]}
        return land_host.build(civilisation, views={"partners_in_agent_economy": lambda: [], "civilisation_record": {},
                                                    "store": {"control": {"values": {}, "default": "owned"}}})

    def test_a_transfer_moves_the_owners_channel_and_the_held_tiles_follow(self):
        land = self.land()
        self.assertEqual(land.home_tiles_held(), [HOME, TOWN])
        before = land.clock.counter("under_test", OWNERS, False)
        land.transfer_tile(TransferTile(HOME, "seat_a", "test"))
        self.assertNotEqual(land.clock.counter("under_test", OWNERS, False), before)
        self.assertEqual(land.home_tiles_held(), [TOWN])

    def test_the_view_is_cached_on_the_owners_channel_and_the_civilisation(self):
        spec = next(view for view in LAND_SPECS[0].publishes if view.name == "home_tiles_held")
        self.assertTrue(spec.cached)
        self.assertEqual((spec.channels, spec.inputs), ((OWNERS,), ("civilisation",)))


class FarmLandChannel(unittest.TestCase):
    def test_setting_the_farm_land_moves_the_channel(self):
        farm = agriculture_stand_in.build()
        before = farm.clock.counter("agriculture", FARM_LAND, False)
        farm.set_farm_land(SetFarmLand(120.0, 0.9))
        self.assertNotEqual(farm.clock.counter("agriculture", FARM_LAND, False), before)

    def test_a_refused_land_leaves_the_channel_where_it_was(self):
        farm = agriculture_stand_in.build()
        before = farm.clock.counter("agriculture", FARM_LAND, False)
        with self.assertRaises(ValueError):
            farm.set_farm_land(SetFarmLand(-1.0, 1.0))
        self.assertEqual(farm.clock.counter("agriculture", FARM_LAND, False), before)


@dataclasses.dataclass(frozen=True)
class _Setup:
    hours: float


class MarketMemoryWrites(unittest.TestCase):
    def test_every_write_notice_calls_a_listener_that_is_alive(self):
        told = []

        class Reader:
            def memory_written(self):
                told.append("written")
        reader = Reader()
        market_memory.add_write_listener(reader.memory_written)
        market_memory.note_written()
        self.assertEqual(told, ["written"])

    def test_a_listener_whose_owner_is_gone_is_not_called(self):
        told = []

        class Reader:
            def memory_written(self):
                told.append("written")
        reader = Reader()
        market_memory.add_write_listener(reader.memory_written)
        del reader
        gc.collect()
        market_memory.note_written()
        self.assertEqual(told, [])

    def test_the_markets_module_bumps_its_memory_channel_when_told(self):
        bumped = []
        MarketObjects.memory_written(SimpleNamespace(bump=bumped.append))
        self.assertEqual(bumped, [MEMORY])

    def test_changing_the_economys_setup_is_a_write_to_what_the_wage_rule_reads(self):
        economy = SimpleNamespace(setup=_Setup(1900.0))
        before = market_memory.written_stamp()
        Economy.change_setup(economy, hours=2100.0)
        self.assertEqual(economy.setup.hours, 2100.0)
        self.assertGreater(market_memory.written_stamp(), before)


class MarketsDeclaration(unittest.TestCase):
    def view(self, name):
        return next(view for view in MARKETS_SPECS[0].publishes if view.name == name)

    def test_the_wage_cell_and_the_working_hours_are_cached_on_the_memory_channel(self):
        for name in ("agent_wage_cell", "agent_working_hours"):
            self.assertTrue(self.view(name).cached, name)
            self.assertEqual(self.view(name).channels, (MEMORY,), name)

    def test_the_wage_quote_stays_uncached(self):
        self.assertFalse(self.view("agent_wage_at").cached)


class WorkforceWageViews(unittest.TestCase):
    """The workforce's cached views over a stand-in whose home tiles, wages, price level, farm land and civilisation report their
    changes on the channel `changed` (`bump`)."""
    WATCHED = ("home_tiles_held", "agent_wage_cell", "home_price_level", "civilisation", "farm_land", "trade_records")

    def setUp(self):
        self.tiles = [HOME, TOWN]
        self.wages = {}                  # (trade, tile) -> money per hour; empty: the money is not yet priced at the economy
        self.level = 2.0
        self.farm = SimpleNamespace(hectares=10.0)
        self.civilisation = {"id": "rome"}
        self.asked = []
        self.opening_money = 0.5
        self.build()

    def build(self, operations=()):
        def wage_cell(cell):
            self.asked.append(cell)
            return self.wages.get(cell)
        answers = {"trade_records": lambda: RECORDS, "home_tiles_held": lambda: list(self.tiles), "agent_wage_cell": wage_cell,
                   "home_price_level": lambda: self.level, "farm_land": lambda: self.farm, "civilisation": lambda: self.civilisation,
                   "agent_working_hours": lambda: None}
        spec = WORKFORCE_SPECS[0]
        every = {name: (lambda *arguments, _name=name: None) for name in spec.reads}
        stand_in = workforce_assembly.stand_in_spec(spec, {**every, **answers})
        reporting = tuple(dataclasses.replace(view, channels=("changed",)) if view.name in self.WATCHED else view
                          for view in stand_in.publishes)
        stand_in = dataclasses.replace(stand_in, channels=("changed",), publishes=reporting)
        self.assembly = assemble([spec, stand_in], list(operations))
        self.workforce = self.assembly.modules["workforce"]
        self.workforce.world, self.workforce.seat = WorkforceSociety(), WorkforceSeat(base_tile=TOWN)
        self.views = self.assembly.views
        schedule = wages.WageSchedule({"digger": 0.0, "smith": 4.0}, self.opening_money, 0.0, HOUSEHOLD_TIME_PREFERENCE, CAREER_YEARS)
        patch = mock.patch("sim.workforce.views_facts.opening_schedule", side_effect=lambda records, civ: schedule)
        patch.start()
        self.addCleanup(patch.stop)

    def bump(self):
        self.assembly.clock.bump("stand_in", "changed")

    # ---- the hour of the unskilled trade ----

    def test_before_the_money_is_priced_an_hour_is_the_opening_figure_at_the_price_level(self):
        self.assertAlmostEqual(self.views["money_per_labour_hour"](), 0.5 * 2.0)

    def test_the_price_level_moving_changes_the_hour(self):
        self.views["money_per_labour_hour"]()
        self.level = 3.0
        self.bump()
        self.assertAlmostEqual(self.views["money_per_labour_hour"](), 0.5 * 3.0)

    def test_once_the_economy_pays_an_hour_it_is_what_it_pays_at_the_base_tile(self):
        self.views["money_per_labour_hour"]()
        self.wages[("digger", TOWN)] = 7.0
        self.bump()
        self.assertEqual(self.views["money_per_labour_hour"](), 7.0)

    def test_the_hour_is_read_once_while_nothing_moves(self):
        self.wages[("digger", TOWN)] = 7.0
        for _read in range(4):
            self.views["money_per_labour_hour"]()
        self.assertEqual(self.asked, [("digger", TOWN)])

    def test_the_opening_hour_is_kept_until_the_civilisation_or_the_records_report_a_change(self):
        with mock.patch("sim.workforce.views_facts.opening_schedule", wraps=lambda records, civ: SimpleNamespace(money_per_labour_hour=0.5)) as built:
            self.views["opening_money_per_labour_hour"]()
            self.views["opening_money_per_labour_hour"]()
            self.assertEqual(built.call_count, 1)
            self.bump()
            self.views["opening_money_per_labour_hour"]()
            self.assertEqual(built.call_count, 2)

    # ---- the wage of a trade ----

    def test_the_wage_of_a_trade_is_the_economys_at_the_base_tile_and_follows_it(self):
        self.wages[("smith", TOWN)] = 3.0
        self.assertEqual(self.views["wage"]["smith"], 3.0)
        self.wages[("smith", TOWN)] = 4.5
        self.bump()
        self.assertEqual(self.views["wage"]["smith"], 4.5)

    def test_a_wage_is_kept_while_nothing_moves(self):
        self.wages[("smith", TOWN)] = 3.0
        for _read in range(3):
            self.views["wage"]["smith"]
        self.assertEqual(self.asked.count(("smith", TOWN)), 1)

    def test_before_the_money_is_priced_a_trade_is_paid_its_training_premium_over_the_hour(self):
        self.assertGreater(self.views["wage"]["smith"], self.views["wage"]["digger"])

    # ---- the base tile ----

    def test_the_base_tile_is_the_tile_the_household_chose_else_the_nations_default(self):
        self.assertEqual(self.views["base_tile"](), TOWN)
        self.assembly.clock.act_as("unplaced")
        self.workforce.seat = WorkforceSeat()
        self.tiles = [HOME]
        self.bump()
        self.assertEqual(self.views["base_tile"](), HOME)

    def test_moving_the_base_moves_the_tile_the_hour_is_paid_at(self):
        self.wages[("digger", TOWN)] = 7.0
        self.wages[("digger", HOME)] = 5.0
        self.assertEqual(self.views["money_per_labour_hour"](), 7.0)

        def move(tile):
            self.workforce.seat.base_tile = tile
            return True, "moved"
        with mock.patch.object(self.workforce.parts.core.labour.relocation, "move_base", side_effect=move):
            self.assembly.handlers[MoveBase](MoveBase(HOME))
        self.assertEqual(self.views["base_tile"](), HOME)
        self.assertEqual(self.views["money_per_labour_hour"](), 5.0)

    def test_losing_the_tile_the_household_chose_sends_it_to_the_nations_default(self):
        self.assertEqual(self.views["base_tile"](), TOWN)
        self.tiles = [HOME]
        self.bump()
        self.assertEqual(self.views["base_tile"](), HOME)

    def test_each_seat_has_its_own_base_tile_and_hour(self):
        self.wages[("digger", TOWN)] = 7.0
        self.wages[("digger", HOME)] = 5.0
        self.assembly.clock.act_as("a")
        self.workforce.seat = WorkforceSeat(base_tile=HOME)
        self.assertEqual(self.views["money_per_labour_hour"](), 5.0)
        self.assembly.clock.act_as("b")
        self.workforce.seat = WorkforceSeat(base_tile=TOWN)
        self.assertEqual(self.views["money_per_labour_hour"](), 7.0)

    def test_the_channel_a_move_bumps_is_the_seats(self):
        before = self.assembly.clock.counter("workforce", BASE_TILE, True)
        with mock.patch.object(self.workforce.parts.core.labour.relocation, "move_base", return_value=(True, "moved")):
            self.assembly.handlers[MoveBase](MoveBase(HOME))
        self.assertNotEqual(self.assembly.clock.counter("workforce", BASE_TILE, True), before)

    # ---- the farm ----

    def test_the_farm_hectares_are_the_farm_lands_and_follow_it(self):
        self.assertEqual(self.views["farm_land_hectares"](), 10.0)
        self.farm = SimpleNamespace(hectares=25.0)
        self.bump()
        self.assertEqual(self.views["farm_land_hectares"](), 25.0)

    # ---- a mod's adjuster ----

    def test_a_mod_adjuster_of_the_hour_still_applies_to_the_cached_view(self):
        adjust = Operations("doubler", adjusters={"money_per_labour_hour": ((lambda access, value: value * 2.0, ()),)})
        self.build(operations=[adjust])
        self.wages[("digger", TOWN)] = 7.0
        self.assertEqual(self.views["money_per_labour_hour"](), 14.0)
        self.assertEqual(self.views["money_per_labour_hour"](), 14.0)

    def test_a_mod_adjuster_of_the_wage_still_applies_to_each_trade(self):
        adjust = Operations("doubler", adjusters={"wage": ((lambda access, value, trade: value * 2.0, ()),)})
        self.build(operations=[adjust])
        self.wages[("smith", TOWN)] = 3.0
        self.assertEqual(self.views["wage"]["smith"], 6.0)


class WageViewsDeclared(unittest.TestCase):
    def specs(self):
        return {view.name: view for view in WORKFORCE_SPECS[0].publishes}

    def test_these_wage_and_source_views_are_cached(self):
        for name in ("money_per_labour_hour", "wage", "opening_money_per_labour_hour", "base_tile", "farm_land_hectares"):
            self.assertTrue(self.specs()[name].cached, name)

    def test_the_hour_and_the_wage_are_per_seat_and_read_the_wage_cell_and_the_price_level(self):
        for name in ("money_per_labour_hour", "wage"):
            self.assertTrue(self.specs()[name].seat_scoped, name)
            self.assertIn("agent_wage_cell", self.specs()[name].inputs, name)
            self.assertIn("home_price_level", self.specs()[name].inputs, name)

    def test_these_views_stay_uncached_because_they_read_state_that_reports_no_change(self):
        # the pre-economy wage reads prices, housing and output (labour_quote, market_annual_wage, wage_signature); the standing pay and the
        # seat's views read hours and trades labour writes in place; hours_per_person_year reads the works that run
        for name in ("labour_quote", "market_annual_wage", "wage_signature", "standing_job_pay", "capacity_job_pay", "base_annual_wage",
                     "hours_per_person_year", "settlement_tiles", "seat_base_tile", "available_trades"):
            self.assertFalse(self.specs()[name].cached, name)


if __name__ == "__main__":
    unittest.main()
