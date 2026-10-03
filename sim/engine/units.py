"""The unit registry and the one conversion path every display goes through.

Units are data (data/world/units.json, plus data/world/units.json in a mod,
named `<mod_id>:<name>`). Each dimension has one base unit; a unit converts to
it as `base = value * factor + offset`. The engine keeps its own numbers as
they are; this layer only converts what a player reads, following the player's
preference per dimension (a unit id, or nothing for "as the game writes it").
"""
import json
import os
import re
from typing import Any, Dict, List, Mapping, Optional, Tuple

from .mods import get_ordered_mods
from .mods_base import ModError
from .mods_ids import check_new_id
from .tree_source import ROOT

Registry = Dict[str, Any]

# What the player chose, per dimension; set from the saved options by the
# front end. Empty means every field is shown exactly as written.
PREFERENCES: Dict[str, str] = {}
_registry_override: Optional[Registry] = None
_default_registry: Optional[Registry] = None


def _read(path: str) -> Dict[str, Any]:
    with open(path, encoding="utf-8") as source:
        return json.load(source)


def load_units(root: str = ROOT, mods_dir: Optional[str] = None) -> Registry:
    """The registry from the base file and every mod's unit file."""
    mods_dir = mods_dir or os.path.join(root, "mods")
    registry = _read(os.path.join(root, "data", "world", "units.json"))
    registry.setdefault("field_rules", [])
    for manifest in get_ordered_mods(mods_dir):
        path = os.path.join(manifest.directory, "data", "world", "units.json")
        if not os.path.isfile(path):
            continue
        extra = _read(path)
        for unit_id, spec in (extra.get("units") or {}).items():
            check_new_id(manifest, unit_id, False, path)
            if unit_id in registry["units"]:
                raise ModError("unit %s of %s is already defined" % (unit_id, path))
            registry["units"][unit_id] = spec
        registry["field_rules"] += extra.get("field_rules") or []
    check_registry(registry)
    return registry


def check_registry(registry: Registry) -> None:
    for unit_id, spec in registry["units"].items():
        if spec.get("dimension") not in registry["dimensions"]:
            raise ModError("unit %s names an unknown dimension" % unit_id)
        if "factor" not in spec and "factor_from" not in spec:
            raise ModError("unit %s needs a factor" % unit_id)
    for rule in registry["field_rules"]:
        if registry["units"].get(rule.get("native"), {}).get("dimension") != rule.get("dimension"):
            raise ModError("field rule %r has a native unit of another dimension" % rule.get("pattern"))


def registry() -> Registry:
    global _default_registry
    if _registry_override is not None:
        return _registry_override
    if _default_registry is None:
        _default_registry = load_units()
    return _default_registry


def set_registry(replacement: Optional[Registry]) -> None:
    """Use another registry (tests, a game with extra mods); None restores the default."""
    global _registry_override, _default_registry
    _registry_override = replacement
    if replacement is None:
        _default_registry = None


def set_preferences(chosen: Optional[Mapping[str, str]]) -> None:
    PREFERENCES.clear()
    PREFERENCES.update(chosen or {})


def unit_context(sim: Any) -> Dict[str, float]:
    """The per-game numbers some units need; none for no game."""
    if sim is None:
        return {}
    return {"hours_per_coin": 1.0 / sim.labour.money_per_labour_hour()}


def unit_factor(spec: Mapping[str, Any], context: Mapping[str, float]) -> float:
    if "factor_from" in spec:
        return float(context[spec["factor_from"]])
    return float(spec["factor"])


def to_base(reg: Registry, unit_id: str, value: float, context: Mapping[str, float]) -> float:
    spec = reg["units"][unit_id]
    return value * unit_factor(spec, context) + float(spec.get("offset", 0.0))


def from_base(reg: Registry, unit_id: str, value: float, context: Mapping[str, float]) -> float:
    spec = reg["units"][unit_id]
    return (value - float(spec.get("offset", 0.0))) / unit_factor(spec, context)


def unit_label(spec: Mapping[str, Any], civ: Optional[Mapping[str, Any]]) -> Tuple[str, str]:
    """(name, symbol) of a unit; a currency unit reads the civilisation's words."""
    if spec.get("label_from") == "civ_currency":
        from .data import money_short, money_word
        return money_word(civ), money_short(civ)
    return spec["name"], spec["symbol"]


def field_rule(reg: Registry, field: str) -> Optional[Dict[str, Any]]:
    for rule in reg["field_rules"]:
        if re.search(rule["pattern"], field):
            return rule
    return None


def native_factor(reg: Registry, rule: Mapping[str, Any], sim: Any) -> float:
    """Base units per native unit of a field rule (the scale; offsets aside)."""
    return unit_factor(reg["units"][rule["native"]], unit_context(sim))


def available_units(reg: Registry, dimension: str, civ_id: Optional[str]) -> List[str]:
    return [unit_id for unit_id, spec in reg["units"].items()
            if spec["dimension"] == dimension
            and (not spec.get("civilisations") or civ_id in spec["civilisations"])]


def _format(dimension: str, base_value: float, sim: Any, preference: Optional[str]) -> Optional[Tuple[float, str, str]]:
    chosen = (PREFERENCES if preference is None else {dimension: preference}).get(dimension)
    reg = registry()
    if not chosen or chosen not in reg["units"]:
        return None
    civ = getattr(sim, "civ", None)
    name, symbol = unit_label(reg["units"][chosen], civ)
    return from_base(reg, chosen, base_value, unit_context(sim)), name, symbol


def format_area(hectares: float, sim: Any = None, preference: Optional[str] = None):
    """(converted value, unit name, symbol) for a base-unit area, or None to show it as written."""
    return _format("area", hectares, sim, preference)


def format_mass(kilograms: float, sim: Any = None, preference: Optional[str] = None):
    return _format("mass", kilograms, sim, preference)


def format_temperature(celsius: float, sim: Any = None, preference: Optional[str] = None):
    return _format("temperature", celsius, sim, preference)


def format_money(labour_hours: float, sim: Any = None, preference: Optional[str] = None):
    return _format("money", labour_hours, sim, preference)


_FORMATTERS = {"area": format_area, "mass": format_mass,
               "temperature": format_temperature, "money": format_money}


def format_field(rule: Mapping[str, Any], value: float, sim: Any):
    """A reply field's value as the player's chosen unit shows it, or None."""
    reg = registry()
    chosen = PREFERENCES.get(rule["dimension"])
    if not chosen or chosen == rule["native"] or chosen not in reg["units"]:
        return None
    base = to_base(reg, rule["native"], value, unit_context(sim))
    return _FORMATTERS[rule["dimension"]](base, sim)


def add_display(reply: Any, sim: Any) -> Any:
    """A copy of a reply with `<field>_display` beside every quantity whose
    dimension has a chosen unit: {"value", "unit", "symbol"}. The base-unit
    field is never changed. No preference chosen: the reply is returned as is."""
    if not PREFERENCES:
        return reply
    reg = registry()

    def walk(node):
        if isinstance(node, list):
            return [walk(item) for item in node]
        if not isinstance(node, dict):
            return node
        out = {}
        for key, value in node.items():
            out[key] = walk(value) if isinstance(value, (dict, list)) else value
            if (isinstance(value, (int, float)) and not isinstance(value, bool)
                    and not key.endswith("_display")):
                rule = field_rule(reg, key)
                shown = format_field(rule, value, sim) if rule else None
                if shown is not None:
                    out[key + "_display"] = {"value": round(shown[0], 4), "unit": shown[1],
                                             "symbol": shown[2]}
        return out
    return walk(reply)
