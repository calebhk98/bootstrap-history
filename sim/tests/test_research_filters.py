"""research_filters: the `available` state and tag filters and the search under fog, each called on the tree's own nodes
with a stand-in game holding the done, active, startable and revealed sets (no game, and no sweep of can_start over
the tree: Complaint 557). Tags are data and mods extend them."""
from types import SimpleNamespace

from .harness import check, NODES, ROOT

import json
import os
import re
import tempfile

from sim.engine import topic_tags as _topic_tags
from sim.engine.mods import ModError as _ModError
from sim.ui.proto import tree_filters
from sim.ui.proto.tree_filters import tags_of
from sim.ui.proto.typed import parse_typed as _parse_typed_line
from sim.tests.ui_stand_in import Game

QUICK_TOPIC = True

IDS = sorted(NODES)
DONE = set(IDS[:10])
ACTIVE = set(IDS[10:13])
STARTABLE = IDS[13:20]
HEARD = set(IDS[20:80])          # known but not startable
HIDDEN = [node_id for node_id in IDS[80:] if len(NODES[node_id]["name"]) > 12][:300]


def _game(fog):
    visible = DONE | ACTIVE | set(STARTABLE) | HEARD
    return Game(
        fog=fog, done=set(DONE), active={node_id: {} for node_id in ACTIVE}, revealed=set(HEARD) | set(STARTABLE),
        project_cost=lambda node_id: 100.0, start_reason=lambda node_id: (False, "not yet"),
        is_visible=lambda node_id: node_id in visible, stock_needed_by=lambda node_id: [])


def _reply(game, state="blocked", find=None, keep=None, paging=(True, 0, 20), subject="", sort_fn=None, reverse=False):
    known = tree_filters.known_ids(game, NODES, STARTABLE)
    return tree_filters.state_reply(game, NODES, state, find, subject, keep, known, STARTABLE, paging, sort_fn, reverse,
                                    lambda node: "")


plain = _game(fog=False)
fogged = _game(fog=True)
known_plain = tree_filters.known_ids(plain, NODES, STARTABLE)
known_fog = tree_filters.known_ids(fogged, NODES, STARTABLE)

# --- what each state lists
check("without fog every node is known", known_plain == set(NODES))
check("under fog what is known is what was heard of, started, finished or could begin",
      known_fog == HEARD | set(STARTABLE) | DONE | ACTIVE, len(known_fog))
check("state:startable lists exactly what can start", tree_filters.ids_in_state(plain, "startable", known_plain, STARTABLE)
      == STARTABLE)
check("state:active and state:done list exactly the running and the completed ones",
      sorted(tree_filters.ids_in_state(plain, "active", known_plain, STARTABLE)) == sorted(ACTIVE)
      and sorted(tree_filters.ids_in_state(plain, "done", known_plain, STARTABLE)) == sorted(DONE))
blocked_plain = set(tree_filters.ids_in_state(plain, "blocked", known_plain, STARTABLE))
check("state:blocked lists exactly the known nodes that are neither done, running nor startable",
      blocked_plain == set(NODES) - DONE - ACTIVE - set(STARTABLE) and not blocked_plain & set(STARTABLE))
blocked_fog = set(tree_filters.ids_in_state(fogged, "blocked", known_fog, STARTABLE))
check("under fog the blocked list is exactly the heard-of, unstartable nodes", blocked_fog == HEARD, len(blocked_fog))

# --- the reply
blocked = _reply(plain)
check("the reply names its state and count", blocked["state"] == "blocked" and blocked["count"] == len(blocked_plain))
check("every blocked row says why, and carries its tags and what is missing",
      blocked["rows"] and all(row["why_not"] and "tags" in row and "missing" in row for row in blocked["rows"]))
check("blocked rows are not startable ones", not any(row["id"] in STARTABLE for row in blocked["rows"]))
nearest = [sum(1 for prereq in NODES[row["id"]]["pre"] if prereq not in DONE) for row in blocked["rows"]]
check("blocked rows come nearest to startable first (fewest missing prerequisites)", nearest == sorted(nearest), nearest[:10])
paged = _reply(plain, paging=(False, 0, 5))
check("blocked list pages like the startable one", len(paged["rows"]) == 5 and "offset" in (paged.get("more") or ""))
last = _reply(plain, paging=(False, len(blocked_plain) - 2, 5))
check("the last page has two rows and no 'more'", len(last["rows"]) == 2 and "more" not in last)

