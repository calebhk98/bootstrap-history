"""The rules of a deal as functions of plain figures: an actor's patents, shares and offers in, the figures they become out.

An exchange applies them to a party's record (`record_dealings.py`); the seats module applies them to a seat's stored figures when it
receives the matching command. Neither argument is changed: each rule returns the new figure."""
from typing import Any, Dict, List, Tuple

from .joint_stock import EPSILON
from .plain_copy import plain

Patents = Dict[str, Dict[str, Any]]


def release_patent(patents: Patents, node_id: str, taker_id: str) -> Tuple[Patents, Dict[str, Any]]:
	"""(the patents without `node_id`, its right with `taker_id` struck from the licensees); KeyError when not held."""
	after = plain(patents)
	entry = after.pop(node_id)
	entry["licensees"] = [each for each in entry["licensees"] if each != taker_id]
	return after, entry


def receive_patent(patents: Patents, node_id: str, entry: Dict[str, Any]) -> Patents:
	"""The patents with the right `entry` held on `node_id`."""
	after = plain(patents)
	after[node_id] = plain(entry)
	return after


def add_licensee(patents: Patents, node_id: str, licensee_id: str) -> Patents:
	"""The patents with `licensee_id` among the licensees of the right on `node_id` (once)."""
	after = plain(patents)
	licensees = after[node_id]["licensees"]
	if licensee_id not in licensees:
		licensees.append(licensee_id)
	return after


def give_shares(issued: float, held: Dict[str, float], issuer_id: str, share: float, own_issue: bool) -> Tuple[float, Dict[str, float]]:
	"""(shares issued, shares held) after the actor gives `share` of `issuer_id`'s equity; an issuer giving its own raises what it has issued."""
	after = dict(held)
	if own_issue:
		return issued + share, after
	left = after.get(issuer_id, 0.0) - share
	if left > EPSILON:
		after[issuer_id] = left
	else:
		after.pop(issuer_id, None)
	return issued, after


def take_shares(issued: float, held: Dict[str, float], issuer_id: str, share: float, own_issue: bool) -> Tuple[float, Dict[str, float]]:
	"""(shares issued, shares held) after the actor takes `share` of `issuer_id`'s equity; an issuer taking its own back lowers what it has issued."""
	after = dict(held)
	if own_issue:
		return max(0.0, issued - share), after
	after[issuer_id] = after.get(issuer_id, 0.0) + share
	return issued, after


def keep_offer(offers: List[Dict[str, Any]], offer: Dict[str, Any]) -> List[Dict[str, Any]]:
	"""The offers with `offer` kept."""
	return plain(offers) + [plain(offer)]


def drop_offer(offers: List[Dict[str, Any]], offer_id: str) -> List[Dict[str, Any]]:
	"""The offers without the one named `offer_id`."""
	return [plain(offer) for offer in offers if offer["id"] != offer_id]


def drop_lapsed_offers(offers: List[Dict[str, Any]], year: int) -> Tuple[List[Dict[str, Any]], List[str]]:
	"""(the offers still open in `year`, the ids of those past their last year)."""
	return ([plain(offer) for offer in offers if year <= offer["expires"]], [offer["id"] for offer in offers if year > offer["expires"]])
