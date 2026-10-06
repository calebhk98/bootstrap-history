"""Complaints 70, 77, 78, 97, 100: a report says a thing once, as one event, with direction."""
from .harness import *  # noqa: F401,F403
from sim.engine import shortage_conditions
from sim.ui.protocol import _agent_dispatch
from sim.ui.proto.event_groups import group_disaster_events
from sim.ui.proto.render_screen_state import render_state

# --- 79: a shortage that persists is one standing condition, not a message a year
shortage_sim = sim()
check("a first shortage is worth an event",
      shortage_conditions.note_shortage(shortage_sim, "charcoal", 0.46))
shortage_sim.state.scenario.year += 1
check("the same shortage a year later is not a new event",
      not shortage_conditions.note_shortage(shortage_sim, "charcoal", 0.45))
shortage_sim.state.scenario.year += 1
check("a material change in throughput is a new event",
      shortage_conditions.note_shortage(shortage_sim, "charcoal", 0.20))
check("a different material is a new event",
      shortage_conditions.note_shortage(shortage_sim, "coal", 0.20))
shortage_sim.state.scenario.year += 3
rows = shortage_conditions.condition_rows(shortage_sim)
check("the standing condition names material, throughput and how long it has lasted",
      len(rows) == 1 and rows[0]["material"] == "coal" and rows[0]["years"] >= 1
      and 0.0 <= rows[0]["throughput"] <= 1.0 and rows[0]["trend"] in ("improving", "worsening", "steady"), rows)
shortage_conditions.clear_shortage(shortage_sim)
check("a resolved shortage leaves no condition", not shortage_conditions.condition_rows(shortage_sim))
check("and the next shortage is news again",
      shortage_conditions.note_shortage(shortage_sim, "coal", 0.5))

standing = shortage_sim
shortage_conditions.note_shortage(standing, "charcoal", 0.46)
state_reply = _agent_dispatch(standing, NODES, {"cmd": "state"})
check("state carries the standing conditions", bool(state_reply.get("conditions")), list(state_reply)[:10])
check("the state screen prints them as a block",
      "CHARCOAL" in render_state(state_reply).upper() and "46%" in render_state(state_reply))

# --- 80: one disaster, one event with its consequences inside
disaster_events = [
    {"year": 410, "message": "you lose 2 smiths to the sack of a site"},
    {"year": 410, "message": "Sack of Rome: a site is sacked - 500 taken, 3 projects back to the beginning"},
    {"year": 410, "message": "KNOWLEDGE LOST: 4 technologies forgotten - a, b, c, d"},
    {"year": 410, "message": "completed: Loom"},
]
grouped = group_disaster_events(disaster_events, "Sack of Rome", [event["message"] for event in disaster_events[:3]])
check("the consequences of one disaster collapse into one event",
      len(grouped) == 2 and grouped[0]["message"].startswith("Sack of Rome")
      and len(grouped[0]["details"]) == 3 and grouped[1]["message"] == "completed: Loom", grouped)
check("a lone consequence is left as it was",
      group_disaster_events(disaster_events, "Sack of Rome", [disaster_events[3]["message"]]) == disaster_events)
check("grouping nothing changes nothing", group_disaster_events(disaster_events, None, []) == disaster_events)

# --- 72: under fog, a hidden prerequisite gives its coarse kind once the player is close
fogged = shortage_sim
fogged.fog = True
hidden_node = next(node_id for node_id, node in NODES.items()
                   if not fogged.is_visible(node_id) and node.get("kind") == "INSTITUTION"
                   and len(node["pre"]) >= 2 and all(prereq in fogged.done for prereq in node["pre"][:-1]))
for prereq in NODES[hidden_node]["pre"][:-1]:
    fogged.done.add(prereq)
message = fogged.missing_prereq_message([hidden_node])
check("a hidden prerequisite still hides its identity", hidden_node not in message and NODES[hidden_node]["name"] not in message, message)
check("a hidden prerequisite near known work names its kind", "institution" in message.lower(), message)
far_node = next(node_id for node_id, node in NODES.items()
                if not fogged.is_visible(node_id) and len(node["pre"]) >= 2 and not any(p in fogged.done for p in node["pre"]))
check("one far from anything known gets no kind hint",
      "institution" not in (fogged.missing_prereq_message([far_node]) or "").lower()
      and "technique" not in (fogged.missing_prereq_message([far_node]) or "").lower())

# --- 99 and 102: the first-screen help points at the beginner index and at sittings
help_reply = _agent_dispatch(shortage_sim, NODES, {"cmd": "help", "topic": "commands"})
first_key = next(iter(help_reply["help"]))
check("help commands opens with a short beginner index", "start" in first_key.lower() or "begin" in first_key.lower(), list(help_reply["help"])[:3])

from sim.ui.cli_interactive import _play_print_welcome
import io, contextlib
welcome = io.StringIO()
with contextlib.redirect_stdout(welcome):
    _play_print_welcome(shortage_sim, "poor_scholar")
check("the welcome screen points at the sittings topic and the beginner index",
      "help sittings" in welcome.getvalue() and "help commands" in welcome.getvalue(), welcome.getvalue()[-400:])
