"""Complaint 377: nodes limited by a measurement declare the instrument that measures it.

Counts the declarations per family (the measured quantity) and checks each one
names an instrument that exists, is a different node, and is not already a
prerequisite (a prerequisite instrument would make the declaration vacuous).
"""
from .harness import *  # noqa: F401,F403
from sim.engine.data import closure

REQUIRED_KEYS = ("instrument", "quantity", "needed", "unit", "needed_words")
declared = {node_id: node["mechanics"]["diagnosis_instrument"]
            for node_id, node in NODES.items()
            if "diagnosis_instrument" in node.get("mechanics", {})}

check("the survey found declarations", len(declared) > 0)
families = {}
for node_id, spec in declared.items():
    families.setdefault(spec["quantity"], []).append(node_id)

for family in ("tolerance", "impurity", "pressure", "temperature uncertainty"):
    check("family %s has several declared nodes" % family,
          len(families.get(family, [])) >= 3, families.get(family))

for node_id, spec in sorted(declared.items()):
    check("%s declares every field" % node_id, all(key in spec for key in REQUIRED_KEYS), spec)
    check("%s names an instrument node that exists" % node_id,
          spec["instrument"] in NODES, spec["instrument"])
    check("%s instrument is not the node itself" % node_id, spec["instrument"] != node_id)
    if spec["instrument"] in NODES:
        check("%s instrument is not already a prerequisite" % node_id,
              spec["instrument"] not in closure(NODES, node_id), spec["instrument"])
    check("%s needs a positive figure" % node_id, spec["needed"] > 0, spec["needed"])
