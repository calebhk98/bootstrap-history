"""A handover moves the leaver's debts and claims, goods and every store keyed by its id, and refuses a replacement that
holds works of its own. Read as numbers in the registry, the book and the stores; a handover pays and forgives nothing."""

QUICK_TOPIC = True

import json

from .harness import check

from sim.book import GoodsMove
from sim.agents.api import ActorRecord, ActorsState, PURSE_CURRENCY
from sim.contracts import Contract, TERM_LOAN
from sim.rekey import rekey, rename_text
from sim.refusal import cause_of

from sim.resources.state import ResourcesSeat

from .seat_handover_fixture import Game


def build():
    """Three seats and two other actors with money, debts, claims, goods, offers, licences and shares keyed by 'leaver'."""
    game = Game(["leaver", "heir", "third"])
    game.state.actors = ActorsState()
    purses = game.state.actors.purses
    game.state.attach_purses()
    purses.set_net("leaver", 100.0, "opening")
    purses.set_net("heir", 30.0, "opening")
    purses.set_net("third", 500.0, "opening")
    purses.set_offers({"third": 200.0})                      # a lender whose deposit funds the pool
    purses.transfer("leaver", "third", 160.0, "purchase")    # 60 more than the purse holds: a draw on the facility
    purses.contracts.term_loans.append(Contract("loan:1", "third", "leaver", PURSE_CURRENCY, 40.0, rate=0.1, years_left=3.0,
                                                arrears=5.0, kind=TERM_LOAN))
    purses.contracts.term_loans.append(Contract("loan:2", "leaver", "third", PURSE_CURRENCY, 25.0, rate=0.1, years_left=3.0,
                                                kind=TERM_LOAN))
    leaver = game.state.seats["leaver"]
    third = game.state.seats["third"]
    leaver.holdings.shares_held["third"] = 0.1
    leaver.holdings.patents["loom"] = {"granted": 1, "expires": 20, "licensees": ["third"]}
    third.holdings.shares_held["leaver"] = 0.2
    third.holdings.offers.append({"id": "leaver#1", "from": "leaver", "to": "third", "give": {}, "take": {}, "expires": 9})
    leaver.holdings.offers.append({"id": "third#1", "from": "third", "to": "leaver", "give": {}, "take": {}, "expires": 9})
    leaver.holdings.offer_serial = 1
    third.modules["diffusion"].disclosures["fire"] = {"mode": "licence", "licensees": {"leaver": {"fee": 1.0}}}
    game.state.actors.records["firm:1"] = ActorRecord(kind="firm", holdings={"leaver": 0.3}, spun_off_from="leaver",
                                                      royalty_owed={"loom": {"holder": "leaver", "rate": 0.1}})
    return game


def totals(game):
    purses = game.state.actors.purses
    contracts = list(purses.contracts.all())
    return {"money": purses.book.money_supply(PURSE_CURRENCY),
            "principal": sum(contract.principal for contract in contracts),
            "arrears": sum(contract.arrears for contract in contracts)}


game = build()
purses = game.state.actors.purses
leaver_debt = purses.debt("leaver")
heir_debt = purses.debt("heir")
leaver_net = purses.net("leaver")
heir_net = purses.net("heir")
before = totals(game)
check("the leaver owes on its facility and a term loan", leaver_debt > 100.0 and purses.contracts.facility_of("leaver"), leaver_debt)

moved = game.hand_over_seat("leaver", "heir")
after = totals(game)
check("the handover went through", not isinstance(moved, str) and moved["to"] == "heir", moved)
check("the replacement owes what the leaver owed, and the leaver owes nothing", abs(purses.debt("heir") - (heir_debt + leaver_debt)) < 1e-9
      and purses.debt("leaver") == 0.0, (purses.debt("heir"), heir_debt, leaver_debt))
check("the replacement's net position is its own and the leaver's", abs(purses.net("heir") - (heir_net + leaver_net)) < 1e-9,
      (purses.net("heir"), heir_net, leaver_net))
check("money in the book is unchanged", abs(after["money"] - before["money"]) < 1e-9, (after, before))
check("every contract's principal and arrears are unchanged except the loan the leaver had made to itself and the heir",
      abs(after["principal"] - before["principal"]) < 1e-9 and abs(after["arrears"] - before["arrears"]) < 1e-9, (after, before))
