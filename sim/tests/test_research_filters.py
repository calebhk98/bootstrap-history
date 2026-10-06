"""research_filters: `available` state and tag filters, and search under fog."""
from .harness import *  # noqa: F401,F403
from sim.ui.proto.tree_filters import tags_of
from sim.ui.proto.typed import parse_typed as _parse_typed_line


def _ask(test_sim, **cmd):
    return S._agent_dispatch(test_sim, NODES, {"cmd": "available", **cmd})


def _rows(out):
    return out.get("rows") if "rows" in out else out.get("available")


def _fogged(revealed_count=60):
    fogged = sim(capital=1_000_000.0)
    fogged.fog = True
    startable = [node_id for node_id in fogged.order if fogged.can_start(node_id)]
    # A spread of nodes the player has heard of but cannot begin.
    heard = [node_id for node_id in fogged.order
             if node_id not in startable and node_id not in fogged.done][:revealed_count]
    fogged.revealed = set(heard) | set(startable)
    return fogged, startable, heard


# --- state filters, no fog
plain = sim(capital=1_000_000.0)
plain_startable = sorted(node_id for node_id in plain.order if plain.can_start(node_id))
plain_blocked = sorted(node_id for node_id in plain.order
                       if node_id not in plain.done and node_id not in plain.active
                       and not plain.can_start(node_id))

startable_out = _ask(plain, state="startable", all=True)
check("state:startable lists exactly what can start",
      sorted(row["id"] for row in _rows(startable_out)) == plain_startable,
      startable_out.get("error"))

blocked_out = _ask(plain, state="blocked", all=True)
blocked_rows = _rows(blocked_out) or []
check("state:blocked lists exactly the known, unstartable nodes",
      sorted(row["id"] for row in blocked_rows) == plain_blocked,
      (len(blocked_rows), len(plain_blocked), blocked_out.get("error")))
check("every blocked row says why, and carries its tags",
      bool(blocked_rows) and all(row.get("why_not") and "tags" in row for row in blocked_rows))
check("blocked rows are not startable ones",
      not any(row["id"] in plain_startable for row in blocked_rows))
check("the reply names its state and count",
      blocked_out.get("state") == "blocked" and blocked_out.get("count") == len(plain_blocked),
      (blocked_out.get("state"), blocked_out.get("count")))

paged = _ask(plain, state="blocked", limit=5)
check("blocked list pages like the startable one",
      len(_rows(paged)) == 5 and "offset" in (paged.get("more") or ""), paged.get("more"))

first_startable = plain_startable[0]
started_ok, _why_started = plain.start_project(first_startable)
active_out = _ask(plain, state="active", all=True)
check("state:active lists exactly the running projects",
      started_ok and sorted(row["id"] for row in _rows(active_out)) == sorted(plain.active),
      (_rows(active_out), sorted(plain.active)))
plain.done.add("pottery") if "pottery" in NODES else None
done_out = _ask(plain, state="done", all=True)
check("state:done lists exactly the completed ones",
      sorted(row["id"] for row in _rows(done_out)) == sorted(plain.done),
      done_out.get("error"))

bad_state = _ask(plain, state="sideways")
check("an unknown state is refused with the valid ones named",
      bad_state.get("ok") is False and "blocked" in bad_state.get("error", ""),
      bad_state)

# --- tag and category filters
tag_out = _ask(plain, state="blocked", tag="mechanical_power", all=True)
tag_rows = _rows(tag_out) or []
check("a tag filter returns only nodes carrying that tag",
      bool(tag_rows) and all("mechanical_power" in row["tags"] for row in tag_rows),
      tag_out.get("error"))
cat_out = _ask(plain, state="blocked", category="metallurgy", all=True)
check("a category filter matches the node's own category",
      bool(_rows(cat_out)) and all(NODES[row["id"]]["cat"] == "metallurgy" for row in _rows(cat_out)),
      cat_out.get("error"))
start_tag = _ask(plain, tag="mechanical_power", all=True)
check("the tag filter narrows the startable list too",
      start_tag.get("ok") is True and start_tag.get("tag") == "mechanical_power"
      and all("mechanical_power" in tags_of(NODES[row["id"]]) for row in _rows(start_tag)),
      start_tag.get("error"))
