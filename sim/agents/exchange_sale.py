"""Selling a concern to whichever actor will pay for it: the exchange's own offer and acceptance.

The price is the concern's worth by the holder's recorded margin over the valuation horizon (the figure
an AI actor weighs a concern at, `exchange_commands.concern_worth`). The buyer is the eligible actor with
the most money left over after paying, ties by id; eligible means it is an AI actor that could take the
concern (knows how, is not blocked by a patent) and can pay.
"""
from typing import Any, Callable, Dict, Iterable

from . import exchange
from .exchange_commands import concern_worth
from .player_commands import CommandRejected


def sale_price(seller: Any, node_id: str) -> float:
	return concern_worth(seller, node_id)


def eligible_buyers(seller: Any, node_id: str, price: float, candidates: Iterable[Any], world: Any) -> list:
	"""The candidates that could take the concern for `price` now, in the order the exchange prefers them."""
	give, take = {"concern": node_id}, {"money": price}
	able = [buyer for buyer in candidates
			if buyer is not seller and buyer.record.controller == "ai"
			and not exchange.problem(seller, buyer, give, take, world)]
	return sorted(able, key=lambda buyer: (-(buyer.money - price), buyer.actor_id))


def sell_concern(seller: Any, node_id: str, candidates: Iterable[Any], find_actor: Callable[[str], Any],
				 world: Any) -> Dict[str, Any]:
	"""Sell `node_id` to the preferred buyer among `candidates`; raises `CommandRejected` with the reason
	when it cannot be sold. Returns the buyer's id and the price paid."""
	if node_id not in seller.concerns:
		raise CommandRejected("you do not run " + node_id)
	price = sale_price(seller, node_id)
	if price <= 0.0:
		raise CommandRejected("nobody would pay for %s: it earns nothing" % node_id)
	buyers = eligible_buyers(seller, node_id, price, candidates, world)
	if not buyers:
		raise CommandRejected("no actor can both make %s and pay %.0f for it" % (node_id, price))
	buyer = buyers[0]
	offer = exchange.make_offer(seller, buyer, {"concern": node_id}, {"money": price}, world)
	exchange.accept(buyer, offer["id"], find_actor, world)
	return {"buyer": buyer.actor_id, "price": price}
