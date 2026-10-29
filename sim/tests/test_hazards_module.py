"""The hazards module on plain values: the order of the commands a dated shock sends and of the dice it draws, the output factor
a war lowers and the state recovers, the capital a catastrophe destroys, the yearly chances, and the world event log's commands.
Each test builds the module with `hazards_host` and reads the commands it sent. The rules are in test_hazards_rules."""
QUICK_TOPIC = True

import unittest

from sim.agents.api import edges
from sim.coin.api import PlunderHousehold
from sim.hazards import constants
from sim.hazards.commands import LoseCapital, RecordWorldEvent, RecoverOutput
from sim.hazards.state import HazardsSeat, HazardsWorld
from sim.reporting.api import ErodeMoney, RecordEvent
from sim.tests import hazards_host, module_harness


class Script:
    """Dice that answer a fixed list of draws and fail when asked for more, so the number and order of draws is pinned."""

    def __init__(self, *draws):
        self.draws = list(draws)
        self.asked = 0

    def random(self):
        self.asked += 1
        return self.draws.pop(0)


def civilisation(*hazards):
    return {"id": "rome", "hazards": list(hazards)}


def plague(**fields):
    return dict({"name": "Plague", "years": [150, 160], "staff_loss": 0.3}, **fields)


def names(module):
    return [type(command).__name__ for command in module_harness.sent(module)]


class DatedShocks(unittest.TestCase):

    def test_a_game_without_events_meets_no_hazard_and_has_no_disaster(self):
        module = hazards_host.build(year=155, events_enabled=False, civilisation=civilisation(plague()))
        module.step_dated_shocks(["founder"])
        self.assertEqual(module_harness.sent(module), [])
        self.assertIsNone(module.disaster())

    def test_a_hazard_outside_its_window_sends_nothing_and_draws_nothing(self):
        dice = Script()
        module = hazards_host.build(year=100, civilisation=civilisation(plague()), game_random=dice)
        module.step_dated_shocks(["founder"])
        self.assertEqual((module_harness.sent(module), dice.asked), ([], 0))

    def test_a_wave_that_the_yearly_chance_spares_costs_one_draw_and_nothing_else(self):
        dice = Script(constants.STAFF_LOSS_HAZARD_ANNUAL_CHANCE + 0.01)
        module = hazards_host.build(year=155, civilisation=civilisation(plague()), game_random=dice)
        module.step_dated_shocks(["founder"])
        self.assertEqual((module_harness.sent(module), dice.asked), ([], 1))

    def test_a_wave_costs_the_seat_its_people_and_cash_then_cuts_the_population_once_and_tells_the_seat(self):
        dice = Script(0.0)
        module = hazards_host.build(
            year=155, civilisation=civilisation(plague()), game_random=dice, acting_balance=1000.0,
            staff={"scholars": 2.0, "artisans": 3.0, "employees": {"smith": 5.0}}, staff_snapshot={"smith": 5.0}, wage_index=1.5)
        module.step_dated_shocks(["founder"])
        self.assertEqual(names(module), ["SurviveStaff", "ScaleDeputies", "ReportStaffReduction", "PayEdge", "CutPopulation",
                                         "NoteWageShock", "RefreshDemographicIndexes", "RecordEvent"])
        survive, deputies, report, pay, cut, wage, refresh, line = module_harness.sent(module)
        self.assertAlmostEqual(survive.survival_share, 0.7)
        self.assertEqual(deputies.share, survive.survival_share)
        self.assertEqual((report.cause, report.before), ("Plague", {"smith": 5.0}))
        self.assertEqual((pay.edge, pay.purpose), (edges.EDGE_DESTROYED, "plague losses"))
        self.assertAlmostEqual(pay.amount, 1000.0 * 0.3 * constants.PLAGUE_CASH_LOSS_SHARE)
        self.assertAlmostEqual(cut.share, 0.3)
        self.assertEqual((wage.cause, wage.index_before, refresh.year), ("Plague", 1.5, 155))
        self.assertEqual((line.kind, line.seat, line.facts["hazard"]), ("hazard_hit", "founder", "Plague"))
        self.assertEqual(dice.asked, 1)

    def test_the_year_remembers_what_struck_and_what_the_seat_was_told(self):
        module = hazards_host.build(year=155, civilisation=civilisation(plague()), game_random=Script(0.0))
        module.step_dated_shocks(["founder"])
        self.assertEqual(module.disaster()["name"], "Plague")

    def test_a_war_lowers_the_world_output_factor_once_to_the_highest_floor_and_says_so(self):
        war = {"name": "Civil war", "years": [150, 160], "output_factor": 0.6}
        world = HazardsWorld()
        module = hazards_host.build(year=155, world=world, civilisation=civilisation(war))
        module.step_dated_shocks(["founder"])
        self.assertAlmostEqual(world.output_factor, 0.6)
        line, = [command for command in module_harness.sent(module) if isinstance(command, RecordEvent)]
        self.assertEqual(line.kind, "hazard_output_fall")
        module.step_dated_shocks(["founder"])
        self.assertEqual(world.output_factor, 0.6)
        self.assertEqual(len([c for c in module_harness.sent(module) if isinstance(c, RecordEvent)]), 1, "told once in twenty years")

    def test_a_hazard_whose_condition_is_met_loses_the_field_it_names(self):
        war = {"name": "Grain fleet", "years": [150, 160], "output_factor": 0.6,
               "condition": {"field": "output_factor", "requires_all": ["rotation"], "outcome": "avert"}}
        world = HazardsWorld()
        module = hazards_host.build(year=155, world=world, civilisation=civilisation(war), techniques_held={"rotation"})
        module.step_dated_shocks(["founder"])
        self.assertEqual(world.output_factor, 1.0)

    def test_a_debasement_erodes_the_coin_once(self):
        module = hazards_host.build(year=155, civilisation=civilisation({"name": "Debasement", "years": [150, 160], "real_erosion": 0.2}))
        module.step_dated_shocks(["founder"])
        eroded, = [command for command in module_harness.sent(module) if isinstance(command, ErodeMoney)]
        self.assertEqual(eroded.share, 0.2)


