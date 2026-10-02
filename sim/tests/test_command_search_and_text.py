"""Regression coverage for complaints 192, 193, 206, 213, 217 and 232: finding things
and reading replies. Searches never reach beyond what a player may see."""
from .harness import *  # noqa: F401,F403
from sim.ui.proto.typed import parse_typed
from sim.ui.proto import tree_filters as _tree_filters

_SIMULATOR = os.path.join(HERE, "simulator.py")


def _play(civ, lines):
    """Text of a typed game: the real command loop, fog on, default kit."""
    with tempfile.TemporaryDirectory() as scratch:
        done = subprocess.run(
            [sys.executable, _SIMULATOR, "play", "--civ", civ, "--kit", "poor_scholar", "--fog",
             "--seed", "1", "--session", os.path.join(scratch, "game.json")],
            input="\n".join(lines) + "\nquit\n", capture_output=True, text=True,
            timeout=300, cwd=ROOT)
    return done.stdout + done.stderr


def _typed(line):
    command, error = parse_typed(line)
    return command or {}, error


# ---- 217: one grammar for available arguments --------------------------------------
_command, _error = _typed("available metallurgy limit 80")
check("217: a subject followed by 'limit 80' keeps the subject and sets the limit",
      _command.get("subject") == "metallurgy" and _command.get("limit") == 80, _command)
_command, _error = _typed("available metallurgy limit:80")
check("217: 'limit:80' after a subject is the same",
      _command.get("subject") == "metallurgy" and _command.get("limit") == 80, _command)
_command, _error = _typed("available subject metallurgy offset 3")
check("217: 'subject X offset 3' keeps the subject and sets the offset",
      _command.get("subject") == "metallurgy" and _command.get("offset") == 3, _command)
_command, _error = _typed("available offset 30 subject metallurgy")
check("217: options before 'subject X' still work",
      _command.get("subject") == "metallurgy" and _command.get("offset") == 30, _command)
_command, _error = _typed("available power and precision limit 5 sort risk")
check("217: a several-word subject stops at the first option word",
      _command.get("subject") == "power and precision" and _command.get("limit") == 5
      and _command.get("sort") == "risk", _command)
_command, _error = _typed("available find iron smelting reverse")
check("217: 'find' takes every word up to the next option",
      _command.get("find") == "iron smelting" and _command.get("reverse") is True, _command)
_command, _error = _typed("available limit banana")
check("217: a limit that is not a number is refused, not swallowed",
      _error is not None and "limit" in _error, (_command, _error))

_replies = proto(
    [{"cmd": "available", "all": True, "limit": 3},
     {"cmd": "available", "tag": "optics"},
     {"cmd": "available", "subject": "metallurgy", "offset": 9999},
     {"cmd": "available", "find": "electricity"},
     {"cmd": "available", "subject": "physics"},
     {"cmd": "available", "find": "physics"},
     {"cmd": "available", "subject": "education"},
     {"cmd": "available", "find": "education"}],
    civ="england_1300", kit="poor_scholar", fog=True)[0][-8:]
check("217: 'all' with 'limit' shows only the limit",
      len(_replies[0].get("available", [])) == 3, len(_replies[0].get("available", [])))
check("217: a tag refusal says subjects are a different list and names both lists",
      not _replies[1].get("ok") and "subject" in _replies[1].get("error", "")
      and "education" in _replies[1].get("error", ""), _replies[1])
check("217: an offset past the end says so and gives the total",
      "past the end" in str(_replies[2].get("nothing_matched", "")), _replies[2])

# ---- 197: the knowledge-file name is not a subject a search matches -----------------
_synthetic = {"a": {"name": "Signal flags", "cat": "comms", "kb": "50_electricity.md#flags",
                    "pre": []}}
check("197: find does not match a node by its knowledge-file name",
      not _tree_filters.matches_find(_synthetic, "electricity", "a"))
check("197: find still matches by name",
      _tree_filters.matches_find(_synthetic, "signal", "a"))
check("197: 'available find electricity' does not list a node by its filing cabinet",
      "com_signal_flags" not in [row["id"] for row in _replies[3].get("available", [])],
      _replies[3].get("available"))
_electricity_replies = proto([{"cmd": "available", "subject": "electricity"}], civ="england_1300", kit="poor_scholar", fog=True)[0][-1]
check("197: 'available electricity' does not list Signal flags",
      "com_signal_flags" not in [row["id"] for row in _electricity_replies.get("available", [])],
      [row["id"] for row in _electricity_replies.get("available", [])])

