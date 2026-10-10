"""The unit registry and the one conversion path every display goes through.

Units are data (data/world/units.json, plus data/world/units.json in a mod,
named `<mod_id>:<name>`). Each dimension has one base unit; a unit converts to
it as `base = value * factor + offset`. The engine keeps its own numbers as
they are; this layer only converts what a player reads, following the player's
preference per dimension (a unit id, or nothing for "as the game writes it").
"""
import os
import re
from typing import Any, Dict, List, Mapping, Optional, Tuple

from sim.json_files import read_json

from .mods import get_ordered_mods
from .mods_base import ModError
from .mods_ids import check_new_id
from .tree_source import ROOT

Registry = Dict[str, Any]

# What the player chose, per dimension; set from the saved options by the
# front end. Empty means every field is shown exactly as written.
PREFERENCES: Dict[str, str] = {}
# What the civilisation's own data names as its display units; used for any dimension the player left unchosen.
CIV_DEFAULTS: Dict[str, str] = {}
_registry_override: Optional[Registry] = None
_default_registry: Optional[Registry] = None


def load_units(root: str = ROOT, mods_dir: Optional[str] = None) -> Registry:
    """The registry from the base file and every mod's unit file."""
    mods_dir = mods_dir or os.path.join(root, "mods")
    registry = read_json(os.path.join(root, "data", "world", "units.json"))
    registry.setdefault("field_rules", [])
    registry.setdefault("quantity_words", "$^")
    registry.setdefault("not_quantities", "$^")
    for manifest in get_ordered_mods(mods_dir):
        path = os.path.join(manifest.directory, "data", "world", "units.json")
        if not os.path.isfile(path):
            continue
        extra = read_json(path)
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
        if rule.get("per_dimension") and (registry["units"].get(rule.get("per_native"), {}).get("dimension")
                                          != rule["per_dimension"]):
            raise ModError("field rule %r has a per unit of another dimension" % rule.get("pattern"))


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


def set_civ_defaults(civ: Optional[Mapping[str, Any]]) -> None:
    """Take the display units a civilisation's data names (`display_units`: {dimension: unit id}); none for no civilisation."""
    CIV_DEFAULTS.clear()
    CIV_DEFAULTS.update((civ or {}).get("display_units") or {})


def chosen_units() -> Dict[str, str]:
    """The unit shown per dimension: the player's choice, else the civilisation's own."""
    return {**CIV_DEFAULTS, **PREFERENCES}


def check_civ_units(reg: Registry, civ_id: str, civ: Mapping[str, Any]) -> List[str]:
    """Problems with the `display_units` a civilisation file names."""
    problems = []
    for dimension, unit_id in ((civ.get("display_units") or {}).items()):
        spec = reg["units"].get(unit_id)
        if spec is None or spec["dimension"] != dimension:
            problems.append("%s: display_units %s=%s is not a %s unit in the registry" % (civ_id, dimension, unit_id, dimension))
        elif spec.get("civilisations") and civ_id not in spec["civilisations"]:
            problems.append("%s: display unit %s is not listed for this civilisation" % (civ_id, unit_id))
    return problems


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


