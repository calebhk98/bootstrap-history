"""State, tag and category filters for the research list, and the forgiving search that goes with them.

Everything here works from the set of nodes the player may see, so a filter
or a search can never reveal what fog hides.
"""

import difflib

from sim.engine.ui_port import topic_tags

STATES = ("startable", "blocked", "active", "done")
_STATE_ALIASES = {"completed": "done", "complete": "done", "finished": "done",
                  "running": "active", "available": "startable",
                  "startable_now": "startable"}

_SUFFIXES = ("ation", "ition", "ing", "ions", "ion", "ers", "er", "ed", "es", "al",
             "ic", "s")


def stem(term):
    """A crude stem: the term without a common ending, if a useful root is left."""
    for suffix in _SUFFIXES:
        if term.endswith(suffix) and len(term) - len(suffix) >= 4:
            return term[:-len(suffix)]
    return term


def tags_of(node):
    """The broad topic tags a node belongs to, by its category."""
    cat = node.get("cat", "")
    return [tag for tag, spec in topic_tags.current().items() if cat in spec["cats"]]


def _tag_words_hit(tag, term):
    root = stem(term)
    return any(term == word or root == stem(word) or
               (len(root) >= 4 and word.startswith(root))
               for word in topic_tags.current()[tag]["words"])


def _search_terms(find):
    return [term for term in find.replace("_", " ").split() if term]


def _haystack(nodes, node_id):
    node = nodes[node_id]
    aliases = node.get("aliases") or []
    if isinstance(aliases, str):
        aliases = [aliases]
    return " ".join([node_id.replace("_", " "), node_id, node.get("name", ""),
                     node.get("cat", "").replace("_", " ")]
                    + aliases).lower()


def term_hits(nodes, node_id, term, haystack=None):
    """Whether one search word reaches a node: text, stem, or topic vocabulary."""
    haystack = haystack if haystack is not None else _haystack(nodes, node_id)
    if term in haystack or stem(term) in haystack:
        return True
    return any(_tag_words_hit(tag, term) for tag in tags_of(nodes[node_id]))


def matches_find(nodes, find, node_id, any_term=False):
    """Every query word (or, with any_term, at least one) reaches the node."""
    terms = _search_terms(find)
    if not terms:
        return False
    haystack = _haystack(nodes, node_id)
    hits = [term_hits(nodes, node_id, term, haystack) for term in terms]
    return any(hits) if any_term else all(hits)


def parse_state(cmd):
    """The requested state, or None for the default; second item is an error."""
    raw = str(cmd.get("state") or "").strip().strip('"\'').lower()
    if not raw:
        return None, None
    state = _STATE_ALIASES.get(raw, raw)
    if state not in STATES:
        return None, ("unknown state %r; the states are %s." % (raw, ", ".join(STATES)))
    return state, None


def subject_names():
    """The subject headings `available <subject>` knows, in order."""
    from .techtree import SUBJECTS
    return list(SUBJECTS.values())


def parse_topic(cmd, nodes):
    """(tag, category, error) from the tag and category options."""
    tag = str(cmd.get("tag") or "").strip().strip('"\'').lower().replace(" ", "_")
    category = str(cmd.get("category") or cmd.get("cat") or "").strip().strip('"\'').lower()
    category = category.replace(" ", "_")
    if tag and tag not in topic_tags.current():
        near = difflib.get_close_matches(tag, list(topic_tags.current()), n=3)
        return "", "", ("unknown tag %r%s. The tags are: %s. Tags and subjects are different lists; "
                        "to look for a word or a subject type 'available %s' (subjects: %s)." % (
            tag, (" (did you mean %s?)" % ", ".join(near)) if near else "",
            ", ".join(topic_tags.current()), tag.replace("_", " "), ", ".join(subject_names())))
    if category:
        cats = {node["cat"] for node in nodes.values()}
        if category not in cats:
            near = difflib.get_close_matches(category, sorted(cats), n=5)
            return "", "", ("unknown category %r%s." % (
                category, (" Close: %s." % ", ".join(near)) if near else
                " Try a tag instead, e.g. tag:mechanical_power."))
    return tag, category, None


def topic_keeper(nodes, tag, category):
    """A predicate for the tag and category filters, or None when neither is set."""
    if not tag and not category:
        return None
    return lambda node_id: ((not tag or tag in tags_of(nodes[node_id]))
                            and (not category or nodes[node_id]["cat"] == category))


def known_ids(sim, nodes, startable):
    """Every node the player is entitled to see: all of them, or under fog
    what they have heard of, started, finished or could begin.
    """
    if not sim.fog:
        return set(nodes)
    return set(getattr(sim, "revealed", ())) | set(sim.done) | set(sim.active) | set(startable)


def blocked_ids(sim, known, startable):
    startable_set = set(startable)
    return [node_id for node_id in known
            if node_id not in sim.done and node_id not in sim.active
            and node_id not in startable_set]


def ids_in_state(sim, state, known, startable):
    if state == "startable":
        return list(startable)
    if state == "blocked":
        return blocked_ids(sim, known, startable)
    if state == "active":
        return [node_id for node_id in sim.active if node_id in known]
    return [node_id for node_id in sim.done if node_id in known]


def _row(sim, nodes, node_id, state):
    node = nodes[node_id]
    row = {"id": node_id, "name": node["name"], "cat": node["cat"],
           "tags": tags_of(node), "state": state,
           "cost": round(sim.project_cost(node_id), 1)}
    if state == "blocked":
        missing = [prereq for prereq in node["pre"] if prereq not in sim.done]
        shown = [prereq for prereq in missing if not sim.fog or sim.is_visible(prereq)]
        row["why_not"] = sim.start_reason(node_id)[1]
        row["missing"] = shown
        row["hidden_missing"] = len(missing) - len(shown)
    stock = sim.stock_needed_by(node_id)
    if stock:
        row["living_stock"] = stock
    return row


