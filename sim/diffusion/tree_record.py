"""The tree's record of a node, read through the tree view."""
from typing import Any, Dict


def tree_node(needs: Any, node_id: str) -> Dict[str, Any]:
    """The tree's record of `node_id`; KeyError for an id the tree lacks."""
    node = needs.tree[node_id]
    if node is None:
        raise KeyError(node_id)
    return node