# --- under fog a missing prerequisite that is hidden is counted, not named
with_hidden = next(node_id for node_id in sorted(HEARD) if any(prereq not in DONE and prereq not in HEARD | set(STARTABLE) | ACTIVE
                                                                  for prereq in NODES[node_id]["pre"]))
row = next(row for row in _reply(fogged)["rows"] if row["id"] == with_hidden)
named_hidden = [prereq for prereq in row["missing"] if prereq not in HEARD | set(STARTABLE) | ACTIVE | DONE]
check("a hidden missing prerequisite is counted in the row, never named",
      row["hidden_missing"] >= 1 and not named_hidden, (row["missing"], row["hidden_missing"]))

# --- states, tags and categories
check("typed 'available blocked' sets the state", (_parse_typed_line("available blocked")[0] or {}).get("state") == "blocked")
parsed = _parse_typed_line("available state blocked tag mechanical_power")[0] or {}
check("typed state and tag words parse together", parsed.get("state") == "blocked" and parsed.get("tag") == "mechanical_power", parsed)
parsed = _parse_typed_line("available state:active category:power")[0] or {}
check("key:value spelling works for state and category", parsed.get("state") == "active" and parsed.get("category") == "power", parsed)
check("a state alias reads as its state",
      tree_filters.parse_state({"state": "completed"})[0] == "done" and tree_filters.parse_state({"state": "running"})[0] == "active"
      and tree_filters.parse_state({})[0] is None)
_state, refusal = tree_filters.parse_state({"state": "sideways"})
check("an unknown state is refused with the valid ones named",
      _state is None and refusal.cause == "unknown_state" and "blocked" in refusal.choices, refusal)

tag, category, error = tree_filters.parse_topic({"tag": "mechanical_power"}, NODES)
keep = tree_filters.topic_keeper(NODES, tag, category)
tagged = _reply(plain, keep=keep)
check("a tag filter returns only nodes carrying that tag",
      tagged["rows"] and all("mechanical_power" in row["tags"] for row in tagged["rows"]) and error is None)
tag, category, error = tree_filters.parse_topic({"category": "metallurgy"}, NODES)
categorised = _reply(plain, keep=tree_filters.topic_keeper(NODES, tag, category))
check("a category filter matches the node's own category",
      categorised["rows"] and all(NODES[row["id"]]["cat"] == "metallurgy" for row in categorised["rows"]))
check("with neither a tag nor a category there is no filter", tree_filters.topic_keeper(NODES, "", "") is None)
_tag, _category, refusal = tree_filters.parse_topic({"tag": "no_such_tag"}, NODES)
check("an unknown tag is refused and the real tags are listed",
      refusal.cause == "unknown_tag" and "mechanical_power" in refusal.choices, refusal)
check("an unknown category is refused", tree_filters.parse_topic({"category": "no_such_category"}, NODES)[2] is not None)

# --- search under fog: only what the player may see
def _leaks(out, hidden):
    text = json.dumps(out).lower()
    return [node_id for node_id in hidden
            if re.search(r"(?<![a-z0-9_])%s(?![a-z0-9_])" % re.escape(node_id.lower()), text)]


check("there are hidden nodes to test leakage against", len(HIDDEN) > 50)
hidden_named = HIDDEN[0]
hidden_query = NODES[hidden_named]["name"].lower()
nonsense = "zzqxv wwkjh"
out_hidden = _reply(fogged, find=hidden_query)
out_nonsense = _reply(fogged, find=nonsense)
check("searching a hidden node's name finds nothing of it",
      hidden_named not in {row["id"] for row in out_hidden["rows"]} and not _leaks(out_hidden, [hidden_named]))
check("a hidden name and pure nonsense get the same reply shape, so absence cannot be told from hiddenness",
      set(out_hidden) == set(out_nonsense), (sorted(out_hidden), sorted(out_nonsense)))
