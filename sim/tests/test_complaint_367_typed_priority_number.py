"""Complaint 367: typed `priority 5` (no id) must refuse with usage, not crash."""
from .harness import *  # noqa: F401,F403
from sim.engine.proto.typed import parse_typed

for line in ("priority 5", "priority", "priority 2 first"):
    try:
        parse_typed(line)
        crashed = None
    except IndexError as error:
        crashed = error
    check("%r does not crash the parser" % line, crashed is None, crashed)

cmd, refusal = parse_typed("priority 5")
check("a bare rank is refused with a usage message",
      cmd is None and refusal and "priority" in refusal, (cmd, refusal))
cmd, refusal = parse_typed("priority bread_baking first")
check("documented form 'priority <id> first' parses",
      cmd == {"cmd": "priority", "id": "bread_baking", "position": "first"}, (cmd, refusal))
cmd, refusal = parse_typed("priority bread_baking 2")
check("documented form 'priority <id> <rank>' parses",
      cmd is not None and cmd.get("position") == 2, (cmd, refusal))
cmd, refusal = parse_typed("priority")
check("bare priority lists", cmd == {"cmd": "priority"}, (cmd, refusal))