def _orderer(sim, nodes, state, sort_fn, reverse):
    if sort_fn:
        return lambda ids: sorted(ids, key=lambda k: (sort_fn(sim, nodes, k), k), reverse=reverse)
    if state == "blocked":
        # nearest to startable first
        return lambda ids: sorted(ids, key=lambda k: (
            sum(1 for prereq in nodes[k]["pre"] if prereq not in sim.done), k))
    return lambda ids: sorted(ids)


def tag_overview(sim, nodes, known, startable, terms=()):
    """Per-tag counts of what the player can see, for empty results. Tags whose
    vocabulary reaches any search word come first.
    """
    startable_set = set(startable)
    entries = []
    for tag in topic_tags.current():
        members = [node_id for node_id in known if tag in tags_of(nodes[node_id])]
        if not members:
            continue
        related = any(_tag_words_hit(tag, term) or stem(term) in tag for term in terms)
        entries.append({"tag": tag, "visible": len(members),
                        "startable": sum(1 for node_id in members if node_id in startable_set),
                        "blocked": sum(1 for node_id in members
                                       if node_id not in startable_set
                                       and node_id not in sim.done and node_id not in sim.active),
                        "_related": related})
    entries.sort(key=lambda entry: (not entry["_related"], -entry["visible"], entry["tag"]))
    for entry in entries:
        entry.pop("_related")
    return entries[:6]


def try_instead(sim, nodes, find, known, startable):
    """What to do after a search finds nothing, built only from visible nodes."""
    terms = _search_terms(find)
    startable_set = set(startable)
    close = [node_id for node_id in sorted(known)
             if terms and matches_find(nodes, find, node_id, any_term=True)]
    close.sort(key=lambda node_id: (node_id not in startable_set, node_id))
    return {
        "tags": tag_overview(sim, nodes, known, startable, terms),
        "closest_visible": [{"id": node_id, "name": nodes[node_id]["name"],
                             "state": _state_of(sim, node_id, startable_set)}
                            for node_id in close[:5]],
        "how": ("filter by topic with tag:<tag>, by state with state:blocked, "
                "or try one shorter word; every word you type must match."),
    }


def _state_of(sim, node_id, startable_set):
    if node_id in sim.done:
        return "done"
    if node_id in sim.active:
        return "active"
    return "startable" if node_id in startable_set else "blocked"


def blocked_match_count(sim, nodes, find, keep, known, startable):
    """How many known, blocked nodes a search or topic would show."""
    return sum(1 for node_id in blocked_ids(sim, known, startable)
               if (not find or matches_find(nodes, find, node_id))
               and (keep is None or keep(node_id)))


def state_reply(sim, nodes, state, find, want_subject, keep, known, startable, paging, sort_fn,
                reverse, subject_of):
    """The list for one state: known nodes only, filtered, ordered and paged.
    `paging` is (show_all, offset, limit).
    """
    show_all, offset, limit = paging
    ids = ids_in_state(sim, state, known, startable)
    if find:
        ids = [node_id for node_id in ids if matches_find(nodes, find, node_id)]
    elif want_subject:
        ids = [node_id for node_id in ids if want_subject in subject_of(nodes[node_id]).lower()]
    if keep is not None:
        ids = [node_id for node_id in ids if keep(node_id)]
    ids = _orderer(sim, nodes, state, sort_fn, reverse)(ids)
    page = ids if show_all else ids[offset:offset + limit]
    out = {"ok": True, "state": state, "count": len(ids),
           "showing": ("nothing" if not page else "%d-%d" % (offset + 1, offset + len(page))),
           "rows": [_row(sim, nodes, node_id, state) for node_id in page]}
    if state == "blocked":
        out["blocked_note"] = ("Known but not startable yet; each row says what is "
                               "missing. Use state:startable for what you can begin.")
    if not show_all and offset + len(page) < len(ids):
        out["more"] = 'ask again with "offset": %d' % (offset + len(page))
    if not page and (find or keep is not None):
        out["nothing_matched"] = ("Nothing you know of in state %s matches that." % state)
        out["try_instead"] = try_instead(sim, nodes, find, known, startable)
    return out


def stock_line(row):
    """What living stock a row's node needs held, beside what is held."""
    return "HELD: " + "; ".join(
        "%s %s of %s needed" % (gate["material"], _held_figure(gate["held"]), _held_figure(gate["needed"]))
        for gate in row["living_stock"])


def _held_figure(units):
    return ("%.3f" % units).rstrip("0").rstrip(".")


def render_state_rows(out):
    """Plain-text table for a state list."""
    lines = ["RESEARCH, state %s: %s" % (out["state"], out.get("count")), out.get("showing", "")]
    for row in out.get("rows", []):
        lines.append("  %-34s %-22s %s" % (row["id"], ",".join(row["tags"]) or row["cat"],
                                           row.get("why_not") or row["name"]))
        if row.get("living_stock"):
            lines.append("      " + stock_line(row))
    if out.get("blocked_note"):
        lines += ["", out["blocked_note"]]
    if out.get("nothing_matched"):
        lines += ["", out["nothing_matched"]]
        hint = out.get("try_instead") or {}
        for entry in hint.get("tags", []):
            lines.append("  tag %-24s %d visible, %d startable, %d blocked" % (
                entry["tag"], entry["visible"], entry["startable"], entry["blocked"]))
        lines.append(hint.get("how", ""))
    if out.get("more"):
        lines += ["", out["more"]]
    return "\n".join(lines)
