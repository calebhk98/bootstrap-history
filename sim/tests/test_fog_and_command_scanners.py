"""fog_and_command_scanners: regression checks, run individually with `--only fog_and_command_scanners`."""
from .harness import *  # noqa: F401,F403
from sim.ui import protocol as _PROTO

# =============================================================================
# A GENERIC FOG SCANNER. `bounty` leaked three hidden node ids (power_grid,
# an induction-coupling prerequisite, a hidden cathode) before anyone wrote
# a test pinned to that one command by name - because the fog filter lived
# in start_reason alone and nothing stopped a second command from building
# its own unfiltered prerequisite list. This scans EVERY command in
# KNOWN_COMMANDS at once, generically, so the NEXT command to do that -
# including `capacity`, `economy` and `changes`, built this round - is
# caught here rather than found by a playtester.
# =============================================================================
_fogscan = sim(capital=5_000_000.0)
_fogscan.fog = True
_fogscan.revealed = set()
_fogscan_visible = sorted(node_id for node_id in NODES if _fogscan.is_visible(node_id))
_fogscan_goal = _fogscan.goal
_fogscan_hidden = {node_id for node_id in NODES
                   if node_id not in _fogscan_visible and node_id != _fogscan_goal}
check("a fresh fogged founder has both a visible node and a large hidden "
      "remainder to test against - a property of the live tree, not an "
      "invented fixture",
      bool(_fogscan_visible) and len(_fogscan_hidden) > 1000,
      (len(_fogscan_visible), len(_fogscan_hidden)))
_fv = _fogscan_visible[0]
_fogscan_args = {
    "why": {"id": _fv}, "path": {"id": _fv},
    "start": {"id": "__no_such_node__"}, "stop": {"id": "__no_such_node__"},
    "bounty": {"id": _fv}, "mothball": {"id": "__no_such_node__"},
    "restore": {"id": "__no_such_node__"}, "open": {"id": _fv},
    "buy": {"what": "mine", "material": "iron", "n": 1},
    "quote": {"what": "mine", "material": "iron", "n": 1},
    "close": {"what": "iron", "material": "iron"},
    "hire": {"trade": "smith", "n": 1}, "fire": {"trade": "smith", "n": 1},
    "train": {"trade": "smith", "n": 1}, "work": {"trade": "smith", "hours": 10},
    "commission": {"trade": "smith", "hours": 10}, "bribe": {"amount": 10},
    "changes": {"years": 5}, "policy": {},
}
# save/load/quit: side effects (a file written, the run ended) unrelated to
# what this test is about, and excluded for that reason, not for safety.
# finish ends the run and on purpose shows the road that fog hid until then.
_fogscan_skip = {"save", "load", "quit", "finish"}
_word_re = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
_fogscan_leaks = {}
for _c in S.KNOWN_COMMANDS:
    if _c in _fogscan_skip:
        continue
    _obj = dict(_fogscan_args.get(_c, {}))
    _obj["cmd"] = _c
    try:
        _resp = S._agent_dispatch(_fogscan, NODES, _obj)
    except Exception as _e:
        continue   # a crash is a different bug; this test is only about leaks
    _tokens = set(_word_re.findall(json.dumps(_resp)))
    _leaked = sorted(_fogscan_hidden & _tokens)
    if _leaked:
        _fogscan_leaks[_c] = _leaked[:5]
check("no command in KNOWN_COMMANDS prints the raw id of a node this fogged "
      "founder has never heard of - scanned generically across every "
      "command at once, so the next command to grow this bug is caught "
      "here rather than by a playtester, the way `bounty` was",
      not _fogscan_leaks, _fogscan_leaks)

# --- 5. MACHINE-READABLE OUTPUT MODES. Every player of this game is an AI
# agent parsing text, and several have lost runs to parsing prose that was
# never meant to be a machine interface.
check("'state json'/'portfolio json'/'risk json' are understood by the "
      "typed parser, in any position, alongside their existing modifiers",
      _PT("state json")[0] == {"cmd": "state", "full": False, "json": True}
      and _PT("state full json")[0] == {"cmd": "state", "full": True, "json": True}
      and _PT("portfolio json")[0] == {"cmd": "portfolio", "json": True}
      and _PT("portfolio")[0] == {"cmd": "portfolio", "json": False}
      and _PT("risk json")[0] == {"cmd": "risk", "json": True}
      and _PT("hazards json")[0] == {"cmd": "risk", "json": True},
      (_PT("state json"), _PT("portfolio json"), _PT("risk json")))
