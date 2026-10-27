"""A defence credited to guns and walls needs powder in a magazine and a garrison present (Complaint 245).

A `hazard_counters` entry may name a `magazine` (material held in the stock ledger), and a node may
name a `garrison` (trades from the labour market). The powder works, while running, banks powder
into the ledger from its crew's hours; a live threat draws it down; a counter whose magazine ran dry
or whose garrison is not present counts for the part that is. Small fixtures, no whole game.
"""

QUICK_TOPIC = True

import collections
import random
import unittest

from types import SimpleNamespace

from sim.defence_stores.module import DefenceStores
from sim.engine import cash_remedies  # noqa: F401  (settles the import cycle through project_materials)
from sim.engine import validate_defence_stores
from sim.engine.forward_mechanics import ForwardMechanicsMixin
from sim.mechanics.module import Mechanics
from sim.living_stock.api import ChangeHeld
from sim.tests import module_harness
from sim.engine.projects_open_gate import OpenGateMixin
from sim.engine.projects_staffing_shortfall import StaffingShortfallMixin
from sim.engine.projects_ventures import VenturesMixin
from sim.tests import hazards_host
from sim.workforce.api import SurviveStaff
from sim.workforce.module import Workforce

POWDER_KG = "gunpowder_kg"
WORKS, GUNS, WALL = "powder_works", "gun", "wall"


def _nodes():
    return {
        WORKS: {"id": WORKS, "name": "Powder works", "up": 5.0, "rev": 1.0, "sch": 1.0, "art": 3.0,
                "mechanics": {"banks_output": {"material": POWDER_KG, "per_labour_hour": 2.0}}},
        GUNS: {"id": GUNS, "name": "Guns", "up": 0.0, "rev": 0.0, "garrison": {"soldier": 10},
               "mechanics": {"hazard_counters": [{
                   "kind": "sack_chance", "share": 0.4, "label": "guns on the walls", "order": 0,
                   "requires_running": [WORKS], "magazine": {POWDER_KG: 1000.0},
                   "draws": {POWDER_KG: 400.0}}]}},
        WALL: {"id": WALL, "name": "Wall", "up": 3.0, "rev": 0.0, "garrison": {"soldier": 20},
               "mechanics": {"hazard_counters": [{
                   "kind": "sack_chance", "share": 0.5, "label": "a bastioned enclosure", "order": 1}]}},
    }


class _Keyed:
    def __init__(self, answer):
        self.answer = answer

    def __getitem__(self, key):
        return self.answer(key)


