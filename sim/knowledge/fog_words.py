"""The words fog lets a player read: hidden node ids replaced, one-sentence summaries, prerequisite sentences.

Pure functions of the tree and of a visibility test passed in; the module decides what is visible."""
import re
from typing import Any, Callable, Dict, List, Mapping, Optional, Set

# What a node id the player has not heard of is replaced with.
HIDDEN_ID_PLACEHOLDER = "something you have not heard of"

# Plain words for a node's kind, so a hidden blocker keeps its identity but shows what sort of thing it is.
FOG_KIND_HINTS = {
    "ENGINEERING": "a technique or device", "SCIENCE": "an idea or body of theory",
    "INSTITUTION": "an institution or social arrangement", "RESOURCE": "a material or its source",
    "INFRASTRUCTURE": "a built facility", "CAPABILITY": "a measurement or power capability",
}
# A hidden prerequisite shows its kind only when this share of its own prerequisites is already done.
FOG_HINT_NEARNESS = 0.5
# Capability nodes (cap_measure_*, cap_power_*) cost nothing, take no time. A refusal naming one must say it is free
# and startable now, not just the name.
FREE_PREREQ_NAMED_AT_MOST = 3

# Removes sentences where a node grades itself against the rest of the tree.
# Matches exact phrases like "pivot", "highest-value", "costs more than any
# single technology", or meta-ranking patterns (mentioning "game"/"tree" + ranking
# words). [temporary_heuristic]
_SELF_PLAY_PHRASES = (
    "pivot of the entire game",
    "costs more than any single",
    "highest expected-value node in the tree",
    "highest expected-value defensive investment",
    "highest-leverage thing you can spend money on",
    "is simply the highest-leverage",
    "largest single call on your personal hours",
    "must not cut",
    # Imperative phrases that say what to build first (same offence as ranking)
    "do this before writing any other recipe down",
    "build it first, use it to learn",
)
_SELF_PLAY_META = re.compile(
    r"\b(the game|this game|the entire game|the tree|this tree)\b", re.I)
_SELF_PLAY_RANK = re.compile(
    r"\bhighest\b|\blargest\b|\bpivot\b|\bmost important\b|\bsingle most\b", re.I)


def prerequisite_label(nodes: Mapping[str, Any], prereq_id: str) -> str:
    """The id with the node's name beside it, so the id is identifiable."""
    name = nodes.get(prereq_id, {}).get("name")
    return "%s (%s)" % (prereq_id, name) if name and name != prereq_id else prereq_id


def prerequisite_names(nodes: Mapping[str, Any], prerequisite_ids) -> Dict[str, str]:
    """{id: name} for each prerequisite the tree knows, in the words of the civilisation the nodes were built for."""
    return {prereq_id: nodes[prereq_id]["name"] for prereq_id in prerequisite_ids if prereq_id in nodes}


def strip_self_play_advice(text: Optional[str]) -> Optional[str]:
    """Drop any sentence that ranks a node against the game or the tree, and hand back what is left."""
    if not text:
        return text
    parts = re.split(r'(?<=[.!?]) ', text)

    def is_self_play(sentence: str) -> bool:
        low = sentence.lower()
        if any(phrase in low for phrase in _SELF_PLAY_PHRASES):
            return True
        return bool(_SELF_PLAY_META.search(sentence) and _SELF_PLAY_RANK.search(sentence))

    return " ".join(sentence for sentence in parts if not is_self_play(sentence)).strip()


def scrub_hidden_ids(text: str, node_ids: Any, is_visible: Callable[[str], bool]) -> str:
    """Replace every whole node id the player cannot see; longest ids first."""
    scrubbed = text
    for node_id in sorted(node_ids, key=lambda candidate: -len(candidate)):
        if not is_visible(node_id):
            # Whole ids only; ':' joins a namespaced id, so it is not a boundary either
            pattern = r'(?<![\w:])' + re.escape(node_id) + r'(?![\w:])'
            scrubbed = re.sub(pattern, HIDDEN_ID_PLACEHOLDER, scrubbed)
    return scrubbed