# ---- 196: a topic word that is not a subject heading is searched as a word ---------
check("196: a bare topic word returns what find returns",
      [row["id"] for row in _replies[6].get("available", [])]
      == [row["id"] for row in _replies[7].get("available", [])]
      and _replies[6].get("count", 0) > 0, (_replies[6].get("showing"), _replies[7].get("count")))
_text = _play("england_1300", ["available science"])
check("196: an empty search teaches 'find' and the topic tags",
      "available find" in _text and "tag" in _text.lower().split("nothing you could begin")[-1],
      _text[-1500:])
_physics_replies = proto([{"cmd": "available", "subject": "physics"}], civ="england_1300", kit="poor_scholar", fog=True)[0][-1]
check("196: 'available physics' returns at least one result",
      _physics_replies.get("ok") is not False and len(_physics_replies.get("available", [])) > 0,
      _physics_replies.get("available", []))
_furnace_replies = proto([{"cmd": "available", "subject": "furnace"}], civ="england_1300", kit="poor_scholar", fog=True)[0][-1]
check("196: 'available furnace' returns at least one result",
      _furnace_replies.get("ok") is not False and len(_furnace_replies.get("available", [])) > 0,
      _furnace_replies.get("available", []))

# ---- 221: close and quote name the right command ------------------------------------
_text = _play("han_china_100ad", ["start hom_button", "step", "open hom_button",
                                   "close hom_button", "quote hom_button"])
_after_close = _text.split("close hom_button")[-1]
check("221: 'close <concern id>' points at mothball",
      "mothball hom_button" in _text and "no such material: hom_button" not in _text, _text[-1500:])
check("221: 'quote <project id>' names the quote commands that exist",
      "quote open" in _text.split("REFUSED")[-1] or "quote open" in _text, _text[-1500:])

# ---- 210: the first help screen is for a person -------------------------------------
_text = _play("england_1300", ["help"])
_first_help = _text.split("> ", 1)[-1]
check("210: the first help screen does not talk about pasting JSON",
      "JSON" not in _first_help.split("[1300")[0], _first_help[:1500])
_text = _play("england_1300", ["help sittings"])
check("210: help sittings still carries the JSON and script notes",
      "JSON" in _text, _text[-800:])

# ---- 236: small text defects --------------------------------------------------------
_goals = subprocess.run([sys.executable, _SIMULATOR, "goals"], capture_output=True, text=True,
                        cwd=ROOT).stdout
check("236.1: the epidemic goal does not call 85 per cent four-fifths",
      "four-fifths" not in _goals, _goals[:600])
from sim.engine.tree_source import load_base_tree as _load_base_tree
_tree_text = json.dumps(_load_base_tree())
check("236.2: the algebra note's sentence matches its equation",
      "add 5 and triple it" not in _tree_text and "triple it and add 5" in _tree_text)
_text = _play("han_china_100ad", ["available", "labour laborer", "help commands"])
check("236.3: the digest title counts the rows it prints",
      "CHEAPEST SIX RIGHT NOW" not in _text, _text[-600:])
_labour = proto([{"cmd": "labour", "trade": "laborer"}], civ="han_china_100ad", kit="poor_scholar")[0][-1]
check("236.6: 'labour laborer' is accepted as 'labour labourer'",
      _labour.get("ok") is not False, _labour)
check("236.7: help commands lists options",
      "options: the saved settings" in _text, _text[-1500:])
from sim.engine.data import STARTING_KITS as _KITS
check("236.4: the poor_scholar kit does not claim a few months",
      "months" not in _KITS["poor_scholar"]["desc"], _KITS["poor_scholar"]["desc"])
check("236.5: the absurd kit description has no patch history",
      "used to" not in _KITS["absurd"]["desc"], _KITS["absurd"]["desc"])
check("236.9: player text does not name internal functions",
      "funding_capacity" not in open(os.path.join(HERE, "engine", "proto", "dispatch_ventures.py")).read().split("what_this_means")[1].split("%")[0])
_ventures = proto([{"cmd": "ventures", "closed": True}], civ="han_china_100ad", kit="poor_scholar")[0][-1]
check("236.11: 'ventures closed' says what it shows instead of silently ignoring the word",
      "closed" in json.dumps(_ventures).lower(), list(_ventures))
