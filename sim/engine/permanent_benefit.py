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
    parts = []
    for name, spec in (node.get("mechanics") or {}).items():
        if name in _HELD_MECHANICS:
            parts.append(_HELD_MECHANICS[name])
        elif isinstance(spec, dict) and spec.get("gate") == "has":
            parts.append(name.replace("_", " "))
    for field, delta in effects.items():
        if not field.startswith("_") and isinstance(delta, (int, float)):
            parts.append(_EFFECT_WORDS.get(field, field.replace("_", " ")))
    return list(dict.fromkeys(parts))
