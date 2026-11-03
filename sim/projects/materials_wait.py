"""What a project does with the material orders it placed: wait for the clearing, then charge the bill for what the clearing
bought and order again what it did not. Plain functions on the project's record and the clearing's order results."""
from typing import Any, Dict, List, Mapping, Sequence, Tuple

SHORT_TOLERANCE = 1e-6   # share of an order's tonnes that may stay unbought before it counts as short


def record_orders(record: Dict[str, Any], entries: Sequence[Mapping[str, Any]]) -> None:
    """Put the orders a start made on the project's record: those posted are waited for, those the market refused stay on
    order as unposted entries (ordered again at the next clearing, the cause shown) and are listed in `materials_refused`."""
    if entries:
        set_on_order(record, kept_after_reorder(entries))
    refused = [{"material": entry["material"], "cause": entry["refused"], "text": entry.get("refused_text", "")}
               for entry in entries if entry.get("refused")]
    if refused:
        record["materials_refused"] = refused


def set_on_order(record: Dict[str, Any], posted: Sequence[Mapping[str, Any]]) -> None:
    """The orders the project waits for; `awaiting_materials` is the stock keys they deliver to."""
    record["materials_on_order"] = [dict(entry) for entry in posted]
    record["awaiting_materials"] = sorted({entry["stock_key"] for entry in posted})


def clear_orders(record: Dict[str, Any]) -> None:
    """The project waits for nothing: it was filled."""
    for field in ("materials_on_order", "awaiting_materials", "materials_short", "materials_refused", "held_cause", "years_held_for_materials"):
        record.pop(field, None)


def reconcile(on_order: Sequence[Mapping[str, Any]], results: Sequence[Mapping[str, Any]]) -> Tuple[float, List[Dict[str, Any]]]:
    """(money the bill rises by, the shortfalls) once the clearing has run: the bill fell by the quote of each order, so it rises
    by the quote less what the order's tonnes actually cost the project. A shortfall is {"material", "stock_key", "tonnes",
    "cause"}: the tonnes the order left unbought and why (the refusal's cause, or "unfilled"). Each posted order takes the
    result carrying its own order id, so another order for the same material is never credited to it."""
    add_back, shortfalls, taken = 0.0, [], set()
    for entry in on_order:
        mine = [] if entry.get("unposted") else _own_results(entry, results, taken)
        bought = sum(result.get("bought_tonnes", 0.0) for result in mine)
        paid = sum(result.get("paid", 0.0) for result in mine)
        add_back += entry["quoted"] - paid
        short = entry["tonnes"] - bought
        if short > max(1e-9, SHORT_TOLERANCE * entry["tonnes"]):
            cause = next((result["refused"]["cause"] for result in mine if result.get("refused")), entry.get("cause") or "unfilled")
            shortfalls.append({"material": entry["material"], "stock_key": entry["stock_key"], "tonnes": short, "cause": cause})
    return add_back, shortfalls


def _own_results(entry: Mapping[str, Any], results: Sequence[Mapping[str, Any]], taken: set) -> List[Mapping[str, Any]]:
    """The result carrying `entry`'s order id, marked taken; none when the clearing handled no such order."""
    order_id = entry.get("order_id")
    for position, result in enumerate(results):
        if order_id is not None and result.get("order_id") == order_id and position not in taken:
            taken.add(position)
            return [result]
    return []


def kept_after_reorder(entries: Sequence[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    """The orders a project waits for after a re-order: those posted as they are, those refused kept as unposted entries so the
    next year orders them again."""
    return [{"material": entry["material"], "stock_key": entry["stock_key"], "tonnes": entry["tonnes"], "quoted": 0.0,
             "unposted": True, "cause": entry["refused"]} if entry.get("refused") else dict(entry) for entry in entries]
