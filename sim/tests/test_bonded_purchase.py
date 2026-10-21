"""Complaint 644: bonded purchase wired to a game. Which tiles allow it, who is for sale, and a purchase moving
people and paying the owner. Each rule is called on built inputs; no game."""
QUICK_TOPIC = True

from .harness import *  # noqa: F401,F403

from sim.agents.api import ActorsState, ActorRegistry, seed_strata
from sim.agents.bonded_sale import (CAPTIVE_SHARE_OF_CONQUERED_PEOPLE, CAPTIVE_SHARE_OF_DEFEATED_LOSSES, add_captives, bondage_tiles,
                                    bonded_for_sale, buy_bonded, captives_from_conquest, captives_from_losses)
from sim.agents.records import CountryProfile
from sim.agents.stratum import stratum_id
from sim.economy import bonded_purchase
from sim.economy.accounts import Book
from sim.economy.types import EDGE_EXCHANGE, EDGE_MINT, LabourBid, Transfer
from sim.labour.market.bonded_worth import BondedLot

from .agents_fake_world import FakeWorld


class CostedWorld(FakeWorld):
    def population_total(self):
        return 1.0e6

    def subsistence_cost_per_person_year(self):
        return 1.0


def registry_of(*profiles):
    state = ActorsState()
    for each in profiles:
        state.countries[each.country] = each
    state.home_country = profiles[0].country
    registry = ActorRegistry(state)
    seed_strata(registry, CostedWorld())
    return registry


def profile(country, tiles, extra):
    return CountryProfile(country=country, name=country, population=1.0e6, urban_fraction=0.2, home_tiles=tiles,
                          extra=extra)


registry = registry_of(profile("slaveholders", ["t1", "t2"], {"debt_bondage": True}),
                       profile("free", ["t3"], {}))

# areas where bonded people may be bought
check("a country with bondage puts its tiles in bondage_allowed", {"t1", "t2"} <= set(bondage_tiles(registry)),
      bondage_tiles(registry))
check("a country without bondage leaves its tiles out", "t3" not in bondage_tiles(registry), bondage_tiles(registry))

# the people for sale come from the bonded stratum
for_sale = bonded_for_sale(registry)
bonded = [actor for actor in registry.of_kind("stratum") if actor.is_bonded()]
check("only the country with a bonded stratum has any for sale", set(for_sale) == {"t1", "t2"}, for_sale)
trade = bonded[0].record.plan["trade"]
offered = sum(by_trade.get(trade, 0.0) for by_trade in for_sale.values())
check("every member of the bonded stratum is on offer at its owners' price (no typed share)",
      abs(offered - bonded[0].record.members) < 1e-6, (offered, bonded[0].record.members))

# a purchase moves people and pays the owner; the money is conserved
stratum = bonded[0]
owner = registry.actors[stratum_id("slaveholders", stratum.record.plan["owner"])]
buyer = registry.state.edge("edge:economy")
members_before = stratum.record.members
owner_before = owner.money
bought = buy_bonded(registry, buyer, "t1", trade, 100.0, 7.0)
check("the people bought leave the bonded stratum",
      abs(members_before - stratum.record.members - 100.0) < 1e-9 and bought == 100.0,
      (members_before, stratum.record.members, bought))
check("the owner is paid the price of the people taken", abs(owner.money - owner_before - 700.0) < 1e-9,
      (owner.money, owner_before))
check("a country without those people sells none", buy_bonded(registry, buyer, "t3", trade, 5.0, 7.0) == 0.0)

# a carried purchase: the owner is paid the ask, the country's merchants the carriage
merchants = registry.actors[stratum_id("slaveholders", "merchants")]
owner_before, merchants_before = owner.money, merchants.money
buy_bonded(registry, buyer, "t2", trade, 10.0, 7.0, 3.0)
check("the owner is paid the ask and the merchants the carriage",
      abs(owner.money - owner_before - 70.0) < 1e-9 and abs(merchants.money - merchants_before - 30.0) < 1e-9,
      (owner.money - owner_before, merchants.money - merchants_before))

# captives of war join the taker's bonded stratum, where it has one
check("captives are a share of the defeated's losses",
      abs(captives_from_losses(1000.0) - 1000.0 * CAPTIVE_SHARE_OF_DEFEATED_LOSSES) < 1e-9)
check("a conquered tile gives a share of its people",
      abs(captives_from_conquest(1.0e4) - 1.0e4 * CAPTIVE_SHARE_OF_CONQUERED_PEOPLE) < 1e-9)
check("no losses, no captives", captives_from_losses(0.0) == 0.0 and captives_from_conquest(-5.0) == 0.0)
before = stratum.record.members
check("captives join the taker's bonded stratum",
      add_captives(registry, "slaveholders", 25.0) == 25.0 and abs(stratum.record.members - before - 25.0) < 1e-9,
      (before, stratum.record.members))
check("a society with no bonded stratum takes none into bondage", add_captives(registry, "free", 25.0) == 0.0)

# the economy side: employers bidding for the trade pay the price between them, as far as their cash goes
book = Book()
for employer, cash in (("forge", 600.0), ("mill", 100.0)):
    book.transfer(Transfer(EDGE_MINT, employer, "coin", cash, "opening"))
bids = [LabourBid("forge", "smith", "work@t1", 300.0, 1.0), LabourBid("mill", "smith", "work@t1", 100.0, 1.0),
        LabourBid("forge", "smith", "work@t2", 50.0, 1.0)]
lots = [BondedLot("work@t1", "smith", "work@t2", 4.0, 10.0, 2.0)]
bought_here, paid, paid_lots, held = bonded_purchase.settle(book, "coin", lots, bids)
price = 4.0 * 12.0
check("the economy reports the people bought by tile", bought_here == {("t1", "smith"): 4.0}, bought_here)
check("the employers pay the price between them",
      abs(paid - price) < 1e-9 and abs(book.balance(EDGE_EXCHANGE, "coin") - price) < 1e-9, (paid, price))
check("the lot is reported as paid: ask and carriage by origin",
      paid_lots == [{"origin": "t2", "destination": "t1", "trade": "smith", "people": 4.0, "ask": 40.0, "carriage": 8.0}],
      paid_lots)
check("the people are held by the employers who bid, in proportion to their hours",
      abs(held[("t1", "smith")]["forge"] - 3.0) < 1e-9 and abs(held[("t1", "smith")]["mill"] - 1.0) < 1e-9, held)
check("the book still sums to nothing", abs(book.total("coin")) < 1e-9, book.total("coin"))
book = Book()
book.transfer(Transfer(EDGE_MINT, "forge", "coin", 12.0, "opening"))
_, paid, paid_lots, _ = bonded_purchase.settle(book, "coin", lots, [LabourBid("forge", "smith", "work@t1", 300.0, 1.0)])
check("an employer short of cash pays what it has and the owners are paid that share",
      abs(paid - 12.0) < 1e-9 and abs(paid_lots[0]["ask"] - 10.0) < 1e-9, (paid, paid_lots))