class _Host(ForwardMechanicsMixin):
    """The fake game the other mixins run on, with the defence-stores module built over it by the harness: its views are
    this host's plain values, and a ChangeHeld it sends changes the host's ledger (kilograms are a thousandth of a tonne)."""
    HOURS_PER_PERSON_YEAR = 2000.0
    civ_diffusion_share = 0.0

    def civ_diffusion(self, node_id):
        return self.civ_diffusion_share

    def __init__(self, powder_kg=0.0, soldiers=0.0, works_open=True, wall_open=True, year=100):
        self.nodes = _nodes()
        done = {WORKS, GUNS, WALL}
        operating = {name for name, flag in ((WORKS, works_open), (WALL, wall_open)) if flag}
        self.ledger = collections.Counter({POWDER_KG: powder_kg / 1000.0})
        self.civ = {"hazards": [{"name": "siege", "years": [year, year + 2], "sack_chance": 0.5}]}
        self.year = year
        self.state = SimpleNamespace(
            projects=SimpleNamespace(done=done, granted=set(), operating=operating, closures={}),
            household=SimpleNamespace(employees={"soldier": soldiers}, log=[], _stock_throttle_sig=None),
            scenario=SimpleNamespace(year=year))
        self.mechanics = module_harness.build(Mechanics, views={
            "tree_nodes": self.nodes, "running": self.running,
            "techniques_held": lambda: self.state.projects.done, "institution_units": self.institution_units,
            "money_per_labour_hour": 1.0})
        self.hazards = hazards_host.build(
            civilisation=self.civ, year=lambda: self.state.scenario.year, hazard_counter_rows=self.mechanics.hazard_counter_rows,
            techniques_held=lambda: self.state.projects.done, running=self.running, tree=self.nodes.get,
            counter_supply_gap=lambda node_id, kind, label: self.counter_supply_gap(node_id, kind, label),
            civ_diffusion=self.civ_diffusion)
        self.defence = module_harness.build(DefenceStores, views={
            "tree": self.nodes.get, "techniques_held": lambda: self.state.projects.done,
            "operating": lambda: self.state.projects.operating, "is_venture": self.is_venture,
            "staff": lambda: {"employees": self.state.household.employees},
            "stock_held": self.stock_held, "year": lambda: self.state.scenario.year,
            "live_hazard_kinds": self.hazards.live_hazard_kinds,
            "running_mechanics": self.mechanics.running_mechanics,
            "hours_per_person_year": lambda: self.HOURS_PER_PERSON_YEAR, "institution_units": self.institution_units,
            "effects_in_force": self.mechanics.effects_in_force},
            answers={ChangeHeld: self.change_held})

    def view(self, name):
        """The published view `name`, as the mechanics module answers it."""
        if name == "staff":
            return lambda: {"employees": self.state.household.employees, "directors_extra": 0.0, "artisans": 0.0, "scholars": 0.0}
        return _Keyed(self.mechanics.mechanic) if name == "mechanic" else getattr(self.mechanics, name)

    def stock_held(self, material):
        return self.ledger.get(material, 0.0) * 1000.0

    def change_held(self, command):
        self.ledger[command.material] = self.ledger.get(command.material, 0.0) + command.units / 1000.0

    def venture_garrison(self, node_id, units=1.0):
        return self.defence.venture_garrison(node_id, units)

    def garrison_claims(self):
        return self.defence.garrison_claims()

    def counter_supply_gap(self, node_id, kind, label):
        return self.defence.counter_supply_gap(node_id, kind, label)

    def step_defence_stores(self):
        self.defence.step_defence_stores("seat")

    def has(self, node_id):
        return node_id in self.state.projects.done

    def running(self, node_id):
        return node_id in self.state.projects.operating or not self.is_venture(node_id)

    def is_venture(self, node_id):
        return self.nodes[node_id]["up"] > 0 or self.nodes[node_id]["rev"] > 0

    def institution_units(self, node_id):
        return 1.0 if self.running(node_id) else 0.0

    def hazard_relief_entries(self, kind, beyond_national=False):
        return self.hazards.hazard_relief_entries(kind, beyond_national)

    def hazard_relief(self, kind, beyond_national=False):
        return self.hazards.hazard_relief(kind, beyond_national)

    def _entry_words(self, entry):
        return self.hazards._entry_words(entry)


def _factor(host, label):
    return [entry for entry in host.hazard_relief_entries("sack_chance") if entry["label"] == label]


class PowderIsAHeldMaterial(unittest.TestCase):

    def test_a_running_works_banks_powder_from_its_crew_hours(self):
        host = _Host()
        host.step_defence_stores()
        crew_hours = (1.0 + 3.0) * host.HOURS_PER_PERSON_YEAR
        self.assertAlmostEqual(host.stock_held(POWDER_KG), crew_hours * 2.0)

    def test_the_threat_spends_before_the_works_restocks(self):
        host = _Host(powder_kg=1000.0)
        host.step_defence_stores()
        self.assertAlmostEqual(host.stock_held(POWDER_KG), 1000.0 - 400.0 + 4.0 * 2000.0 * 2.0)

    def test_a_shut_works_banks_nothing(self):
        host = _Host(works_open=False)
        host.step_defence_stores()
        self.assertEqual(host.stock_held(POWDER_KG), 0.0)

    def test_a_live_threat_draws_the_stock_down_but_never_below_nothing(self):
        host = _Host(powder_kg=100.0, works_open=False)
        host.step_defence_stores()
        self.assertEqual(host.stock_held(POWDER_KG), 0.0)

    def test_no_threat_this_year_draws_nothing(self):
        host = _Host(powder_kg=900.0, works_open=False, year=50)
        host.civ["hazards"][0]["years"] = [200, 210]
        host.step_defence_stores()
        self.assertEqual(host.stock_held(POWDER_KG), 900.0)