for query in ("gear", "steam", "rotary", "education", hidden_query, nonsense):
    for state in ("startable", "blocked", "done"):
        out = _reply(fogged, state=state, find=query)
        leaked = _leaks(out, HIDDEN)
        check("search %r (%s) under fog never names a hidden id" % (query, state), not leaked, leaked[:5])
visible_word = next(NODES[node_id]["name"].split()[0].lower().strip(",") for node_id in sorted(HEARD)
                    if len(NODES[node_id]["name"].split()[0].strip(",")) > 4)
check("search under fog finds a visible node by a word in its name",
      any(visible_word in NODES[row["id"]]["name"].lower() for row in _reply(fogged, find=visible_word)["rows"]))

# --- the vocabulary of a tag reaches the nodes of its categories
power_node = next(node_id for node_id in IDS if NODES[node_id]["cat"] == "power")
check("a vocabulary word (rotary) reaches a node of the mechanical power tag that never names it",
      "rotary" not in (NODES[power_node]["name"] + power_node).lower() and tree_filters.matches_find(NODES, "rotary", power_node))
check("every query word must match, but any_term needs one",
      not tree_filters.matches_find(NODES, "rotary zzqxv", power_node)
      and tree_filters.matches_find(NODES, "rotary zzqxv", power_node, any_term=True))
check("an empty query matches nothing", not tree_filters.matches_find(NODES, "", power_node))

# --- an empty search says something useful, from visible nodes only
empty = _reply(fogged, find=nonsense)
hint = empty["try_instead"]
check("an empty search suggests tags and states which states it looked in",
      empty["count"] == 0 and empty.get("nothing_matched") and hint["tags"], hint["tags"])
check("the empty-search tag counts cover only what the player can see",
      all(entry["visible"] <= len(known_fog) for entry in hint["tags"])
      and sum(entry["startable"] for entry in hint["tags"]) <= len(STARTABLE) * len(hint["tags"]))
close = tree_filters.try_instead(fogged, NODES, "gear", known_fog, STARTABLE)
check("the closest nodes it names are all known ones", all(entry["id"] in known_fog for entry in close["closest_visible"]))
check("a search that misses startable nodes reports the blocked matches by count",
      tree_filters.blocked_match_count(fogged, NODES, "gear", None, known_fog, STARTABLE)
      == len(_reply(fogged, find="gear")["rows"]))

# --- tags are data, and mods extend them
_tag_base = os.path.join(ROOT, "data", "world", "topic_tags.json")
check("the base tags live in a data file", os.path.isfile(_tag_base))


def _tag_mod(parent, mod_id, tags):
    folder = os.path.join(parent, mod_id)
    os.makedirs(os.path.join(folder, "data", "world"))
    with open(os.path.join(folder, "mod.json"), "w") as handle:
        json.dump({"id": mod_id, "name": mod_id, "version": "1", "dependencies": [], "conflicts": []}, handle)
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
              "metallurgy" in _merged["agriculture"]["cats"] and "soil" in _merged["agriculture"]["cats"]
              and "scythe" in _merged["agriculture"]["words"])
        _keep = tree_filters.topic_keeper(NODES, "test_arcane_k3f9:sorcery", "")
        check("`available tag:<new>` keeps exactly the new tag's nodes, and their rows carry the new tag",
              _weaving_ids and [node_id for node_id in IDS if _keep(node_id)] == _weaving_ids
              and all("test_arcane_k3f9:sorcery" in tags_of(NODES[node_id]) for node_id in _weaving_ids))
        check("a mod's search word reaches the tag's nodes",
              tree_filters.matches_find(NODES, "spell", _weaving_ids[0]))
        check("an extended tag now covers the added category",
              "agriculture" in tags_of(next(node for node in NODES.values() if node["cat"] == "metallurgy")))
    finally:
        _topic_tags.use_mods_dir(None)
    check("the default tags come back once the mod is gone", "test_arcane_k3f9:sorcery" not in _topic_tags.current())

with tempfile.TemporaryDirectory() as _bad_tmp:
    _tag_mod(_bad_tmp, "test_arcane_k3f9", {"sorcery": {"cats": ["weaving"]}})
    _refused = False
    try:
        _topic_tags.load_topic_tags(ROOT, _bad_tmp)
    except _ModError:
        _refused = True
    check("a new tag outside the mod namespace is refused", _refused)
