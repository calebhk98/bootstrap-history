"""Things an actor will not do: the entries of a persistent exclusion list the automatic starters honour.

An entry is a node id, `category:<category>` or `trait:<trait>`."""
from typing import Any, Collection, Mapping, Optional

CATEGORY_PREFIX = "category:"
TRAIT_PREFIX = "trait:"


def entry_known(entry: str, nodes: Mapping[str, Any]) -> bool:
	"""Whether an exclusion entry names a node, a category or a trait that exists in the tree `nodes`."""
	if entry.startswith(CATEGORY_PREFIX):
		return any(node.get("cat") == entry[len(CATEGORY_PREFIX):] for node in nodes.values())
	if entry.startswith(TRAIT_PREFIX):
		return any(entry[len(TRAIT_PREFIX):] in node.get("traits", ()) for node in nodes.values())
	return entry in nodes


def reason(excluded: Collection[str], node_id: str, nodes: Mapping[str, Any]) -> Optional[str]:
	"""Why the actor excluded this node, in words, or None when it is not excluded."""
	if not excluded:
		return None
	node = nodes.get(node_id, {})
	if node_id in excluded:
		return "you excluded it by name"
	category = node.get("cat")
	if CATEGORY_PREFIX + str(category) in excluded:
		return "you excluded the category %s" % category
	for trait in node.get("traits", ()):
		if TRAIT_PREFIX + trait in excluded:
			return "you excluded everything with the trait %s" % trait
	return None