def field_rule(reg: Registry, field: str, parent: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """The first rule matching a field name; a rule with `within` matches only inside a field whose name fits it."""
    for rule in reg["field_rules"]:
        if re.search(rule["pattern"], field) and (
                not rule.get("within") or (parent is not None and re.search(rule["within"], parent))):
            return rule
    return None


def tagged(reply: Dict[str, Any], **fields: str) -> Dict[str, Any]:
    """Declare, where a reply is built, the dimension and native unit of fields no name rule covers:
    `tagged(reply, hull_cargo="mass:tonne")`; a price per another dimension is `"money:civ_coin/area:hectare"`. The tag
    travels in the reply's `field_units`, which also tells a script the unit."""
    if fields:
        reply.setdefault("field_units", {}).update(fields)
    return reply


def rule_for(reg: Registry, node: Mapping[str, Any], field: str, parent: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """The rule for one field of a reply: the producer's own `field_units` tag first, then the name rules."""
    tag = (node.get("field_units") or {}).get(field) if isinstance(node.get("field_units"), dict) else None
    if tag:
        quantity, _, per = str(tag).partition("/")
        dimension, _, native = quantity.partition(":")
        rule = {"dimension": dimension, "native": native}
        if per:
            rule["per_dimension"], _, rule["per_native"] = per.partition(":")
        if (reg["units"].get(native, {}).get("dimension") == dimension
                and (not per or reg["units"].get(rule["per_native"], {}).get("dimension") == rule["per_dimension"])):
            return rule
    return field_rule(reg, field, parent)


def looks_like_quantity(reg: Registry, field: str) -> bool:
    """Whether a reply field's name reads like a mass, area or sum of money (the registry's `quantity_words`, less its `not_quantities`)."""
    return bool(re.search(reg["quantity_words"], field)) and not re.search(reg["not_quantities"], field)


def known_field(reg: Registry, field: str) -> bool:
    """Whether some field rule covers this name, whatever field it sits inside."""
    return any(re.search(rule["pattern"], field) for rule in reg["field_rules"])


def native_factor(reg: Registry, rule: Mapping[str, Any], sim: Any) -> float:
    """Base units per native unit of a field rule (the scale; offsets aside)."""
    return unit_factor(reg["units"][rule["native"]], unit_context(sim))


def available_units(reg: Registry, dimension: str, civ_id: Optional[str]) -> List[str]:
    return [unit_id for unit_id, spec in reg["units"].items()
            if spec["dimension"] == dimension
            and (not spec.get("civilisations") or civ_id in spec["civilisations"])]


def _format(dimension: str, base_value: float, sim: Any, preference: Optional[str]) -> Optional[Tuple[float, str, str]]:
    chosen = (chosen_units() if preference is None else {dimension: preference}).get(dimension)
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


def _format_compound(rule: Mapping[str, Any], value: float, sim: Any):
    """(value, name, symbol) of a quantity per another dimension (money per mass), each part in its chosen unit."""
    reg = registry()
    context = unit_context(sim)
    civ = getattr(sim, "civ", None)
    parts = []
    for dimension, native in ((rule["dimension"], rule["native"]), (rule["per_dimension"], rule["per_native"])):
        chosen = chosen_units().get(dimension)
        if not chosen or chosen not in reg["units"] or chosen == native:
            parts.append((native, 1.0))
        else:
            parts.append((chosen, unit_factor(reg["units"][native], context) / unit_factor(reg["units"][chosen], context)))
    if parts[0][0] == rule["native"] and parts[1][0] == rule["per_native"]:
        return None
    labels = [unit_label(reg["units"][chosen], civ) for chosen, _ in parts]
    return (value * parts[0][1] / parts[1][1], "%s per %s" % (labels[0][0], labels[1][0]),
            "%s/%s" % (labels[0][1], labels[1][1]))


def format_field(rule: Mapping[str, Any], value: float, sim: Any):
    """A reply field's value as the player's chosen unit shows it, or None."""
    reg = registry()
    if rule.get("per_dimension"):
        return _format_compound(rule, value, sim)
    chosen = chosen_units().get(rule["dimension"])
    if not chosen or chosen == rule["native"] or chosen not in reg["units"]:
        return None
    base = to_base(reg, rule["native"], value, unit_context(sim))
    return _FORMATTERS[rule["dimension"]](base, sim)


def add_display(reply: Any, sim: Any) -> Any:
    """A copy of a reply with `<field>_display` beside every quantity whose
    dimension has a chosen unit: {"value", "unit", "symbol"}. The base-unit
    field is never changed. No preference chosen: the reply is returned as is."""
    if not chosen_units():
        return reply
    reg = registry()

    def walk(node, parent=None):
        if isinstance(node, list):
            return [walk(item, parent) for item in node]
        if not isinstance(node, dict):
            return node
        out = {}
        for key, value in node.items():
            out[key] = walk(value, key) if isinstance(value, (dict, list)) else value
            if (isinstance(value, (int, float)) and not isinstance(value, bool)
                    and not key.endswith("_display")):
                rule = rule_for(reg, node, key, parent)
                shown = format_field(rule, value, sim) if rule else None
                if shown is not None:
                    out[key + "_display"] = {"value": round(shown[0], 4), "unit": shown[1],
                                             "symbol": shown[2]}
        return out
    return walk(reply)


def find_unit(reg: Registry, text: str, dimension: Optional[str] = None, civ_id: Optional[str] = None) -> Optional[str]:
    """The unit id a player word names (id, name, plural or symbol), or None. With a civilisation id, units limited to other civilisations are not found."""
    word = str(text or "").strip().lower()
    if not word:
        return None
    for unit_id, spec in reg["units"].items():
        if dimension and spec["dimension"] != dimension:
            continue
        if civ_id is not None and spec.get("civilisations") and civ_id not in spec["civilisations"]:
            continue
        names = {unit_id.lower(), spec["name"].lower(), str(spec.get("plural", "")).lower(), spec["symbol"].lower()}
        if word in names or word.replace(" ", "_") in names or (word.endswith("s") and word[:-1] in names):
            return unit_id
    return None


def convert_between(reg: Registry, value: float, from_unit: str, to_unit: str, context: Mapping[str, float]) -> float:
    """A value in one unit of a dimension expressed in another."""
    return from_base(reg, to_unit, to_base(reg, from_unit, value, context), context)
