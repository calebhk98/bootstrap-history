"""Which registry actors hold a patent on a node, kept without scanning every actor for every question.

An actor's patents are a `PatentBook`: a dict that counts each change to which nodes it holds. The index of
node -> holders is rebuilt only after a change (or when the registry replaces an actor or gains one that holds a patent).
"""
from typing import Any, Dict, List

CHANGES = [0]


class PatentBook(dict):
    """node id -> right, counting every change to which nodes are held."""

    def __setitem__(self, node_id, entry):
        CHANGES[0] += 1
        super().__setitem__(node_id, entry)

    def __delitem__(self, node_id):
        CHANGES[0] += 1
        super().__delitem__(node_id)

    def pop(self, *arguments):
        CHANGES[0] += 1
        return super().pop(*arguments)

    def popitem(self):
        CHANGES[0] += 1
        return super().popitem()

    def clear(self):
        CHANGES[0] += 1
        super().clear()

    def update(self, *arguments, **keywords):
        CHANGES[0] += 1
        super().update(*arguments, **keywords)

    def setdefault(self, node_id, default=None):
        CHANGES[0] += 1
        return super().setdefault(node_id, default)

    def __ior__(self, other):
        CHANGES[0] += 1
        return super().__ior__(other)


def track(record: Any, replaces_actor: bool) -> None:
    """Make the record's patents a PatentBook (a record keeps the one it has). An actor that holds nothing, and
    does not stand in for an indexed one, leaves the index as it is."""
    if not isinstance(record.patents, PatentBook):
        record.patents = PatentBook(record.patents)
    if replaces_actor or record.patents:
        CHANGES[0] += 1


def holders_of(registry: Any, node_id: str) -> List[Any]:
    """The registry's actors whose patents name `node_id` (live or expired), in no particular order."""
    stamp = CHANGES[0]
    held = registry.__dict__.get("_patent_index")
    if held is None or held[0] != stamp:
        by_node: Dict[str, List[Any]] = {}
        for actor in registry.actors.values():
            for held_node in actor.record.patents:
                by_node.setdefault(held_node, []).append(actor)
        held = registry.__dict__["_patent_index"] = (stamp, by_node)
    return held[1].get(node_id, [])
