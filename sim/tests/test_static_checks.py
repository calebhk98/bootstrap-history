"""static_checks: player-facing text (tech node notes) does not contain developer references."""

QUICK_TOPIC = True

import re

from .harness import check

# CHECK: Player-facing tech node notes contain no Complaints/ or file paths.
from sim.engine.tree_source import load_base_tree as _load_base_tree
_tech_data = _load_base_tree()

_bad_nodes = []
for _node in _tech_data.get("nodes", []):
    _node_id = _node.get("id")
    _note = _node.get("note", "")

    if not _note:
        continue

    if "Complaints/" in _note:
        _bad_nodes.append((_node_id, "contains 'Complaints/' reference"))
    elif re.search(r"data/[a-zA-Z_/.-]+\.json", _note):
        _bad_nodes.append((_node_id, "contains file path (.json)"))

check("no tech node notes contain Complaints/ or file paths",
      not _bad_nodes,
      "\n".join(f"{node_id}: {issue}" for node_id, issue in _bad_nodes[:10])
      if _bad_nodes else "clean")
