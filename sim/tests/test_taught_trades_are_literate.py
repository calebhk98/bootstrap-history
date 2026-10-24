"""Every trade that has to be taught into being is a lettered trade, so literate_capacity bounds it (electrician included)."""
QUICK_TOPIC = True

import json
import os

from .harness import *  # noqa: F401,F403

from sim.labour import trade_data

DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "world")
trades_file = json.load(open(os.path.join(DATA, "trades.json")))["trades"]

taught_in = {trade for trade, record in trades_file.items() if record.get("initially_absent")}
check("the shipped data names trades that start absent", bool(taught_in), taught_in)
lettered = trade_data.literate_trades(trades_file, sorted(trades_file))
check("every trade that starts absent is literate", taught_in <= lettered, sorted(taught_in - lettered))
