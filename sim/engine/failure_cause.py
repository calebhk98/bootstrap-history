"""One sentence on what failed when a project fails, from the node's own fields."""

_LEAD_BY_KIND = {
    "SCIENCE": "the explanation did not hold up under trial, or was not taught well enough to be adopted",
    "INSTITUTION": "the organisation did not hold together: its rules and people were not accepted or staffed to work",
    "CAPABILITY": "the capability did not reach the standard the work needs",
    "ENGINEERING": "the apparatus or process failed in trial",
    "INFRASTRUCTURE": "the works failed in trial",
    "RESOURCE": "the extraction or supply failed in trial",
}


def _words(identifier):
    return identifier.rsplit("_", 1)[0].replace("_", " ") if identifier.count("_") else identifier


def failure_cause(sim, node_id):
    """What failed, drawn from the node's kind, materials, trades and the
    state's attitude to its traits."""
    node = sim.nodes[node_id]
    parts = [_LEAD_BY_KIND.get(node.get("kind"), "the attempt did not come together")]
    if node["mat"]:
        parts.append("materials spoiled (%s)" % ", ".join(_words(name) for name in sorted(node["mat"])[:3]))
    if node["lab"]:
        parts.append("trades whose work was wasted (%s)" % ", ".join(sorted(node["lab"])[:3]))
    if not node["mat"] and not node["lab"]:
        parts.append("nothing physical was lost; this is teaching and adoption, not apparatus")
    if sim.state_interest(node) < 0:
        parts.append("official opposition made it harder")
    return "; ".join(parts)
