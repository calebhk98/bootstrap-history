"""Complaint 133: operating dependents of a built work require it running, not merely known.

Reads the authored branch files directly, so nothing here builds a game."""

QUICK_TOPIC = True

import glob
import json
import os
import unittest

from sim.engine import validate_running_gates
from sim.geography import queries, routes_graph, routes_modes

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# node -> works it must find running; the physical reasoning sits in each node's `_internal`.
EXPECTED_RUNNING = {
    "arc_furnace_ferroalloys": ["power_grid"],
    "electrolysis_industrial": ["power_grid"],
    "hom_electric_lighting": ["power_grid"],
    "civ_street_lighting": ["power_grid"],
    "pwr_hydroelectric_generation": ["power_grid"],
    "pwr_pumped_storage": ["power_grid"],
    "en_hydroelectric_station": ["power_grid"],
    "en_pumped_storage": ["power_grid"],
    "en_grid_interconnection": ["power_grid"],
    "el2_ring_main_distribution": ["power_grid"],
    "el2_trolleybus_catenary_power": ["power_grid"],
    "tl_electric_tram": ["power_grid"],
    "el2_electric_locomotive_traction_motor": ["power_grid"],
    "el2_load_dispatch_and_scheduling": ["power_grid", "telegraph_electric"],
    "fin_telegraph_business": ["telegraph_electric"],
    "com_stock_ticker": ["telegraph_electric"],
    "mil_chain_home": ["telegraph_electric"],
    "lnd_block_system": ["telegraph_electric"],
    "sea_submarine_cable": ["telegraph_electric"],
    "com_submarine_cable": ["telegraph_electric"],
    "if_submarine_cable_gutta_percha": ["telegraph_electric"],
    "fin_railway_company": ["railway"],
    "fud_cold_chain_refrigerated_shipping": ["railway"],
    "tl_level_crossing": ["railway"],
    "mil_railway_mobilisation": ["railway", "telegraph_electric"],
    "ben_harbour_and_lighthouse": ["civ_harbour_dock"],
    "ben_fire_and_flood_brigades": ["civ_aqueduct_roman"],
    "sea_buoy": ["sea_harbours_pozzolana"],
    "sea_drydock": ["civ_harbour_dock"],
    "tr_dry_dock": ["civ_harbour_dock"],
    "civ_water_treatment": ["civ_aqueduct_roman"],
    "civ_pumping_station": ["civ_aqueduct_roman"],
    "md2_sand_filtration": ["civ_aqueduct_roman"],
    "civ_water_tower": ["civ_pumping_station"],
    "cn_siphon": ["cn_aqueduct"],
    "ben_civic_water_works": ["civ_aqueduct_roman", "civ_sewer_roman"],
    "civ_sewer_separate": ["civ_sewer_roman"],
    "md2_sewage_separation": ["civ_sewer_roman"],
    "hom_sewer_stormwater_separation": ["civ_sewer_roman"],
    "civ_sewage_treatment": ["civ_sewer_separate"],
    "md2_activated_sludge": ["md2_sewage_separation"],
    "lnd_cursus_publicus": ["lnd_paved_road_network"],
}
EXPECTED_RAIL = ("fin_railway_company", "fud_cold_chain_refrigerated_shipping", "tl_level_crossing",
                 "mil_railway_mobilisation", "lnd_block_system", "el2_electric_locomotive_traction_motor")


def _nodes():
    nodes = {}
    for path in sorted(glob.glob(os.path.join(_ROOT, "data", "branches", "[0-9]*.json"))):
        with open(path, encoding="utf-8") as handle:
            for node in json.load(handle):
                nodes[node["id"]] = node
    return nodes


def _ancestors(nodes, start):
    seen, pending = set(), [start]
    while pending:
        node = nodes.get(pending.pop()) or {}
        for reference in node.get("pre") or []:
            if reference not in seen:
                seen.add(reference)
                pending.append(reference)
    return seen


class DependentsNeedRunningTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.nodes = _nodes()

    def test_each_dependent_names_the_works_it_needs_running(self):
        for node_id, works in sorted(EXPECTED_RUNNING.items()):
            self.assertEqual(self.nodes[node_id].get("requires_running"), works, node_id)

    def test_every_gate_is_valid_and_names_a_work_with_upkeep(self):
        self.assertEqual(validate_running_gates.check_running_gates(self.nodes), [])

    def test_no_node_gates_on_a_work_that_stands_on_it(self):
        for node_id, node in sorted(self.nodes.items()):
            for work in node.get("requires_running") or ():
                self.assertNotIn(node_id, _ancestors(self.nodes, work), "%s <-> %s" % (node_id, work))

    def test_a_gated_node_explains_itself_in_the_audit_note_not_the_player_note(self):
        for node_id, node in sorted(self.nodes.items()):
            if node.get("requires_running") or node.get("requires_ways"):
                self.assertIn("[GATE:", node.get("_internal") or "", node_id)
                self.assertNotIn("requires_", node.get("note") or "", node_id)

    def test_track_is_asked_of_the_railway_services_and_rolling_stock(self):
        for node_id in EXPECTED_RAIL:
            self.assertGreater((self.nodes[node_id].get("requires_ways") or {}).get("rail", 0), 0, node_id)

    def test_a_way_requirement_is_one_to_two_lines_between_held_tiles(self):
        world_map = queries._map(None)
        shortest = min(edge.km for edge in routes_graph.graph(world_map).edges if edge.edge_class == "land")
        modes = list(routes_modes.modes(world_map).values())
        for node_id, node in sorted(self.nodes.items()):
            for way, kilometres in (node.get("requires_ways") or {}).items():
                mode = next(entry for entry in modes if entry.get("needs_improvement") == way and entry.get("construction"))
                one_line = shortest * mode.get("km_factor", 1.0)
                self.assertLessEqual(kilometres, one_line * 2, node_id)
                self.assertGreaterEqual(kilometres, one_line * 0.9, node_id)

    def test_no_civilisation_opens_holding_a_dependent_without_its_works(self):
        for path in sorted(glob.glob(os.path.join(_ROOT, "data", "civilizations", "*.json"))):
            with open(path, encoding="utf-8") as handle:
                held = set(json.load(handle).get("starting_techs") or ())
            for node_id in sorted(held & set(EXPECTED_RUNNING)):
                self.assertLessEqual(set(EXPECTED_RUNNING[node_id]), held, "%s in %s" % (node_id, path))
                self.assertFalse(self.nodes[node_id].get("requires_ways"), "%s in %s" % (node_id, path))


if __name__ == "__main__":
    unittest.main()