bad_tag = _ask(plain, tag="no_such_tag")
check("an unknown tag is refused and the real tags are listed",
      bad_tag.get("ok") is False and "mechanical_power" in bad_tag.get("error", ""), bad_tag)

# --- typed parsing
parsed, _err = _parse_typed_line("available blocked")
check("typed 'available blocked' sets the state", parsed and parsed.get("state") == "blocked", parsed)
parsed, _err = _parse_typed_line("available state blocked tag mechanical_power")
check("typed state and tag words parse together",
      parsed and parsed.get("state") == "blocked" and parsed.get("tag") == "mechanical_power",
      parsed)
parsed, _err = _parse_typed_line("available state:active category:power")
check("key:value spelling works for state and category",
      parsed and parsed.get("state") == "active" and parsed.get("category") == "power", parsed)

# --- fog: filters only see what the player has heard of
fogged, fog_startable, fog_heard = _fogged()
fog_blocked = _ask(fogged, state="blocked", all=True)
fog_ids = {row["id"] for row in _rows(fog_blocked) or []}
check("fogged blocked list is exactly the heard-of, unstartable nodes",
      fog_ids == set(fog_heard), (len(fog_ids), len(fog_heard), fog_blocked.get("error")))
hidden_ids = [node_id for node_id in NODES if node_id not in fogged.revealed
              and node_id not in fogged.done and not fogged.is_visible(node_id)]
check("there are hidden nodes to test leakage against", bool(hidden_ids))


def _leaks(out, hidden):
    text = json.dumps(out).lower()
    return [node_id for node_id in hidden
            if re.search(r"(?<![a-z0-9_])%s(?![a-z0-9_])" % re.escape(node_id.lower()), text)]


leaked = _leaks(fog_blocked, hidden_ids)
check("fogged blocked rows never name a hidden id", not leaked, leaked[:5])

# --- fog: search
word_hits = [node_id for node_id in fog_heard + fog_startable
             if "gear" in NODES[node_id]["name"].lower()]
probe_id = word_hits[0] if word_hits else None
if probe_id is None:
    probe_id = next(node_id for node_id in fog_heard)
probe_word = NODES[probe_id]["name"].split()[0].lower().strip(",")
found = _ask(fogged, find=probe_word, state="blocked", all=True)
check("search under fog finds a visible node by a word in its name",
      probe_id in {row["id"] for row in _rows(found) or []} or
      probe_id in fog_startable,
      (probe_word, found.get("error")))

# A hidden node's own name as the query must look exactly like nonsense.
hidden_named = next(node_id for node_id in hidden_ids if len(NODES[node_id]["name"]) > 12)
hidden_query = NODES[hidden_named]["name"].lower()
nonsense = "zzqxv wwkjh"
out_hidden = _ask(fogged, find=hidden_query)
out_nonsense = _ask(fogged, find=nonsense)


def _strip_echo(out, query):
    return json.dumps(out).replace(query, "<q>")


check("searching a hidden node's name finds nothing of it",
      not _leaks(out_hidden, [hidden_named]) and out_hidden.get("count") == 0
      or hidden_named not in {row["id"] for row in _rows(out_hidden) or []},
      out_hidden.get("count"))
check("a hidden name and pure nonsense get the same reply shape, so absence "
      "cannot be told from hiddenness",
      set(out_hidden) == set(out_nonsense), (sorted(out_hidden), sorted(out_nonsense)))

for query in ("gear", "steam", "rotary", "education", hidden_query, nonsense):
    for state in (None, "blocked"):
        out = _ask(fogged, find=query, **({"state": state} if state else {}), all=True)
        leaked = _leaks(out, hidden_ids)
        check("search %r (%s) under fog never names a hidden id" % (query, state or "startable"),
              not leaked, leaked[:5])

# Synonyms land on the broader tag, but only among what is visible.
fogged.revealed = set(fog_heard) | set(fog_startable)
power_ids = {node_id for node_id in NODES if NODES[node_id]["cat"] == "power"}
fogged.revealed |= power_ids
syn = _ask(fogged, find="rotary", state="blocked", all=True)
syn_ids = {row["id"] for row in _rows(syn) or []}
check("a vocabulary word (rotary) reaches visible nodes of the mechanical power tag",
      bool(syn_ids) and syn_ids <= (fogged.revealed | set(fogged.done)),
      (len(syn_ids), syn.get("error")))

