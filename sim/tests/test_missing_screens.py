"""Complaints 243, 96 and 270: the map, education, demography and divergence
screens. Each figure on a screen must equal what the engine's own function
returns, and a fogged player must not be shown a hidden node.
"""
import json
import os
import random
import sys
import unittest

_REPOSITORY_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
if _REPOSITORY_ROOT not in sys.path:
    sys.path.insert(0, _REPOSITORY_ROOT)
from sim import simulator
from sim.engine.core import Sim
from sim.engine.proto import command_registry
from sim.engine.proto.dispatch import _agent_dispatch
from sim.engine.proto.render import render_pretty
from sim.engine.proto.typed import parse_typed
from sim.world import deposits as deposit_model

_TREE, _PRICES, _NODES, _WAGES, _GOODS = simulator.load()


def _fresh_sim(civ="han_china_100ad", fog=False):
    sim = Sim(_NODES, list(_NODES), random.Random(1), civ=simulator.load_civ(civ))
    if fog:
        sim.fog = True
        sim.revealed = set()
    return sim


def _ask(sim, name, **fields):
    return _agent_dispatch(sim, _NODES, dict(cmd=name, **fields))


class RegistryTests(unittest.TestCase):

    def test_each_screen_is_registered_with_help(self):
        for name in ("map", "education", "demography", "divergence"):
            self.assertTrue(name in command_registry.COMMANDS, name)
            entry = command_registry.COMMANDS[name]
            self.assertTrue(entry["summary"] and entry["description"], name)

    def test_aliases_reach_the_screens(self):
        for word, name in (("map", "map"), ("country", "map"),
                           ("geography", "map"), ("education", "education"),
                           ("literacy", "education"), ("schools", "education"),
                           ("demography", "demography"),
                           ("divergence", "divergence")):
            command, error = parse_typed(word)
            self.assertIsNone(error, word)
            self.assertEqual(command["cmd"], name, word)


class MapTests(unittest.TestCase):

    def test_map_names_the_base_and_every_held_tile(self):
        sim = _fresh_sim()
        reply = _ask(sim, "map", full=True)
        self.assertTrue(reply["ok"], reply)
        base = reply["you_are_based_at"]
        self.assertEqual(base["tile"], sim.base_tile())
        self.assertNotEqual(base["name"], base["tile"])
        self.assertTrue(base["region"])
        held = sim.settlement_tiles()
        self.assertEqual({row["tile"] for row in reply["tiles"]}, set(held))
        for row in reply["tiles"]:
            self.assertEqual(row["people"], round(held[row["tile"]]))
            self.assertNotEqual(row["name"], row["tile"])
            self.assertTrue(row["terrain"])

    def test_the_town_figure_is_the_engines(self):
        sim = _fresh_sim()
        reply = _ask(sim, "map")
        self.assertEqual(reply["you_are_based_at"]["town_people"],
                         round(sim.home_town_population_estimate()))

    def test_deposits_on_held_tiles_are_listed(self):
        sim = _fresh_sim("rome_100ad")
        reply = _ask(sim, "map", full=True)
        listed = {(deposit["name"], row["tile"])
                  for row in reply["tiles"] for deposit in row["deposits"]}
        held = set(sim.settlement_tiles())
        expected = {(deposit.name, deposit.tile)
                    for metal in deposit_model.METALS
                    for deposit in deposit_model.load_deposits(metal)
                    if deposit.tile in held}
        self.assertTrue(expected)
        self.assertEqual(listed, expected)

    def test_reach_lists_neighbours_not_held(self):
        sim = _fresh_sim()
        reply = _ask(sim, "map", full=True)
        held = set(sim.settlement_tiles())
        self.assertTrue(reply["next_door"])
        for row in reply["next_door"]:
            self.assertNotIn(row["tile"], held)
            self.assertNotEqual(row["name"], row["tile"])

    def test_move_rows_carry_names(self):
        sim = _fresh_sim()
        reply = _ask(sim, "move_base")
        self.assertTrue(reply["tiles"])
        for row in reply["tiles"]:
            self.assertTrue(row["name"])
            self.assertNotEqual(row["name"], row["tile"])
        self.assertTrue(reply["you_are_at_name"])

    def test_pretty_screen_prints_names(self):
        sim = _fresh_sim()
        reply = _ask(sim, "map")
        text = render_pretty("map", reply)
        self.assertIn(reply["you_are_based_at"]["name"], text)

    def test_fog_map_names_no_technology(self):
        sim = _fresh_sim(fog=True)
        text = json.dumps(_ask(sim, "map", full=True))
        for node_id in _NODES:
            if not sim.is_visible(node_id) and len(node_id) > 6:
                self.assertNotIn('"%s"' % node_id, text)


