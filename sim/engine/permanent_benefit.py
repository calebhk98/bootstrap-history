"""What a finished work gives for good, open or shut, read from its mechanics and effects."""
# Mechanics the engine reads through `has` (built is enough), not `running`.
_HELD_MECHANICS = {
    "corpus": "a hedge against losing knowledge in a sack (holds while it is shut)",
    "disease_burden": "a lower disease burden",
}

_EFFECT_WORDS = {
    "literacy_general": "general literacy",
    "literacy_elite": "elite literacy",
    "state_capacity": "state capacity",
    "population": "a lower disease burden, so more people survive",
}


def permanent_parts(node, effects):
    mechanics = node.get("mechanics") or {}
    # a work that serves a share of the people lowers the disease burden only for the share its open doors reach
    serves_a_share = "coverage" in mechanics
    parts = []
    for name, spec in mechanics.items():
        if name == "disease_burden" and serves_a_share:
            continue
        if name in _HELD_MECHANICS:
            parts.append(_HELD_MECHANICS[name])
        elif isinstance(spec, dict) and spec.get("gate") == "has":
            parts.append(name.replace("_", " "))
    for field, delta in effects.items():
        if field == "population" and serves_a_share:
            continue
        if not field.startswith("_") and isinstance(delta, (int, float)):
            parts.append(_EFFECT_WORDS.get(field, field.replace("_", " ")))
    return list(dict.fromkeys(parts))
