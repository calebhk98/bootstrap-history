"""Workers placed from outside the clearing (`economy.api.add_workers`) move the market memory's write stamp, so the
figures kept between steps and the views' cached reads, which read the workforce, are read again."""
QUICK_TOPIC = True

import types
import unittest

from sim.economy import api, market_memory


class AddWorkersStampTests(unittest.TestCase):
    def test_placing_workers_moves_the_stamp(self):
        placed = []
        labour = types.SimpleNamespace(add_workers=lambda area, trade, people: placed.append((area, trade, people)))
        economy = types.SimpleNamespace(record=types.SimpleNamespace(labour=labour))
        before = market_memory.written_stamp()
        api.add_workers(economy, "italy_01", "smith", 2.0)
        self.assertEqual(len(placed), 1)
        self.assertGreater(market_memory.written_stamp(), before)


if __name__ == "__main__":
    unittest.main()