class EducationTests(unittest.TestCase):

    def test_figures_are_the_engines(self):
        sim = _fresh_sim()
        reply = _ask(sim, "education")
        self.assertTrue(reply["ok"], reply)
        literacy = reply["literacy"]
        self.assertEqual(literacy["general"],
                         round(float(sim.civ["literacy_general"]), 4))
        self.assertEqual(literacy["general_ceiling"],
                         round(sim.literacy_ceiling_general(), 4))
        self.assertEqual(literacy["elite_ceiling"],
                         round(sim.literacy_ceiling_elite(), 4))
        self.assertEqual(reply["schooling_flow"], round(sim._schooling_flow(), 4))
        self.assertEqual(reply["farm_share_of_hours"],
                         round(sim.farm_share_of_hours(), 4))

    def test_effective_flow_has_one_definition(self):
        sim = _fresh_sim()
        self.assertTrue(hasattr(sim, "effective_schooling_flow"))
        reply = _ask(sim, "education")
        self.assertEqual(reply["effective_schooling_flow"],
                         round(sim.effective_schooling_flow(), 4))

    def test_next_year_gain_matches_advance(self):
        sim = _fresh_sim()
        for node_id, spec in sim._effect_terms("schooling_flow"):
            if spec.get("required") and node_id in _NODES:
                sim.done.add(node_id)
                sim.operating.add(node_id)
        sim._done_changed()
        before = float(sim.civ["literacy_general"])
        predicted = _ask(sim, "education")["literacy"]["general_next_year"]
        sim._advance_literacy(sim.year)
        self.assertAlmostEqual(float(sim.civ["literacy_general"]), predicted, places=4)
        self.assertGreaterEqual(predicted, before)

    def test_exact_percent_against_ceiling(self):
        sim = _fresh_sim()
        reply = _ask(sim, "education")
        self.assertIn("share_of_ceiling_general", reply["literacy"])

    def test_pretty_screen(self):
        text = render_pretty("education", _ask(_fresh_sim(), "education"))
        self.assertIn("EDUCATION", text)
        self.assertIn("general", text)

    def test_fog_hides_unheard_school_nodes(self):
        sim = _fresh_sim(fog=True)
        reply = _ask(sim, "education")
        shown = {row["id"] for row in reply["schools"]}
        for node_id in shown:
            self.assertTrue(sim.is_visible(node_id), node_id)


