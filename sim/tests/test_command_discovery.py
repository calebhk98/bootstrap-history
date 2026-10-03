"""command_discovery: adding a command needs no edit outside its own handler.

Complaints/361. Dispatch modules load by discovery, the typed parser entry is
derived from the argument shape a command declares, the id-taking lists come
from the registry, and every command parses its documented typed usage.
"""
from .harness import *  # noqa: F401,F403
from sim.ui.proto import command_registry as _registry
from sim.ui.proto import dispatch as _dispatch
from sim.ui.proto import typed as _typed

# --- every dispatch_*.py file on disk was loaded, with no hand import list
_proto_dir = os.path.dirname(_dispatch.__file__)
_on_disk = sorted(name[:-3] for name in os.listdir(_proto_dir)
                  if name.startswith("dispatch_") and name.endswith(".py"))
_not_loaded = [name for name in _on_disk if "sim.ui.proto." + name not in sys.modules
               and "engine.proto." + name not in sys.modules
               and not any(module.endswith("proto." + name) for module in sys.modules)]
check("every dispatch_*.py module is loaded by discovery", not _not_loaded, _not_loaded)

# --- every typed usage in the registry parses (and its words reach a command)
_NUMBER_WORDS = re.compile(r"\b(n|years|hours|tonnes|count|amount|units|rate|share|number"
                           r"|tonnes_per_year)\b")
_bad_usage = []
for _name, _entry in _registry.COMMANDS.items():
    for _form in _entry["usage"]:
        if _form.startswith("{"):
            continue
        _line = re.sub(r"<([^>]*)>", lambda match: "5" if _NUMBER_WORDS.search(match.group(1)) else "iron", _form)
        _line = re.sub(r"\[[^\]]*\]", "", _line)
        _line = " ".join(token.split("|")[0] for token in _line.split())
        try:
            _parsed, _error = _typed.parse_typed(_line)
        except Exception as error:  # a parser crash is the failure
            _parsed, _error = None, repr(error)
        if _parsed is None or _error:
            _bad_usage.append((_name, _form, _error))
check("every registered command's documented typed usage parses", not _bad_usage, _bad_usage)

# --- no command is both hand-parsed and shape-derived
_both = [name for name, entry in _registry.COMMANDS.items()
         if entry.get("shape") and name in _typed._COMMAND_PARSERS]
check("a command has either a hand parser or a declared shape, not both", not _both, _both)

# --- the id-taking command lists are read from the registry
check("the fog-guarded id commands come from the registry",
      set(_registry.names_with_shape("tech")) >= {"why", "path", "start", "stop"}
      and "open" not in _registry.names_with_shape("tech")
      and "open" in _registry.names_with_shape("tech", "tech_done"),
      _registry.names_with_shape("tech"))

# --- a throwaway command of each shape needs no edit anywhere else
_registered = []
try:
    for _shape in ("bare", "tech", "file", "word"):
        _throwaway = "zz_shape_" + _shape

        @_registry.command(_throwaway, group="game", summary="probe", usage=[_throwaway],
                           description="Exists only for this test.", shape=_shape)
        def _cmd_probe(sim, nodes, cmd, ended):
            return {"ok": True}
        _registered.append(_throwaway)
    _got = {name: _typed.parse_typed(name + " thing")[0] for name in _registered}
    check("a bare-shaped command parses with no arguments",
          _typed.parse_typed("zz_shape_bare")[0] == {"cmd": "zz_shape_bare"})
    check("a file-shaped command carries its file",
          _got["zz_shape_file"] == {"cmd": "zz_shape_file", "file": "thing"}, _got["zz_shape_file"])
    check("a word-shaped command carries its word",
          _got["zz_shape_word"] == {"cmd": "zz_shape_word", "what": "thing"}, _got["zz_shape_word"])
    check("a tech-shaped command carries an id and is fog-guarded",
          _got["zz_shape_tech"].get("cmd") == "zz_shape_tech" and "id" in _got["zz_shape_tech"]
          and "zz_shape_tech" in _registry.names_with_shape("tech"), _got["zz_shape_tech"])
finally:
    for _throwaway in _registered:
        _registry.unregister(_throwaway)

# --- the help pages' hand text names only commands that exist, and the
# command index shows each command's registered text (no hand override)
from sim.ui.proto import help as _help
_help_sim = sim()
_index = _help._topic_commands(_help_sim)
_hand_overrides = [name for name in _registry.COMMANDS
                   if _index["commands"].get(name) != _help._command_text(name, _help_sim.fog)]
check("the command index shows every command's registered text", not _hand_overrides, _hand_overrides)
_known_words = set(_registry.COMMANDS) | set(_registry.alias_map())
_unknown_start = [key for key in _index["start here"]
                  if key != "the rest" and key.split()[0] not in _known_words]
check("every 'start here' entry names a registered command", not _unknown_start, _unknown_start)
_front = _help._front_page(_help_sim, False)
_front_unknown = sorted({found for found in re.findall(r'"cmd":"(\w+)"', json.dumps(_front).replace('\\"', '"'))
                         if found not in _known_words})
check("the front page names only registered commands", not _front_unknown, _front_unknown)
_front_five = [key.split()[0] for key in _front.get("the five you need first", {})]
check("the front page's five commands are registered",
      all(word in _known_words for word in _front_five), _front_five)
