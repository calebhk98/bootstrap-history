"""Trade that actors (the traders) carry between this society and a partner, as the partner's market sees it.

Actors tally the year's cargo here (`NoteActorTrade`); the tallies reset at the year's end (`ResetActorTradeTallies`).
A good the actors carry in a direction this year is theirs: the engine's aggregate
foreign flow and the agent economy's stand-in external orders leave that direction alone (`actors_carry`).

(needs: partner_price_level, market_rate)"""
from typing import Any, Optional, Tuple

from . import rules


class ActorTrade:

    def apply_note_actor_trade(self, command: Any) -> None:
        rules.note_actor_trade(self.world.actor_trade, command.partner, command.material, command.tonnes,
                               command.to_partner, command.landed_cost)

    def apply_note_actor_home_trade(self, command: Any) -> None:
        rules.note_home_trade(self.world.home_actor_trade, command.material, command.tonnes, command.landing)

    def actor_home_trade(self, material: str) -> Tuple[float, float]:
        """(tonnes landed in the home market, tonnes taken out of it) by actors so far this year."""
        return rules.home_trade(self.world.home_actor_trade, material)

    def actors_carry(self, material: str, to_partner: bool, partner: Optional[str] = None) -> bool:
        """Whether actors have carried the material this year toward (or from) a partner, any partner by default."""
        return rules.actors_carry(self.world.actor_trade, material, to_partner, partner)

    def landed_cost(self, paid: float, carriage: float) -> float:
        """What a cargo costs its carrier on landing: the purchase, a year's return on it (the carrier's margin) and the
        carriage with its dues."""
        return rules.landed_cost(paid, carriage, self.needs.market_rate())

    def partner_price_per_unit(self, partner: str, material: str) -> Optional[float]:
        """A partner's price of a material in home money: its solved cost at its coin's price level; None when the partner
        prices nothing of it."""
        price = self.partner_facts(partner)["prices_in_home_money"].get(material)
        return price * self.needs.partner_price_level[partner] if price else None

    def apply_reset_actor_trade_tallies(self, command: Any) -> None:
        """The year ends: the actors' tallies reset."""
        self.world.home_actor_trade.clear()
        self.world.actor_trade.clear()
        self.bump("books")
