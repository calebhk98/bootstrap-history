"""A commodity pool's stock is held under the material keys of its forms (bar, ore, ...) and, for a pool that names no form,
under the pool's own id. These are plain functions of the ledger's dict and the commodity records."""
from typing import Any, Dict, List, Mapping, MutableMapping

_TOLERANCE_TONNES = 1e-9     # float noise in a taking cut to the stock held


def pool_keys(commodity: str, commodities: Mapping[str, Mapping[str, Any]]) -> List[str]:
	"""The keys a pool's tonnes can sit under, sorted: its material keys, then its own id when that is not one of them."""
	keys = sorted(set((commodities.get(commodity) or {}).get("material_keys", ())) - {commodity})
	return keys + [commodity]


def pool_total(stock: Mapping[str, float], commodity: str, commodities: Mapping[str, Mapping[str, Any]]) -> float:
	"""Tonnes of the pool held in any form: the sum of its material keys plus anything held under the pool id."""
	return sum(stock.get(key, 0.0) for key in pool_keys(commodity, commodities))


def held_by_form(stock: Mapping[str, float], commodity: str, commodities: Mapping[str, Mapping[str, Any]]) -> Dict[str, float]:
	"""{key: tonnes} of the pool's keys the stock holds, in key order."""
	return {key: stock[key] for key in pool_keys(commodity, commodities) if key in stock}


def form_key(material: str, commodity: str, commodities: Mapping[str, Mapping[str, Any]]) -> str:
	"""The key a tonne of `material` is held under: itself where it is one of the pool's material keys, else the pool's id."""
	return material if material in (commodities.get(commodity) or {}).get("material_keys", ()) else commodity


def raised_key(commodity: str, commodities: Mapping[str, Mapping[str, Any]]) -> str:
	"""The key a pool's mine flow is held under: the form its mines raise; a pool with no distinct raised form raises the
	material it is priced as, when that is one of its forms; else the pool's id."""
	record = commodities.get(commodity) or {}
	if record.get("raised_material"):
		return record["raised_material"]
	if record.get("price_material") in record.get("material_keys", ()):
		return record["price_material"]
	return commodity


def held_enough(stock: Mapping[str, float], key: str, tonnes: float) -> bool:
	"""True when a taking of `tonnes` (negative) leaves the stock under `key` at or above zero; any addition is allowed."""
	return tonnes >= 0.0 or stock.get(key, 0.0) + tonnes >= -_TOLERANCE_TONNES


def change_tonnes(stock: MutableMapping[str, float], opening: MutableMapping[str, float], key: str, tonnes: float) -> None:
	"""`tonnes` added to (or, negative, taken from) the stock under exactly `key`; no other form of the pool is touched."""
	_add(stock, opening, key, tonnes)


def bank_tonnes(stock: MutableMapping[str, float], key: str, tonnes: float) -> None:
	"""The tonnes held under exactly `key` become `tonnes`."""
	stock[key] = tonnes


def _add(stock: MutableMapping[str, float], opening: MutableMapping[str, float], key: str, tonnes: float) -> None:
	stock[key] = stock.get(key, 0.0) + tonnes
	opening[key] = opening.get(key, 0.0) + tonnes
