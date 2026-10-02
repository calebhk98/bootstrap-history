"""Test that 'school' has been renamed to 'trade_school'."""
from .harness import *
from sim.ui.proto.typed import parse_typed


check("buy trade_school parses correctly",
      parse_typed("buy trade_school smith 2")[0]
      == {"cmd": "buy", "what": "trade_school", "material": "smith", "n": 2})

check("help text mentions trade school",
      "trade school" in str(parse_typed("help economy")).lower()
      or parse_typed("help buy") is not None)

test_sim = sim(capital=1_000_000)
test_sim.trades_created.add("chemist")
test_sim.labour_market.press("chemist", 100)

reply = S._agent_dispatch(test_sim, NODES,
                          {"cmd": "buy", "what": "trade_school",
                           "trade": "chemist", "n": 1})
check("buy trade_school command works",
      reply["ok"], reply)

reply_old = S._agent_dispatch(test_sim, NODES,
                              {"cmd": "buy", "what": "school",
                               "trade": "chemist", "n": 1})
check("'school' is the documented spelling and works",
      reply_old["ok"], reply_old)