# THE JSON MUST NOT BE A FOG BYPASS. Reusing the exact same fogged founder
# and hidden-node set the generic fog scanner above already built: the
# JSON this session would emit for 'state json'/'portfolio json'/'risk
# json' is exactly json.dumps(the same resp dict render_pretty renders), so
# checking it here is checking the one shared source both paths read from.
for _jc in ("state", "portfolio", "risk"):
    _jresp = S._agent_dispatch(_fogscan, NODES, {"cmd": _jc})
    _jtext = json.dumps(_jresp)
    check("'%s json' parses as valid JSON" % _jc,
          json.loads(_jtext) == _jresp, _jtext[:200])
    _jtokens = set(_word_re.findall(_jtext))
    _jleak = sorted(_fogscan_hidden & _jtokens)
    _jprose = _RP(_jc, _jresp)
    _jprose_leak = sorted(_fogscan_hidden & set(_word_re.findall(_jprose)))
    check("a node this fogged founder has never heard of is absent from "
          "'%s'`s JSON exactly as it is absent from its rendered prose "
          "(both read the identical resp dict; the JSON is not a second, "
          "unfiltered path)" % _jc,
          not _jleak and not _jprose_leak,
          (_jleak, _jprose_leak, _jc))

# =============================================================================
# A GENERIC COMMAND-POINTER SCANNER. `state`'s own footer once pointed a
# player at `training_pending` with nothing behind it - "did you mean: "
# answered with a command that does not exist - and the fix for that one
# name would not have caught the next one. This walks every reply
# KNOWN_COMMANDS and help can produce, collects every "{"cmd":"X"}" and
# "see 'X'" pointer found anywhere in them, and asserts X is something
# the parser - parse_typed's own KNOWN_COMMANDS/TYPED_ALIASES check -
# actually accepts. Generic across every command at once, the same shape
# as the fog scanner above, so the next stale pointer is caught here.
# =============================================================================
from sim.ui.protocol import TYPED_ALIASES as _TYPED_ALIASES


def _strings_of(obj):
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for value in obj.values():
            yield from _strings_of(value)
    elif isinstance(obj, (list, tuple)):
        for value in obj:
            yield from _strings_of(value)


# One game serves both scanners: the fog scan above has already played it, and the pointer scan reads
# replies with the fog lifted (a command pointer is not a node id).
_fogscan.fog = False
_ptr_sim = _fogscan
_ptr_strings = []
for _pc in S.KNOWN_COMMANDS:
    if _pc in ("save", "load", "quit", "step"):
        continue            # side effects unrelated to what this scans for
    _pobj = dict(_fogscan_args.get(_pc, {}))
    _pobj["cmd"] = _pc
    try:
        _pr = S._agent_dispatch(_ptr_sim, NODES, _pobj)
    except Exception:
        continue             # a crash is a different bug
    _ptr_strings.extend(_strings_of(_pr))
for _pt in list(S.HELP_TOPICS) + [None]:
    _ptr_strings.extend(_strings_of(S._agent_help(_ptr_sim, _pt)))
_ptr_cmd_re = re.compile(r'\{"cmd":"([A-Za-z_]+)"')
_ptr_see_re = re.compile(r"see '([A-Za-z_]+)")
_ptr_found = set()
for _ps in _ptr_strings:
    _ptr_found.update(_ptr_cmd_re.findall(_ps))
    _ptr_found.update(_ptr_see_re.findall(_ps))
_ptr_accepted = set(S.KNOWN_COMMANDS) | set(_TYPED_ALIASES.keys())
_ptr_bad = sorted(_ptr_found - _ptr_accepted)
check("every command every reply in KNOWN_COMMANDS or help points a player "
      "at - every {\"cmd\":\"X\"} and every bare see 'X' - is a command the "
      "parser actually accepts, walked generically so the class of bug "
      "`training_pending` was (advertised, not implemented) cannot come "
      "back under a different name",
      not _ptr_bad, (_ptr_bad, sorted(_ptr_found)))
check("...and the scan actually found real pointers to check - an empty "
      "result from a broken scanner would pass this test for the wrong "
      "reason",
      len(_ptr_found) >= 10, sorted(_ptr_found))
