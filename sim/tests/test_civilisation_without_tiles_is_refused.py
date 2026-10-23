"""The agent economy is the game's only economy and runs its markets on the tiles a civilisation holds, so a
civilisation that holds none is refused when the game is built, with a message naming where to declare its claim."""
QUICK_TOPIC = True

import unittest

from sim.engine.territory_required import require_territory


class RefusedWithoutTiles(unittest.TestCase):
    def test_the_rule_refuses_no_tiles_and_names_where_to_declare_them(self):
        with self.assertRaises(ValueError) as refused:
            require_territory({"id": "nowhere"}, [])
        self.assertIn("home_tiles", str(refused.exception))
        self.assertIn("nowhere", str(refused.exception))
        require_territory({"id": "somewhere"}, ["tile_1"])   # holding land is not refused


if __name__ == "__main__":
    unittest.main()
