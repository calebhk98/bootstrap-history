"""Naming a project in a note: an exact id or name, never one fog hides."""
from .nodes import _did_you_mean, _norm_name, names_for

MAX_NAME_WORDS = 8


def candidates(sim, text):
    """Visible node ids whose id or full name is exactly `text`, case and punctuation folded."""
    found = []
    names = names_for(sim.view("mods_directory")())
    by_id = names.ids_lower.get(str(text).strip().lower())
    if by_id:
        found.append(by_id)
    for node_id in names.by_name.get(_norm_name(text), ()):
        if node_id not in found:
            found.append(node_id)
    return [node_id for node_id in found
            if node_id in sim.view("tree_nodes")() and (not sim.view("fog_of_war")() or sim.view("visibility")(node_id))]


def resolve_project(sim, text):
    """(node_id, None) for one match, (None, error) otherwise. The error never names a hidden node."""
    found = candidates(sim, text)
    if len(found) == 1:
        return found[0], None
    if found:
        return None, "%r names several projects (%s); use the id" % (text, ", ".join(sorted(found)))
    near = [node_id for node_id in _did_you_mean(text, sim.view("tree_nodes")(), sim=sim)
            if not sim.view("fog_of_war")() or sim.view("visibility")(node_id)]
    return None, "no project called %r that you know of%s" % (
        text, ". did you mean: " + ", ".join(near) if near else "")


def split_leading_project(sim, words):
    """(node_id, text) when the words open with a project and leave some text after it, else (None, text).

    A leading `--` marks plain text that only looks like a project name."""
    if words and words[0] == "--":
        return None, " ".join(words[1:])
    for length in range(min(len(words) - 1, MAX_NAME_WORDS), 0, -1):
        found = candidates(sim, " ".join(words[:length]))
        if len(found) == 1:
            return found[0], " ".join(words[length:])
    return None, " ".join(words)
