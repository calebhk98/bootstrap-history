"""Complaints 70, 77, 78, 97, 100: a report says a thing once, as one event, with direction. The standing shortage, the
disaster grouping, the fog kind hint and the first-screen help, each called on a stand-in game or a built reply (no
game). The shortage on the state screen is test_state_conditions_block."""
import contextlib
import io
from types import SimpleNamespace

from .harness import check

from sim.materials import rules as shortage_conditions
from sim.tests import materials_stand_in
from sim.knowledge.api import FOG_KIND_HINTS, hidden_prerequisite_kinds, missing_prereq_message
from sim.ui.cli_interactive import _play_print_welcome
from sim.ui.proto.event_groups import group_disaster_events
from sim.ui.proto.help import _agent_help

QUICK_TOPIC = True


def _game(year=100, shortfall=0.0):
    """The materials module over a clock the test moves, with the shortfall of any material fixed."""
    clock = SimpleNamespace(year=year)
    module = materials_stand_in.build(year=lambda: clock.year)
    module.material_shortfall = lambda material: shortfall
    module.clock_year = clock
    return module


def _year_on(game, years=1):
    game.clock_year.year += years


def _news(game, material, throughput):
    return game.note_shortage(material, throughput)


# --- 79: a shortage that persists is one standing condition, not a message a year
shortage = _game()
check("a first shortage is worth an event", _news(shortage, "charcoal", 0.46))
_year_on(shortage)
check("the same shortage a year later is not a new event", not _news(shortage, "charcoal", 0.45))
_year_on(shortage)
check("a material change in throughput is a new event", _news(shortage, "charcoal", 0.20))
check("a different material is a new event", _news(shortage, "coal", 0.20))
_year_on(shortage, 3)
rows = shortage.shortage_conditions()
check("the standing condition names material, throughput and how long it has lasted",
      len(rows) == 1 and rows[0]["material"] == "coal" and rows[0]["years"] == 4 and rows[0]["throughput"] == 0.20, rows)
shortage.step_shortage_notes()      # the reading is back to full pace: nothing is slowed, the condition ends
check("a resolved shortage leaves no condition", not shortage.shortage_conditions())
check("and the next shortage is news again", _news(shortage, "coal", 0.5))

steady = _game()
_news(steady, "coal", 0.5)
_year_on(steady)
_news(steady, "coal", 0.5 + shortage_conditions.STEADY_BAND / 2)
check("a move inside the steady band reads as steady", steady.shortage_conditions()[0]["trend"] == "steady")
_news(steady, "coal", 0.5 + shortage_conditions.STEADY_BAND / 2 + 0.05)
check("a rise beyond the band reads as improving", steady.shortage_conditions()[0]["trend"] == "improving")
_news(steady, "coal", 0.3)
check("a fall beyond the band reads as worsening", steady.shortage_conditions()[0]["trend"] == "worsening")
edge = _game()
_news(edge, "coal", 0.5)
check("a throughput move just under the material change is not news, and one at it is",
      not _news(edge, "coal", 0.5 - shortage_conditions.MATERIAL_THROUGHPUT_CHANGE + 0.01)
      and _news(edge, "coal", 0.5 - shortage_conditions.MATERIAL_THROUGHPUT_CHANGE - 0.01))
deficit_game = _game(shortfall=12.34)
_news(deficit_game, "coal", 0.5)
check("a deficit in tonnes a year rides on the row when the material is short",
      deficit_game.shortage_conditions()[0]["deficit_tonnes_per_year"] == 12.3)
# presentation: the standing-condition line names the material, throughput, deficit and trend
line = shortage_conditions.condition_line({"material": "alum_kg", "throughput": 0.46, "deficit_tonnes_per_year": 12.3,
                                           "years": 3, "trend": "worsening"})
check("the standing-condition line names the material in words, the throughput, the deficit, the years and the trend",
      "ALUM CONSTRAINED" in line and "46%" in line and "12.3" in line and "year 3" in line and "worsening" in line, line)

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
NODES_OF_KIND = {
    "target": {"name": "Target", "pre": ["near_hidden", "far_hidden"], "cat": "x"},
    "near_hidden": {"name": "Near", "pre": ["done_one", "open_one"], "cat": "x", "kind": "INSTITUTION"},
    "far_hidden": {"name": "Far", "pre": ["unknown_a", "unknown_b"], "cat": "x", "kind": "SCIENCE"},
    "leaf_resource": {"name": "Leaf", "pre": [], "cat": "x", "kind": "RESOURCE"},
    "done_one": {"name": "Done", "pre": [], "cat": "x"}, "open_one": {"name": "Open", "pre": [], "cat": "x"},
    "unknown_a": {"name": "A", "pre": [], "cat": "x"}, "unknown_b": {"name": "B", "pre": [], "cat": "x"},
}


def _visible_but_for_the_two_hidden(node_id):
    return node_id not in ("near_hidden", "far_hidden")


def _hidden_kinds(hidden_ids, done):
    return hidden_prerequisite_kinds(NODES_OF_KIND, hidden_ids, done)


def _message(missing, done):
    return missing_prereq_message(NODES_OF_KIND, missing, _visible_but_for_the_two_hidden, True, done)


done_one = {"done_one"}
check("a hidden prerequisite near known work (half its own prerequisites built) names its kind",
      _hidden_kinds(["near_hidden"], done_one) == [FOG_KIND_HINTS["INSTITUTION"]])
check("one far from anything known gets no kind hint", _hidden_kinds(["far_hidden"], done_one) == [])
message = _message(["near_hidden"], done_one)
check("a hidden prerequisite still hides its identity", "near_hidden" not in message and "Near" not in message, message)
# presentation: the fog sentence names the kind of thing
check("...and the message names its kind", "institution" in message.lower(), message)
check("the message for the far one carries no kind",
      "institution" not in _message(["far_hidden"], done_one).lower()
      and "idea or body" not in _message(["far_hidden"], done_one).lower())
check("a hidden prerequisite with no prerequisites of its own counts as near",
      _hidden_kinds(["leaf_resource"], done_one) == [FOG_KIND_HINTS["RESOURCE"]])

# --- 99 and 102: the first-screen help points at the beginner index and at sittings
help_reply = _agent_help(SimpleNamespace(fog=False), "commands")
first_key = next(iter(help_reply))
# presentation: the first heading of the commands page
check("help commands opens with a short beginner index",
      "start" in first_key.lower() or "begin" in first_key.lower(), list(help_reply)[:3])

welcome = io.StringIO()
with contextlib.redirect_stdout(welcome):
    _play_print_welcome(SimpleNamespace(year=100, capital=1000.0, civ={"id": "stub"}, fog=False), "poor_scholar")
# presentation: the welcome screen names the help topics
check("the welcome screen points at the sittings topic and the beginner index",
      "help sittings" in welcome.getvalue() and "help commands" in welcome.getvalue(), welcome.getvalue()[-400:])
