"""help_registry: help is generated from the command registry, so no command can be missing from it."""
from .harness import *  # noqa: F401,F403

_help_sim = sim()


def _dispatch_help(topic=None):
    reply = S._agent_dispatch(_help_sim, NODES, {"cmd": "help", "topic": topic})
    return reply["help"]


def _mentioned(text, word):
    return re.search(r"(?<![A-Za-z_])%s(?![A-Za-z_])" % re.escape(word), text) is not None


# --- the front index names every command the JSON dispatcher runs, and every
# typed alias, each with a summary
_index = _dispatch_help("commands")
_index_text = json.dumps(_index)
_dispatchable = sorted(set(_protocol._AGENT_DISPATCH_TABLE) | set(S.KNOWN_COMMANDS))
_missing = [word for word in _dispatchable if not _mentioned(_index_text, word)]
check("`help commands` lists every command the dispatcher accepts",
      not _missing, _missing)
_missing_aliases = [word for word in _protocol.TYPED_ALIASES
                    if not _mentioned(_index_text, word)]
check("`help commands` lists every typed alias", not _missing_aliases, _missing_aliases)

# --- every accepted word has its own help page with usage and description
_no_page = []
_empty = []
for _word in sorted(set(_dispatchable) | set(_protocol.TYPED_ALIASES)):
    _page = _dispatch_help(_word)
    _entry = _page.get("command") if isinstance(_page, dict) else None
    if not isinstance(_entry, dict):
        _no_page.append(_word)
    elif not (_entry.get("usage") and _entry.get("description") and _entry.get("summary")):
        _empty.append(_word)
check("`help <word>` gives a command page for every command and alias",
      not _no_page, _no_page)
check("...and every page has a summary, usage and description",
      not _empty, _empty)

_alias_page = _dispatch_help("ledger")["command"]
check("`help <alias>` shows the page of the command it stands for",
      _alias_page["name"] == "money", _alias_page.get("name"))
check("a command's page lists its aliases", "ledger" in _alias_page["aliases"],
      _alias_page.get("aliases"))

# --- unknown words are answered with near matches
_unknown = _dispatch_help("stuk")
check("`help <unknown>` suggests close matches",
      "stuck" in _unknown.get("did you mean", []), _unknown)
check("...and still lists the topics", bool(_unknown.get("topics")), _unknown)

# --- topics that share a name with a command keep their text and gain the page
_money = _dispatch_help("money")
check("a topic sharing a command's name keeps its topic text and adds the page",
      "where it comes from" in _money and _money.get("command", {}).get("name") == "money",
      sorted(_money))

# --- the topic list is generated too
check("the front page links every registered topic",
      all(name in _dispatch_help(None)["more"] for name in S.HELP_TOPICS),
      S.HELP_TOPICS)

# --- a throwaway command registration shows up in help with no other edit
from sim.engine.proto import command_registry as _registry
from sim.engine.proto.typed import parse_typed


@_registry.command("zz_throwaway", group="game", summary="a throwaway probe",
                   usage=["zz_throwaway <n>"], description="Exists only for this test.",
                   options={"n": "how many"}, aliases=("zzt",), shape="file")
def _cmd_zz_throwaway(sim, nodes, cmd, ended):
    return {"ok": True}


try:
    _throwaway_text = json.dumps(_dispatch_help("commands"))
    check("a newly registered command appears in `help commands`",
          _mentioned(_throwaway_text, "zz_throwaway") and _mentioned(_throwaway_text, "zzt"))
    _throwaway_page = _dispatch_help("zzt")["command"]
    check("...and has its own page under its alias",
          _throwaway_page["name"] == "zz_throwaway"
          and _throwaway_page["options"] == {"n": "how many"}
          and _throwaway_page["usage"] == ["zz_throwaway <n>"], _throwaway_page)
    check("...and its typed line parses by its declared shape, by name or alias",
          parse_typed("zzt out.json")[0] == {"cmd": "zz_throwaway", "file": "out.json"},
          parse_typed("zzt out.json"))
    check("...and the registry can build the dispatch table entry for it",
          _registry.handlers().get("zz_throwaway") is _cmd_zz_throwaway)
finally:
    _registry.unregister("zz_throwaway")
check("unregistering removes it again",
      not _mentioned(json.dumps(_dispatch_help("commands")), "zz_throwaway"))

# --- PROTOCOL.md points at help rather than keeping its own list
_protocol_md = open(os.path.join(HERE, "PROTOCOL.md")).read()
check("PROTOCOL.md says help is the complete, generated command list",
      "command_registry" in _protocol_md and '"cmd":"help"' in _protocol_md)