class GunsNeedThePowderWorksRunning(unittest.TestCase):

    def test_guns_lapse_while_the_powder_works_is_closed(self):
        host = _Host(powder_kg=1000.0, soldiers=30.0, works_open=False)
        entry = _factor(host, "guns on the walls")[0]
        self.assertEqual(entry["lapsed_node"], WORKS)
        self.assertIn("lapsed", host.hazard_relief("sack_chance")[1][0])

    def test_closing_the_powder_works_weakens_the_defence(self):
        closed = _Host(powder_kg=1000.0, soldiers=30.0, works_open=False).hazard_relief("sack_chance")[0]
        running = _Host(powder_kg=1000.0, soldiers=30.0, works_open=True).hazard_relief("sack_chance")[0]
        self.assertGreater(closed, running)

    def test_guns_count_while_the_powder_works_runs(self):
        entry = _factor(_Host(powder_kg=1000.0, soldiers=30.0, works_open=True), "guns on the walls")[0]
        self.assertIsNone(entry["lapsed_node"])


class HazardLabelsFollowTheMechanics(unittest.TestCase):
    """The words on a defence say what the mechanics did: lapsed only when the concern is closed, and the national
    adoption it was discounted by."""

    def _wall(self, host):
        return [entry for entry in host.hazard_relief_entries("sack_chance", beyond_national=True)
                if entry["label"] == "a bastioned enclosure"][0]

    def test_a_running_counter_partly_adopted_nationally_is_not_lapsed(self):
        host = _Host(powder_kg=1000.0, soldiers=30.0)
        host.civ_diffusion_share = 0.4
        entry = self._wall(host)
        self.assertAlmostEqual(entry["factor"], 1.0 - 0.5 * 0.6)
        words = host._entry_words(entry)
        self.assertNotIn("lapsed", words)
        self.assertNotIn("is closed", words)

    def test_national_adoption_is_named_in_the_label(self):
        host = _Host(powder_kg=1000.0, soldiers=30.0)
        host.civ_diffusion_share = 0.4
        self.assertTrue(self._wall(host)["partly_adopted_nationally"])
        self.assertIn("adopted nationally", host._entry_words(self._wall(host)))

    def test_a_closed_concern_is_still_labelled_lapsed(self):
        host = _Host(powder_kg=1000.0, soldiers=30.0, wall_open=False)
        entry = self._wall(host)
        self.assertEqual(entry["lapsed_node"], WALL)
        self.assertIn("lapsed", host._entry_words(entry))
        self.assertLess(entry["factor"], 1.0)


class _Survivors:
    """The people of a household and the dice that decide who lives (the workforce module's SurviveStaff)."""

    def __init__(self, seed):
        self.rng = random.Random(seed)
        self.state = SimpleNamespace(household=SimpleNamespace(
            scholars=7.0, artisans=9.0, employees={"carpenter": 3.0, "smith": 5.0}))

    def apply_staff_survival(self, survival_share):
        workforce = module_harness.build(Workforce, seat=self.state.household, views={"legacy_acting_household": self.state.household, "legacy_dice": self.rng})
        workforce.survive_staff(SurviveStaff(survival_share))


class PeopleStayWhole(unittest.TestCase):

    def test_a_shock_leaves_whole_people_and_never_more_than_before(self):
        for seed in range(6):
            for survival_share in (0.9, 0.5, 0.1, 0.0):
                host = _Survivors(seed)
                host.apply_staff_survival(survival_share)
                household = host.state.household
                counts = [household.scholars, household.artisans] + list(household.employees.values())
                self.assertEqual(counts, [float(round(count)) for count in counts], (seed, survival_share, counts))
                self.assertLessEqual(household.scholars, 7.0)
                self.assertLessEqual(household.artisans, 9.0)

    def test_a_trade_that_loses_everyone_leaves_the_books(self):
        host = _Survivors(1)
        host.apply_staff_survival(0.0)
        self.assertEqual(host.state.household.employees, {})

    def test_everyone_survives_a_share_of_one(self):
        host = _Survivors(1)
        host.apply_staff_survival(1.0)
        self.assertEqual((host.state.household.scholars, host.state.household.artisans), (7.0, 9.0))


class TheMagazineRunsDry(unittest.TestCase):

    def test_guns_with_a_full_magazine_count_in_full(self):
        entry = _factor(_Host(powder_kg=1000.0, soldiers=30.0), "guns on the walls")[0]
        self.assertAlmostEqual(entry["factor"], 1.0 - 0.4)
        self.assertIsNone(entry.get("short_of"))

    def test_a_half_empty_magazine_halves_the_credit_and_says_why(self):
        host = _Host(powder_kg=500.0, soldiers=30.0)
        entry = _factor(host, "guns on the walls")[0]
        self.assertAlmostEqual(entry["factor"], 1.0 - 0.4 * 0.5)
        self.assertIn("magazine", entry["short_of"])
        self.assertIn("magazine", host.hazard_relief("sack_chance")[1][0])

    def test_an_empty_magazine_leaves_no_credit_but_the_entry_says_why(self):
        entry = _factor(_Host(powder_kg=0.0, soldiers=30.0), "guns on the walls")[0]
        self.assertEqual(entry["factor"], 1.0)
        self.assertIn("magazine", entry["short_of"])