class DemographyTests(unittest.TestCase):

    def test_cohorts_are_the_models(self):
        sim = _fresh_sim()
        reply = _ask(sim, "demography")
        self.assertTrue(reply["ok"], reply)
        self.assertEqual(reply["population"], round(sim.population.total))
        self.assertEqual(reply["cohorts"]["children"], round(sim.population.children))
        self.assertEqual(reply["cohorts"]["working_age"], round(sim.population.working_age))
        self.assertEqual(reply["cohorts"]["elderly"], round(sim.population.elderly))
        self.assertEqual(reply["disease_burden"], round(sim._disease_burden(), 4))

    def test_flows_after_a_year(self):
        sim = _fresh_sim()
        sim.step()
        flows = sim._last_demographic_step
        reply = _ask(sim, "demography")
        self.assertEqual(reply["last_year"]["births"], round(flows.births))
        self.assertEqual(reply["last_year"]["deaths"], round(flows.deaths))
        self.assertEqual(reply["last_year"]["nutrition_ratio"], round(flows.nutrition_ratio, 4))

    def test_trades_come_from_population_report(self):
        sim = _fresh_sim()
        reply = _ask(sim, "demography")
        report = sim.population_report()
        self.assertEqual([row["trade"] for row in reply["trades"]],
                         [row["trade"] for row in report["trades"]])

    def test_says_what_it_cannot_know(self):
        reply = _ask(_fresh_sim(), "demography")
        self.assertTrue(reply["not_held"])

    def test_pretty_screen(self):
        text = render_pretty("demography", _ask(_fresh_sim(), "demography"))
        self.assertIn("DEMOGRAPHY", text)
        self.assertIn("children", text)

    def test_population_no_longer_swallows_the_alias(self):
        self.assertEqual(command_registry.resolve("demography")["name"], "demography")


class DivergenceTests(unittest.TestCase):

    def test_fresh_run_has_not_diverged(self):
        sim = _fresh_sim()
        reply = _ask(sim, "divergence")
        self.assertTrue(reply["ok"], reply)
        self.assertEqual(reply["years_elapsed"], 0)
        self.assertEqual(reply["technologies_you_built"], [])
        self.assertEqual(reply["population"]["start"], round(sim.civ["population"]))
        self.assertEqual(reply["population"]["now"], round(sim.population.total))

    def test_a_built_technology_is_listed(self):
        sim = _fresh_sim()
        candidate = next(node_id for node_id in sorted(_NODES)
                         if node_id not in sim.done)
        sim.done.add(candidate)
        sim._done_changed()
        reply = _ask(sim, "divergence")
        self.assertIn(candidate, [row["id"] for row in reply["technologies_you_built"]])

    def test_literacy_and_indices_against_the_start(self):
        sim = _fresh_sim()
        start_literacy = float(sim.civ["literacy_general"])
        sim.civ["literacy_general"] = start_literacy + 0.1
        reply = _ask(sim, "divergence")
        self.assertEqual(reply["literacy_general"]["start"], round(start_literacy, 4))
        self.assertEqual(reply["literacy_general"]["now"], round(start_literacy + 0.1, 4))
        self.assertEqual(reply["wage_index"]["now"], round(sim.wage_index, 4))
        self.assertEqual(reply["price_index"]["now"], round(sim.price_index, 4))

    def test_dated_events_are_sorted_by_status(self):
        sim = _fresh_sim("rome_100ad")
        sim.year += 200
        reply = _ask(sim, "divergence")
        statuses = {row["status"] for row in reply["dated_events"]}
        self.assertIn("happened", statuses)
        self.assertTrue(statuses <= {"happened", "under way", "upcoming",
                                     "before the run began"})
        for row in reply["dated_events"]:
            self.assertIn("causes_checked", row)
            self.assertFalse(row["causes_checked"])

    def test_says_plainly_what_it_cannot_know(self):
        reply = _ask(_fresh_sim(), "divergence")
        self.assertTrue(reply["cannot_know"])
        self.assertIn("baseline", " ".join(reply["cannot_know"]).lower())

    def test_pretty_screen(self):
        text = render_pretty("divergence", _ask(_fresh_sim(), "divergence"))
        self.assertIn("DIVERGENCE", text)

    def test_fog_lists_only_nodes_the_player_has_built(self):
        sim = _fresh_sim(fog=True)
        candidate = next(node_id for node_id in sorted(_NODES)
                         if node_id not in sim.done and not sim.is_visible(node_id))
        reply = _ask(sim, "divergence")
        self.assertNotIn(candidate, json.dumps(reply))


if __name__ == "__main__":
    unittest.main()