check("a loan the leaver owed the lender is now the replacement's debt",
      [contract.borrower for contract in purses.contracts.term_loans if contract.lender == "third"] == ["heir"], None)
check("a loan the leaver made is now the replacement's claim",
      [contract.lender for contract in purses.contracts.term_loans if contract.borrower == "third"] == ["heir"], None)
check("nothing in the purses' record names the leaver", "leaver" not in json.dumps(purses.to_canon_dict()), None)

third, heir_seat = game.state.seats["third"], game.state.seats["heir"]
check("the replacement holds the leaver's stake and licence under its own name",
      heir_seat.holdings.shares_held == {"third": 0.1} and heir_seat.holdings.patents["loom"]["licensees"] == ["third"], heir_seat.holdings)
check("another seat's stake in the leaver, its offer from the leaver and its disclosure licence name the replacement",
      third.holdings.shares_held == {"heir": 0.2} and third.holdings.offers[0]["from"] == "heir"
      and third.holdings.offers[0]["id"] == "heir#1" and "heir" in game.view("disclosures")["third"]["fire"]["licensees"], third.holdings)
check("the leaver's inbox of offers passes with the seat, addressed to the replacement",
      heir_seat.holdings.offers[0]["to"] == "heir" and heir_seat.holdings.offer_serial == 1, heir_seat.holdings.offers)
record = game.state.actors.records["firm:1"]
check("another actor's records name the replacement", record.holdings == {"heir": 0.3} and record.spun_off_from == "heir"
      and record.royalty_owed["loom"]["holder"] == "heir", record)

# ---- goods and money held across holders
game = build()
purses = game.state.actors.purses
purses.book.move(GoodsMove("edge:outside the book", "leaver", "grain", "rome", 40.0, "test"))
purses.book.move(GoodsMove("edge:outside the book", "heir", "grain", "rome", 10.0, "test"))
purses.book.move(GoodsMove("edge:outside the book", "third", "grain", "rome", 5.0, "test"))
goods_before = purses.book.goods_totals()
game.hand_over_seat("leaver", "heir")
check("the leaver's goods pass to the replacement and the total across holders is unchanged",
      purses.book.stock("heir", "grain", "rome") == 50.0 and purses.book.stock("leaver", "grain", "rome") == 0.0
      and purses.book.goods_totals() == goods_before, purses.book.goods_totals())
check("the book no longer knows the leaver", not purses.book.knows("leaver"), purses.book.agents())

# ---- a replacement that holds works is refused with a cause and nothing changes
game = build()
game.state.seats["heir"].modules["resources"] = ResourcesSeat(mines=[{"material": "iron_ore"}])
refused = game.hand_over_seat("leaver", "heir")
check("a replacement with workings of its own is refused", cause_of(refused) == "replacement_not_empty" and refused.facts["holds"] == ["holdings"], refused)
check("a refused handover changed nothing", "leaver" in game.state.seats and game.state.actors.purses.debt("leaver") > 0.0, None)
game = build()
game.state.seats["heir"].household.scholars = 2.0
check("a replacement with staff is refused", game.hand_over_seat("leaver", "heir").facts["holds"] == ["staff"], None)
game = build()
game.state.seats["heir"].household.interest_arrears = 3.0
check("a replacement with arrears is refused", game.hand_over_seat("leaver", "heir").facts["holds"] == ["arrears or bondage"], None)
game = build()
game.state.seats["heir"].projects.done |= {"wheel"}
game.state.seats["leaver"].projects.done |= {"fire"}
game.hand_over_seat("leaver", "heir")
check("a replacement that only knows techniques keeps them and adds the leaver's", game.state.seats["heir"].projects.done == {"wheel", "fire"}, None)

# ---- the renaming itself
check("an id is renamed whole and in composite ids, not inside other words",
      rename_text("leaver", "leaver", "heir") == "heir" and rename_text("facility:leaver:pool", "leaver", "heir") == "facility:heir:pool"
      and rename_text("leaver#4", "leaver", "heir") == "heir#4" and rename_text("leavers", "leaver", "heir") == "leavers", None)
merged = rekey({"leaver": 2.0, "heir": 3.0, "nested": {"leaver": ["leaver", "heir"]}}, "leaver", "heir")
check("two keys that become one add, and lists do not repeat an id", merged == {"heir": 5.0, "nested": {"heir": ["heir"]}}, merged)