class Recovery(unittest.TestCase):

    def test_a_crushed_output_recovers_by_the_base_rate_and_a_whole_one_is_left_alone(self):
        world = HazardsWorld(output_factor=0.5)
        module = hazards_host.build(world=world, military_leverage=0.0)
        module.recover_output(RecoverOutput())
        self.assertAlmostEqual(world.output_factor, 0.5 + constants.OUTPUT_RECOVERY_RATE)
        whole = HazardsWorld()
        hazards_host.build(world=whole).recover_output(RecoverOutput())
        self.assertEqual(whole.output_factor, 1.0)

    def test_an_armed_state_recovers_faster(self):
        armed, unarmed = HazardsWorld(output_factor=0.5), HazardsWorld(output_factor=0.5)
        hazards_host.build(world=armed, military_leverage=1.0).recover_output(RecoverOutput())
        hazards_host.build(world=unarmed, military_leverage=0.0).recover_output(RecoverOutput())
        self.assertGreater(armed.output_factor, unarmed.output_factor)

    def test_the_output_factor_is_the_view_of_the_world_state(self):
        self.assertEqual(hazards_host.build(world=HazardsWorld(output_factor=0.8)).output_factor(), 0.8)


class Capital(unittest.TestCase):

    def test_a_catastrophe_destroys_a_share_of_what_is_held(self):
        module = hazards_host.build(acting_balance=1000.0)
        self.assertEqual(module.lose_capital_command(LoseCapital(0.25, "fire")), 250.0)
        pay, = module_harness.sent(module)
        self.assertEqual((pay.edge, pay.amount, pay.purpose), (edges.EDGE_DESTROYED, 250.0, "fire"))

    def test_it_never_pays_off_a_debt(self):
        module = hazards_host.build(acting_balance=-500.0)
        self.assertEqual(module.lose_capital(0.5, "fire"), 0.0)
        self.assertEqual(module_harness.sent(module), [])


