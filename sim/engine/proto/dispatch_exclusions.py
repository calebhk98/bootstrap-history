"""The exclude and include commands: what rush and the automatic policies must never begin."""

from .command_registry import command
from ..projects_exclusions import CATEGORY_PREFIX, TRAIT_PREFIX


def _listing(sim):
    return sorted(sim.state.projects.excluded)


def _normalise(sim, nodes, entry):
    """The stored form of what the actor typed, or (None, why) when it names nothing known."""
    text = str(entry).strip()
    lowered = text.lower()
    for prefix in (CATEGORY_PREFIX, TRAIT_PREFIX):
        if lowered.startswith(prefix):
            text = prefix + lowered[len(prefix):]
            break
    else:
        if text not in nodes:
            text = next((node_id for node_id in nodes if node_id.lower() == lowered), text)
    if sim.fog and text in nodes and not sim.is_visible(text):
        return None, "no node called %r that you have heard of" % text
    if not sim.exclusion_entry_known(text):
        return None, ("%r names no technology, category or trait. Use a node id, "
                      "category:<category> or trait:<trait>" % text)
    return text, None


@command("exclude", shape="word", group="projects", aliases=("skip",),
         summary="never let rush or the automatic policies begin these",
         usage=["exclude", "exclude <id>", "exclude category:<category>",
                "exclude trait:<trait>", '{"cmd":"exclude","what":"<id>"}'],
         options={"<id>": "a technology",
                  "category:<category>": "every technology in a category",
                  "trait:<trait>": "every technology carrying a trait, e.g. trait:buys_people"},
         description="A standing list, saved with the game. 'rush' and 'rush preview' leave these out "
                     "and say why; auto_open will not open them and auto_commission will not buy "
                     "hands for them. Starting one by hand with 'start' still works. Bare exclude "
                     "lists the entries; 'include' removes one.")
def _cmd_exclude(sim, nodes, cmd, ended):
    what = cmd.get("what") or cmd.get("id")
    if what is None:
        return {"ok": True, "excluded": _listing(sim) or "none"}
    entry, error = _normalise(sim, nodes, what)
    if error:
        return {"ok": False, "error": error}
    sim.state.projects.excluded.add(entry)
    return {"ok": True, "excluded": _listing(sim),
            "note": "%s is excluded: rush, rush preview, auto_open and auto_commission leave it out. "
                    "'include %s' undoes this." % (entry, entry)}


@command("include", shape="word", group="projects", aliases=("unexclude",),
         summary="take something off the exclusion list",
         usage=["include <entry>", "include all"],
         options={"<entry>": "an id, category:<category> or trait:<trait> you excluded",
                  "all": "empty the list"},
         description="The reverse of 'exclude'.")
def _cmd_include(sim, nodes, cmd, ended):
    what = cmd.get("what") or cmd.get("id")
    excluded = sim.state.projects.excluded
    if what is None:
        return {"ok": False, "error": "say what to include, e.g. 'include <id>' or 'include all'"}
    if str(what).strip().lower() == "all":
        excluded.clear()
    else:
        entry, error = _normalise(sim, nodes, what)
        if error or entry not in excluded:
            return {"ok": False, "error": "%s is not on your exclusion list; 'exclude' shows it" % what}
        excluded.discard(entry)
    return {"ok": True, "excluded": _listing(sim) or "none"}
