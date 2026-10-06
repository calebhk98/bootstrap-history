"""Complaint 276: a req_any option naming a material that has its own resource
node (mat_<name>) must name that node, not a bare commodity id the engine would
price as a discounted purchase."""

QUICK_TOPIC = True

from .harness import *  # noqa: F401,F403

bare_options = []
for node_id, node_record in NODES.items():
    for group in node_record.get("req_any") or []:
        for option_id in group.get("options") or {}:
            if (option_id not in NODES and option_id not in GOODS
                    and option_id not in (node_record.get("mat") or {})
                    and ("mat_" + option_id) in NODES):
                bare_options.append((node_id, option_id))
check("no option is a bare id that has a mat_ resource node of its own",
      not bare_options, bare_options)