class YearlyChances(unittest.TestCase):

    def test_a_year_of_no_luck_draws_three_dice_and_sends_nothing(self):
        dice = Script(0.99, 0.99, 0.99)
        module = hazards_host.build(game_random=dice)
        module.random_events_for_seat(100)
        self.assertEqual((module_harness.sent(module), dice.asked), ([], 3))

    def test_a_fire_destroys_a_share_of_the_purse_and_says_what_it_cost(self):
        module = hazards_host.build(game_random=Script(0.99, 0.0, 0.99), acting_balance=1000.0)
        module.random_events_for_seat(100)
        pay, line = module_harness.sent(module)
        self.assertEqual((pay.edge, line.kind), (edges.EDGE_DESTROYED, "fire"))
        self.assertAlmostEqual(pay.amount, 1000.0 * constants.FIRE_CAPITAL_LOSS)

    def test_banditry_plunders_the_household_by_its_exposure(self):
        module = hazards_host.build(game_random=Script(0.99, 0.99, 0.0))
        module.random_events_for_seat(100)
        plunder, line = module_harness.sent(module)
        self.assertEqual((plunder, line.kind), (PlunderHousehold(constants.BANDITRY_TAKE_STRENGTH, "banditry", True), "banditry"))

    def test_a_patron_dies_once_a_cooling_off_and_the_seat_remembers_the_year(self):
        seat = HazardsSeat()
        module = hazards_host.build(game_random=Script(0.0, 0.99, 0.99), seat=seat, running_mechanics=lambda name: [("patron", {})],
                                    standing={"protection": 0.9, "scandal": 0.0, "bribes_year_to_date": 0.0})
        module.random_events_for_seat(100)
        self.assertEqual(seat.last_patron_death, 100)
        self.assertEqual(names(module), ["RaiseScandal", "ScaleProtection", "PayEdge", "RecordEvent"])
        again = hazards_host.build(game_random=Script(0.0, 0.99, 0.99), seat=seat, running_mechanics=lambda name: [("patron", {})])
        again.random_events_for_seat(100 + constants.PATRON_DEATH_COOLDOWN_YEARS)
        self.assertEqual(module_harness.sent(again), [])

    def test_a_patron_who_is_not_mortal_does_not_die(self):
        module = hazards_host.build(game_random=Script(0.0, 0.99, 0.99))
        module.random_events_for_seat(100)
        self.assertEqual(module_harness.sent(module), [])

    def test_with_auto_court_heir_off_no_money_is_spent(self):
        module = hazards_host.build(game_random=Script(0.0, 0.99, 0.99), running_mechanics=lambda name: [("patron", {})],
                                    founder={"alive": True, "life_left": 1.0, "dead_reason": None, "policy": {"auto_court_heir": False}})
        module.random_events_for_seat(100)
        self.assertNotIn("PayEdge", names(module))

    def test_seats_that_ended_are_left_out_of_the_year(self):
        dice = Script(0.99, 0.99, 0.99)
        module = hazards_host.build(game_random=dice, ended_seats=["second"])
        module.step_random_events(["founder", "second"])
        self.assertEqual(dice.asked, 3)


class WorldEventLog(unittest.TestCase):

    def test_the_command_answers_the_record_it_wrote(self):
        world = HazardsWorld()
        module = hazards_host.build(year=120, world=world)
        entry = module.record_world_event(RecordWorldEvent("omen", actors=("rome",), cause="a comet", facts={"brightness": 2}))
        self.assertEqual(world.world_events, [entry])
        self.assertEqual((entry["year"], entry["kind"], entry["facts"]), (120, "omen", {"brightness": 2}))


if __name__ == "__main__":
    unittest.main()