# An empty search says something useful, from visible nodes only.
empty = _ask(fogged, find=nonsense)
check("an empty search suggests tags and states which states it looked in",
      empty.get("count") == 0 and empty.get("try_instead") and empty["try_instead"].get("tags"),
      empty.get("try_instead"))
check("the empty-search tag counts cover only what the player can see",
      all(entry["visible"] <= len(fogged.revealed) + len(fogged.done) + len(fog_startable)
          for entry in empty["try_instead"]["tags"]))
blocked_hint = _ask(fogged, find="gear")
check("a search that misses startable nodes reports blocked matches by count",
      "known_but_blocked_matches" in blocked_hint, sorted(blocked_hint))

# --- tags are data, and mods extend them
from sim.engine import topic_tags as _topic_tags
from sim.engine.mods import ModError as _ModError

_tag_base = os.path.join(ROOT, "data", "world", "topic_tags.json")
check("the base tags live in a data file", os.path.isfile(_tag_base))


def _tag_mod(parent, mod_id, tags):
    folder = os.path.join(parent, mod_id)
    os.makedirs(os.path.join(folder, "data", "world"))
    with open(os.path.join(folder, "mod.json"), "w") as handle:
        json.dump({"id": mod_id, "name": mod_id, "version": "1",
                   "dependencies": [], "conflicts": []}, handle)
    with open(os.path.join(folder, "data", "world", "topic_tags.json"), "w") as handle:
        json.dump({"tags": tags}, handle)


_weaving_ids = sorted(node_id for node_id, node in NODES.items() if node["cat"] == "weaving")
with tempfile.TemporaryDirectory() as _mods_tmp:
    _tag_mod(_mods_tmp, "test_arcane_k3f9", {
        "test_arcane_k3f9:sorcery": {"cats": ["weaving"], "words": ["spell"]},
        "agriculture": {"cats": ["metallurgy"], "words": ["scythe"]}})
    _topic_tags.use_mods_dir(_mods_tmp)
    try:
        _merged = _topic_tags.current()
        check("a mod adds a new tag", "test_arcane_k3f9:sorcery" in _merged, sorted(_merged))
        check("a mod extends an existing tag without dropping its categories",
              "metallurgy" in _merged["agriculture"]["cats"]
              and "soil" in _merged["agriculture"]["cats"]
              and "scythe" in _merged["agriculture"]["words"])
        _mod_sim = plain
        _new = _ask(_mod_sim, state="blocked", tag="test_arcane_k3f9:sorcery", all=True)
        _new_ids = sorted(row["id"] for row in _rows(_new) or [])
        _expected = sorted(node_id for node_id in _weaving_ids
                           if node_id not in _mod_sim.done and node_id not in _mod_sim.active
                           and not _mod_sim.can_start(node_id))
        check("`available tag:<new>` finds the new tag's nodes",
              bool(_new_ids) and _new_ids == _expected, (_new.get("error"), len(_new_ids)))
        check("...and their rows carry the new tag",
              all("test_arcane_k3f9:sorcery" in row["tags"] for row in _rows(_new)))
        _spell = _ask(_mod_sim, find="spell", state="blocked", all=True)
        check("a mod's search word reaches the tag's nodes",
              bool(_rows(_spell)), _spell.get("error"))
        _ext = _ask(_mod_sim, state="blocked", tag="agriculture", category="metallurgy", all=True)
        check("an extended tag now covers the added category",
              bool(_rows(_ext)), _ext.get("error"))
    finally:
        _topic_tags.use_mods_dir(None)
    check("the default tags come back once the mod is gone",
          "test_arcane_k3f9:sorcery" not in _topic_tags.current())

with tempfile.TemporaryDirectory() as _bad_tmp:
    _tag_mod(_bad_tmp, "test_arcane_k3f9", {"sorcery": {"cats": ["weaving"]}})
    _refused = False
    try:
        _topic_tags.load_topic_tags(ROOT, _bad_tmp)
    except _ModError:
        _refused = True
    check("a new tag outside the mod namespace is refused", _refused)
