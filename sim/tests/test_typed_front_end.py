"""How a typed line is read: documented forms parse, ids keep their real case, malformed lines are refused (Complaint 640 split)."""
from .harness import *  # noqa: F401,F403
from sim.ui.proto.typed import parse_typed

QUICK_TOPIC = True

# The documented three-word buy lost its material to the parser, which made mining unreachable.
for line in ("quote mine coal 500", "quote coal 500"):
    command = parse_typed(line)[0] or {}
    check("the mining form %r parses to material and amount" % line,
          command.get("material") == "coal" and command.get("n") == 500, command)

command, error = parse_typed("step 1; step 1")
check("two commands on one line are refused, not half-executed", command is None and error is not None, (command, error))
# presentation: the refusal tells the player the one-command-per-line rule
check("...and the refusal says why", "one command per line" in (error or ""), error)

# The help shows {"cmd":"labour","trade":"smith"}, so the typed reading of it has to work.
command, error = parse_typed("labour trade smith")
check("the typed form of what the help shows works", error is None and (command or {}).get("trade") == "smith", (command, error))

command, error = parse_typed("step abc")
check("a step that is not a number is refused, not taken as one", command is None and error is not None, (command, error))
# presentation: the refusal names the problem
check("...and the refusal says it is not a number", "not a number" in (error or ""), error)

# Eleven ids carry capitals; lowercasing what was typed made them unreachable.
capitalised = sorted(node_id for node_id in NODES if node_id != node_id.lower())
check("the tree has ids that carry capitals", bool(capitalised), None)
mismatched = []
for node_id in capitalised:
    for typed in (node_id, node_id.upper(), node_id.lower()):
        parsed = (parse_typed("why " + typed)[0] or {}).get("id")
        if parsed != node_id:
            mismatched.append((typed, parsed))
check("every id that carries capitals is reached whatever case the player types", not mismatched, mismatched[:5])

check("a typed id in the wrong case parses to a lowercase id the tree knows",
      (parse_typed("why AG2_MARLING")[0] or {}).get("id") in NODES, parse_typed("why AG2_MARLING"))

started = time.time()
for node_id in list(NODES)[:400]:
    S.downstream_count(NODES, node_id)
# a speed bound on the shared tree walk, not on any rule
check("what rests on a node is cheap enough to put in a table", time.time() - started < 1.0,
      "%.2fs for 400" % (time.time() - started))
