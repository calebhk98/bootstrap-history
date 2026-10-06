"""Regression coverage for complaints 192, 193, 206, 213, 217 and 232: finding things
and reading replies. Searches never reach beyond what a player may see."""
from .harness import *  # noqa: F401,F403
from sim.ui.proto.typed import parse_typed
from sim.ui.proto import tree_filters as _tree_filters


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

def _fogged_england():
    """England as the typed game starts it: fog on, the poor scholar's kit."""
    game = S.Sim(NODES, ORDER, random.Random(1), events=False, manual=True,
                 civ=S.load_civ("england_1300"), cfg={"start_kit": "poor_scholar"})
    game.goal, game.done_year = GOAL, {}
    game.fog, game.revealed = True, set()
    return game


_england = _fogged_england()


def _ask(game, **command):
    return S._agent_dispatch(game, NODES, command)


_replies = [_ask(_england, cmd="available", all=True, limit=3),
            _ask(_england, cmd="available", tag="optics"),
            _ask(_england, cmd="available", subject="metallurgy", offset=9999),
            _ask(_england, cmd="available", subject="physics"),
            _ask(_england, cmd="available", find="physics"),
            _ask(_england, cmd="available", find="electricity"),
            _ask(_england, cmd="available", subject="electricity"),
            _ask(_england, cmd="available", subject="furnace")]
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

_electricity_find, _electricity_subject = _replies[5], _replies[6]
_signal_find = _ask(_england, cmd="available", find="signal")
check("197: Signal flags is in view under fog, so its absence from an electricity search means something",
      "com_signal_flags" in [row["id"] for row in _signal_find.get("available", [])],
      [row["id"] for row in _signal_find.get("available", [])])
check("197: 'available find electricity' does not list a node by its filing cabinet",
      "com_signal_flags" not in [row["id"] for row in _electricity_find.get("available", [])],
      _electricity_find.get("available"))
check("197: 'available electricity' does not list Signal flags",
      "com_signal_flags" not in [row["id"] for row in _electricity_subject.get("available", [])],
      [row["id"] for row in _electricity_subject.get("available", [])])

# ---- 196: a topic word that is not a subject heading is searched as a word ---------
check("196: a bare topic word returns what find returns",
      [row["id"] for row in _replies[3].get("available", [])]
      == [row["id"] for row in _replies[4].get("available", [])]
      and _replies[3].get("count", 0) > 0, (_replies[3].get("showing"), _replies[4].get("count")))

for _word, _reply in (("physics", _replies[3]), ("furnace", _replies[7])):
    check("196: 'available %s' returns at least one result" % _word,
          _reply.get("ok") is not False and len(_reply.get("available", [])) > 0, _reply.get("available", []))

# ---- 221: close and quote name the right command ------------------------------------
_han = sim("han_china_100ad")
_han.end_year = _han.cfg["start_year"] + 50
_ask(_han, cmd="start", id="hom_button")
_ask(_han, cmd="step", years=1)
_ask(_han, cmd="open", id="hom_button")
_closed = _ask(_han, cmd="close", what="hom_button", material="hom_button")
_quoted = _ask(_han, cmd="quote", what="mine", material="hom_button")
check("221: 'close <concern id>' points at mothball",
      not _closed["ok"] and "mothball hom_button" in _closed["error"], _closed)
check("221: 'quote <project id>' names the quote commands that exist",
      not _quoted["ok"] and "quote open" in _quoted["error"], _quoted)

# ---- 236: small behaviour defects ----------------------------------------------------
_labour = _ask(_han, cmd="labour", trade="laborer")
check("236.6: 'labour laborer' is accepted as 'labour labourer'",
      _labour.get("ok") is not False, _labour)
_ventures = _ask(_han, cmd="ventures", closed=True)
check("236.11: 'ventures closed' says what it shows instead of silently ignoring the word",
      "closed" in json.dumps(_ventures).lower(), list(_ventures))
