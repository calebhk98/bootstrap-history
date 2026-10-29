"""SMOKE: a Han game's replies and start refusals carry no Roman money word or place (Complaint 132): the leak is across every reply
builder, so they are read together on one unopened game. The words each builder takes from the civilisation record are the
unit-and-money tests of the module that builds the text. No years run."""
import json
import re
import unittest

from sim.tests.harness import NODES, S, unopened_sim


class HanRepliesNameNoRomanMoneyTest(unittest.TestCase):
    # presentation: the leak is a Roman word in any player-facing text, so the replies are read as text
    FORBIDDEN = re.compile(r"denari|\bRom(?:e|an)\b|iuger", re.IGNORECASE)

    def test_replies_and_start_refusals_use_the_civilisations_own_words(self):
        game = unopened_sim(civ="han_china_100ad", capital=50)
        texts = [json.dumps(S._agent_dispatch(game, NODES, {"cmd": name}))
                 for name in ("status", "money", "help", "land", "labour", "population", "economy")]
        texts += [json.dumps(S._agent_dispatch(game, NODES, {"cmd": "start", "id": node_id}))
                  for node_id in [node_id for node_id in NODES if node_id not in game.done][:30]]
        leaks = [self.FORBIDDEN.findall(text) for text in texts if self.FORBIDDEN.search(text)]
        self.assertEqual(leaks, [])

if __name__ == "__main__":
    unittest.main()
