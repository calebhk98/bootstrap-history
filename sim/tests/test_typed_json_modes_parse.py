"""Every player of this game is an AI agent parsing text, so the machine-readable modes must be understood by the typed
parser: `state json`, `portfolio json` and `risk json` (and `hazards json`), in any position, beside their existing
modifiers. The parser is called on built lines."""
QUICK_TOPIC = True

import unittest

from sim.ui.protocol import parse_typed


class JsonModeParsingTests(unittest.TestCase):
    def parsed(self, text):
        return parse_typed(text)[0]

    def test_state_json(self):
        self.assertEqual(self.parsed("state json"), {"cmd": "state", "full": False, "json": True})

    def test_state_full_json(self):
        self.assertEqual(self.parsed("state full json"), {"cmd": "state", "full": True, "json": True})

    def test_portfolio_json_and_plain(self):
        self.assertEqual(self.parsed("portfolio json"), {"cmd": "portfolio", "json": True})
        self.assertEqual(self.parsed("portfolio"), {"cmd": "portfolio", "json": False})

    def test_risk_json_and_its_alias_hazards(self):
        self.assertEqual(self.parsed("risk json"), {"cmd": "risk", "json": True})
        self.assertEqual(self.parsed("hazards json"), {"cmd": "risk", "json": True})


if __name__ == "__main__":
    unittest.main()
