"""Conversion between units of a registry, and the words of a civilisation's coin: plain functions of their inputs."""
from typing import Any, Mapping, Optional, Tuple


def money_word(civilisation: Optional[Mapping[str, Any]]) -> str:
	civilisation = civilisation or {}
	return (civilisation.get("currency_words") or {}).get("long") or civilisation.get("currency") or "denarii"


def money_short(civilisation: Optional[Mapping[str, Any]]) -> str:
	"""The abbreviation used in compact lines: "400 den", "net +12 den/yr"."""
	civilisation = civilisation or {}
	return (civilisation.get("currency_words") or {}).get("short") or civilisation.get("currency") or "den"


def unit_factor(spec: Mapping[str, Any], context: Mapping[str, float]) -> float:
	if "factor_from" in spec:
		return float(context[spec["factor_from"]])
	return float(spec["factor"])


def to_base(registry: Mapping[str, Any], unit_id: str, value: float, context: Mapping[str, float]) -> float:
	spec = registry["units"][unit_id]
	return value * unit_factor(spec, context) + float(spec.get("offset", 0.0))


def from_base(registry: Mapping[str, Any], unit_id: str, value: float, context: Mapping[str, float]) -> float:
	spec = registry["units"][unit_id]
	return (value - float(spec.get("offset", 0.0))) / unit_factor(spec, context)


def unit_label(spec: Mapping[str, Any], civilisation: Optional[Mapping[str, Any]]) -> Tuple[str, str]:
	"""(name, symbol) of a unit; a currency unit reads the civilisation's words."""
	if spec.get("label_from") == "civ_currency":
		return money_word(civilisation), money_short(civilisation)
	return spec["name"], spec["symbol"]