class TheGarrisonMustBePresent(unittest.TestCase):

    def test_guns_without_a_crew_do_not_count(self):
        entry = _factor(_Host(powder_kg=1000.0, soldiers=0.0), "guns on the walls")[0]
        self.assertEqual(entry["factor"], 1.0)
        self.assertIn("soldier", entry["short_of"])

    def test_the_trade_is_shared_between_the_works_that_claim_it(self):
        host = _Host(powder_kg=1000.0, soldiers=15.0)
        wall = _factor(host, "a bastioned enclosure")[0]
        self.assertAlmostEqual(wall["factor"], 1.0 - 0.5 * 0.5)
        self.assertIn("soldier", wall["short_of"])

    def test_a_fully_manned_wall_counts_in_full(self):
        wall = _factor(_Host(powder_kg=1000.0, soldiers=30.0), "a bastioned enclosure")[0]
        self.assertAlmostEqual(wall["factor"], 0.5)

    def test_a_shut_wall_claims_no_garrison(self):
        host = _Host(powder_kg=1000.0, soldiers=10.0, wall_open=False)
        self.assertEqual(host.garrison_claims(), {"soldier": 10.0})

    def test_an_open_concern_holds_its_garrison_like_a_foreman(self):
        host = _Host()
        self.assertEqual(host.venture_garrison(WALL), {"soldier": 20.0})
        self.assertEqual(host.venture_garrison(WORKS), {})


class _Staffed(VenturesMixin, OpenGateMixin, StaffingShortfallMixin, _Host):
    CAPABILITY_INSTITUTIONS = frozenset()
    FOUNDER_IS_WORTH = 0.0
    STAFFING_CLOSURE_SLACK = 0.5
    labour = SimpleNamespace(effective_scholars=lambda: 100.0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.state.household.artisans = 100.0
        self.founder_alive = False
        self.state.projects.keep_staffed = set()

    def venture_hands(self, node_id):
        return 0.0, 0.0

    def venture_staff_free(self):
        return 10.0, 10.0


class AGarrisonIsStaffedLikeAForeman(unittest.TestCase):

    def test_an_open_concern_draws_its_garrison_from_the_labour_market(self):
        host = _Staffed(soldiers=5.0)
        self.assertEqual(host._staffing_draw_of(WALL)["soldier"], 20.0)
        self.assertEqual(host.venture_foremen_used()["soldier"], 20.0)

    def test_opening_is_refused_while_the_garrison_is_not_free(self):
        host = _Staffed(soldiers=5.0, wall_open=False)
        self.assertIn("soldier", host.staffing_open_refusal(WALL))
        self.assertIsNone(_Staffed(soldiers=25.0, wall_open=False).staffing_open_refusal(WALL))

    def test_the_yearly_rule_sees_a_shortfall_when_the_soldiers_are_gone(self):
        host = _Staffed(soldiers=5.0)
        self.assertEqual(host.concerns_to_close_for_staffing(), [WALL])
        self.assertEqual(_Staffed(soldiers=25.0).concerns_to_close_for_staffing(), [])


class TheDataNamesRealThings(unittest.TestCase):

    def _check(self, nodes):
        return validate_defence_stores.check_defence_stores(nodes, {"soldier"}, {POWDER_KG})

    def test_the_shipped_shape_is_accepted(self):
        self.assertEqual(self._check(_nodes()), [])

    def test_an_unknown_trade_or_material_is_named(self):
        nodes = _nodes()
        nodes[WALL]["garrison"] = {"pikeman": 5}
        nodes[GUNS]["mechanics"]["hazard_counters"][0]["magazine"] = {"saltpetre_kg": 1}
        errors = " ".join(self._check(nodes))
        self.assertIn("pikeman", errors)
        self.assertIn("saltpetre_kg", errors)

    def test_banking_on_a_work_that_cannot_run_is_refused(self):
        nodes = _nodes()
        nodes[WORKS].update(up=0.0, rev=0.0)
        self.assertIn("cannot run", " ".join(self._check(nodes)))


if __name__ == "__main__":
    unittest.main()
