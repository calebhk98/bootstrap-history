"""A commodity pool's stock is held under the material keys of its forms (bar, ore, ...) and, for a pool that names no form,
under the pool's own id. These are plain functions of the ledger's dict and the commodity records."""
from typing import Any, Dict, List, Mapping, MutableMapping


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
	"""The key a pool's mine flow is held under: the form its mines raise, else the pool's id."""
	return (commodities.get(commodity) or {}).get("raised_material") or commodity


def change_tonnes(stock: MutableMapping[str, float], opening: MutableMapping[str, float], key: str, tonnes: float,
                  other_keys: List[str]) -> None:
	"""`tonnes` added to (or, negative, taken from) the stock under `key`. A taking beyond what `key` holds is met from
	`other_keys` in order (the rest of the pool); only what none holds is left owing on `key`."""
	if tonnes < 0.0:
		owed = -tonnes
		for each in [key] + other_keys:
			taken = min(owed, max(0.0, stock.get(each, 0.0)))
			if taken > 0.0:
				_add(stock, opening, each, -taken)
				owed -= taken
		tonnes = -owed
	if tonnes != 0.0:
		_add(stock, opening, key, tonnes)


def bank_pool_total(stock: MutableMapping[str, float], commodity: str, commodities: Mapping[str, Mapping[str, Any]],
                    total: float) -> None:
	"""The pool's tonnes become `total`: a rise is held in the form the pool's mines raise, a fall comes off that form first and
	then the rest of the pool. A commodity naming no forms is simply set."""
	if not (commodities.get(commodity) or {}).get("material_keys"):
		stock[commodity] = total
		return
	change = total - pool_total(stock, commodity, commodities)
	target = raised_key(commodity, commodities)
	change_tonnes(stock, {}, target, change, [key for key in pool_keys(commodity, commodities) if key != target])


def _add(stock: MutableMapping[str, float], opening: MutableMapping[str, float], key: str, tonnes: float) -> None:
	stock[key] = stock.get(key, 0.0) + tonnes
	opening[key] = opening.get(key, 0.0) + tonnes
