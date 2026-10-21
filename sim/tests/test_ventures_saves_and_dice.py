"""The identity_cover prerequisite (Complaint 640: read off the tree, no game). Writing down zero does not require a
respectable persona, but being received by a patron and publishing still do. The played-game checks are in
test_ventures_saves_and_dice_scenario."""
QUICK_TOPIC = True

import unittest

from .harness import NODES


class IdentityCoverPrerequisiteTests(unittest.TestCase):

    def test_writing_down_zero_does_not_require_a_respectable_persona(self):
        self.assertNotIn("identity_cover", NODES["arithmetic_positional"]["pre"])
        self.assertNotIn("identity_cover", NODES["scientific_method"]["pre"])

    def test_being_received_by_a_patron_and_publishing_still_do(self):
        self.assertIn("identity_cover", NODES["patron_local"]["pre"])
        self.assertIn("identity_cover", NODES["world_map"]["pre"])

    def test_the_balloon_can_be_built_without_a_persona(self):
        self.assertNotIn("identity_cover", NODES["hot_air_balloon"]["pre"])


if __name__ == "__main__":
    unittest.main()