def summary_sentence(node: Mapping[str, Any]) -> str:
    """One sentence of a node's note, never the unlocks; its name when the note says nothing fit to show. The
    self-ranking sentences go before the first is taken (a note can open with one)."""
    note = strip_self_play_advice((node.get("note") or "").strip())
    if not note:
        return node["name"]
    for separator in (". ", "? ", "! "):
        if separator in note:
            note = note.split(separator)[0].strip() + "."
            break
    # A "one sentence" summary that runs long, times thirty entries in a list, is most of the reply.
    return note if len(note) <= 110 else note[:107].rstrip(" ,;") + "..."


def hidden_prerequisite_kinds(nodes: Mapping[str, Any], hidden_ids: List[str], done: Set[str]) -> List[str]:
    """Kind phrases for hidden prerequisites the player has built enough nearby knowledge to place."""
    kinds: List[str] = []
    for node_id in hidden_ids:
        node = nodes.get(node_id) or {}
        prereqs = node.get("pre") or []
        near = (sum(1 for prereq_id in prereqs if prereq_id in done) / len(prereqs) >= FOG_HINT_NEARNESS
                if prereqs else True)
        phrase = FOG_KIND_HINTS.get(node.get("kind"))
        if near and phrase and phrase not in kinds:
            kinds.append(phrase)
    return kinds


def free_prereq_hint(nodes: Mapping[str, Any], missing: List[str], done: Set[str]) -> str:
    """", and X costs nothing..." for whichever missing prerequisites are free, instant and startable right now - or
    "" when none are. A free node that is itself blocked is not named: that would be a second refusal."""
    ready: List[str] = []
    for node_id in missing:
        node = nodes.get(node_id)
        if not node:
            continue
        if ((node.get("_total_cost") or 0) > 1 or (node.get("ph") or 0) > 0
                or (node.get("yrs") or 0) > 0 or (node.get("risk") or 0) > 0):
            continue
        if all(prereq_id in done for prereq_id in node["pre"]):
            ready.append(node_id)
    if not ready:
        return ""
    ready = ready[:FREE_PREREQ_NAMED_AT_MOST]
    if len(ready) == 1:
        return (". %s costs nothing, takes no time and cannot fail: "
                "start %s" % (ready[0], ready[0]))
    return (". %s cost nothing, take no time and cannot fail: start "
            "them now (%s)"
            % (", ".join(ready), ", ".join("start " + node_id for node_id in ready)))


def missing_prereq_message(nodes: Mapping[str, Any], missing: List[str], is_visible: Callable[[str], bool],
                           fog: bool, done: Set[str]) -> Optional[str]:
    """One player-facing sentence for a list of not-yet-done prerequisite ids, filtered through the same visibility test
    every refusal applies. There must be exactly one way to turn "missing" into words: a second caller printing the
    raw ids is how hidden prerequisites leaked before. None for an empty list."""
    if not missing:
        return None
    known = [prereq_id for prereq_id in missing if is_visible(prereq_id)]
    hidden = len(missing) - len(known)
    if not fog or not hidden:
        message = "missing prerequisites: " + ", ".join(prerequisite_label(nodes, prereq_id) for prereq_id in missing)
        return message + free_prereq_hint(nodes, missing, done)
    bits = []
    if known:
        bits.append("missing prerequisites: " + ", ".join(prerequisite_label(nodes, prereq_id) for prereq_id in known))
    hidden_kinds = hidden_prerequisite_kinds(nodes, [prereq_id for prereq_id in missing if prereq_id not in known], done)
    bits.append("%d other thing%s you have not heard of yet%s"
                % (hidden, "" if hidden == 1 else "s",
                   " (%s)" % ", ".join(hidden_kinds) if hidden_kinds else ""))
    message = "; and ".join(bits) if known else \
        ("this needs %s, and you do not yet know what %s"
         % (bits[-1], "they are" if hidden > 1 else "it is"))
    # Only the visible ones: a hidden prerequisite is never named by the hint either.
    return message + free_prereq_hint(nodes, known, done)
