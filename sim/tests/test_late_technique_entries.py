"""Complaint 478: a technique the society gains after the opening adds the production entries it allows, their
trades' wages and the price of a good that had none, to the economy's opening values."""
QUICK_TOPIC = True

import types
import unittest
from unittest import mock

from sim.engine import economy_port_late
from sim.engine import economy_port_year
from sim.engine.economy_port_year import AgentEconomy
from sim.engine.economy_port_setup import allowed_entries

PRODUCTION = {
    "mortar_kg": {"outputs": {"mortar_kg": 1000.0}, "inputs": {"lime_kg": 500.0},
                  "labour_hours": {"labourer": 10.0}, "unit_dimension": "mass"},
    "cement_kg": {"outputs": {"cement_kg": 1000.0}, "inputs": {"lime_kg": 1000.0},
                  "labour_hours": {"kilnman": 20.0}, "unit_dimension": "mass", "requires_node": "kiln_node"},
    "cement_mint": {"outputs": {"coin": 1.0}, "labour_hours": {"smith": 1.0}, "actor": "mint",
                    "requires_node": "kiln_node"},
}
WAGES = {"labourer": 2.0, "kilnman": 5.0}


def stand_in_society(live_prices=None):
    economy = types.SimpleNamespace(agent_prices=lambda: live_prices, base_rate=lambda: 0.0,
                                    labour=types.SimpleNamespace(quote=lambda trade: WAGES.get(trade, 0.0)))
    return types.SimpleNamespace(economy=economy, civ={"id": "testland"})


def opening():
    return {"recipes": ["mortar_kg"], "prices": {"lime_kg": 1.0, "mortar_kg": 3.0}, "wages": {"labourer": 2.0}}


class AllowedEntries(unittest.TestCase):
    def test_an_entry_needing_a_node_waits_for_it_and_a_mint_entry_never_counts(self):
        self.assertEqual(allowed_entries(PRODUCTION, frozenset()), ["mortar_kg"])
        self.assertEqual(allowed_entries(PRODUCTION, frozenset({"kiln_node"})), ["cement_kg", "mortar_kg"])


class OpeningWithTechniques(unittest.TestCase):
    def test_nothing_new_allowed_adds_nothing(self):
        self.assertIsNone(economy_port_late.opening_with_techniques(
            stand_in_society(), opening(), frozenset(), PRODUCTION))

    def test_a_held_node_adds_its_recipe_its_trade_wage_and_the_price_of_the_good_it_makes(self):
        grown = economy_port_late.opening_with_techniques(
            stand_in_society(), opening(), frozenset({"kiln_node"}), PRODUCTION)
        self.assertEqual(grown["recipes"], ["cement_kg", "mortar_kg"])
        self.assertEqual(grown["wages"]["kilnman"], 5.0)
        self.assertIn("cement_kg", grown["prices"])
        self.assertGreater(grown["prices"]["cement_kg"], 0.0)
        self.assertNotIn("cement_kg", opening()["prices"])

    def test_a_good_that_already_has_a_price_keeps_it(self):
        base = opening()
        base["prices"]["cement_kg"] = 9.0
        grown = economy_port_late.opening_with_techniques(
            stand_in_society(), base, frozenset({"kiln_node"}), PRODUCTION)
        self.assertEqual(grown["prices"]["cement_kg"], 9.0)

    def test_the_new_good_costs_its_inputs_and_crew_at_live_input_prices_per_unit(self):
        cost = economy_port_late.late_goods_costs(
            stand_in_society({"lime_kg": 2.0}), {"lime_kg": 1.0}, ["cement_kg"], frozenset({"kiln_node"}), PRODUCTION)
        self.assertAlmostEqual(cost["cement_kg"], (1000.0 * 2.0 + 20.0 * 5.0) / 1000.0)

    def test_without_a_live_price_the_openings_input_price_is_used(self):
        cost = economy_port_late.late_goods_costs(
            stand_in_society(None), {"lime_kg": 1.0}, ["cement_kg"], frozenset({"kiln_node"}), PRODUCTION)
        self.assertAlmostEqual(cost["cement_kg"], (1000.0 * 1.0 + 20.0 * 5.0) / 1000.0)

    def test_a_good_whose_input_has_no_price_gets_none(self):
        self.assertEqual(economy_port_late.late_goods_costs(
            stand_in_society(), {}, ["cement_kg"], frozenset({"kiln_node"}), PRODUCTION), {})


class AdmitTechniquesWiring(unittest.TestCase):
    """EconomyPort.admit_techniques on a stand-in port: it looks again only when the held nodes changed."""

    def port(self, admitted, in_use):
        society = stand_in_society()
        society.state = types.SimpleNamespace(projects=types.SimpleNamespace(granted={"a"}))
        society.techniques_in_use = lambda: in_use
        return types.SimpleNamespace(_sim=society, _techniques_admitted=admitted, stored={"opening": opening()},
                                     _record_stale=False)

    def test_held_nodes_unchanged_since_the_last_look_leave_the_opening_alone(self):
        port = self.port(frozenset({"a", "b"}), {"b"})
        with mock.patch.object(economy_port_year, "default_production_entries", lambda: PRODUCTION):
            AgentEconomy.admit_techniques(port)
        self.assertEqual(port.stored["opening"], opening())
        self.assertFalse(port._record_stale)

    def test_held_nodes_that_allow_no_new_entry_are_remembered_and_change_nothing(self):
        port = self.port(frozenset(), {"b"})
        with mock.patch.object(economy_port_year, "default_production_entries", lambda: PRODUCTION):
            AgentEconomy.admit_techniques(port)
        self.assertEqual(port._techniques_admitted, frozenset({"a", "b"}))
        self.assertEqual(port.stored["opening"], opening())
        self.assertFalse(port._record_stale)


if __name__ == "__main__":
    unittest.main()
