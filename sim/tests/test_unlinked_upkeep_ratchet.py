"""Complaint 510: a node that charges upkeep and gates or operates no production entry is an error, unless it is on
the list of nodes still to be linked (data/unlinked_upkeep_nodes.txt), which can only shrink. The rule is called on
built nodes and a built catalogue; the shipped list is checked against the shipped tree."""

QUICK_TOPIC = True

import unittest

from sim.engine import data, validate_unlinked_producers
from sim.labour.labour_market import production_data

PRODUCTION = {"smelt": {"outputs": {"lead_kg": 1.0}, "operated_by": ["runs"]}}
NODES = {
    "runs": {"id": "runs", "up_hours": 5.0},
    "idle": {"id": "idle", "up_hours": 5.0},
    "known": {"id": "known", "up_hours": 5.0},
    "free": {"id": "free", "up_hours": 0.0},
}


class UnlinkedUpkeepRatchet(unittest.TestCase):

    def test_a_node_with_upkeep_and_no_plant_not_on_the_list_is_an_error(self):
        errors, _stale = validate_unlinked_producers.check_unlinked_upkeep(NODES, PRODUCTION, {"known"})
        self.assertEqual(len(errors), 1)
        self.assertIn("idle", errors[0])

    def test_a_node_that_operates_an_entry_or_charges_nothing_is_fine(self):
        errors, _stale = validate_unlinked_producers.check_unlinked_upkeep(NODES, PRODUCTION, {"idle", "known"})
        self.assertEqual(errors, [])

    def test_a_listed_node_that_no_longer_offends_is_reported_stale(self):
        _errors, stale = validate_unlinked_producers.check_unlinked_upkeep(
            NODES, PRODUCTION, {"idle", "known", "runs", "free"})
        self.assertEqual(sorted(stale), ["free", "runs"])

    def test_the_shipped_list_is_sorted_and_matches_the_shipped_tree(self):
        _tree, _document, nodes, _wages, _goods = data.load()
        listed = validate_unlinked_producers.load_allowed()
        self.assertEqual(sorted(listed), list(listed))
        errors, stale = validate_unlinked_producers.check_unlinked_upkeep(nodes, production_data(), listed)
        self.assertEqual((errors, stale), ([], []))


if __name__ == "__main__":
    unittest.main()
