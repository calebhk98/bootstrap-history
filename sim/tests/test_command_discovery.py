"""command_discovery: adding a command needs no edit outside its own handler.

Complaints/361. Dispatch modules load by discovery, the typed parser entry is
derived from the argument shape a command declares, the id-taking lists come
from the registry, and every command parses its documented typed usage.
"""
from .harness import *  # noqa: F401,F403
from sim.engine.proto import command_registry as _registry
from sim.engine.proto import dispatch as _dispatch
from sim.engine.proto import typed as _typed

# --- every dispatch_*.py file on disk was loaded, with no hand import list
_proto_dir = os.path.dirname(_dispatch.__file__)
_on_disk = sorted(name[:-3] for name in os.listdir(_proto_dir)
                  if name.startswith("dispatch_") and name.endswith(".py"))
_not_loaded = [name for name in _on_disk if "sim.engine.proto." + name not in sys.modules
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
