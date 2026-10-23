"""Complaints 644 and 648: what a bonded person is worth and where merchants buy people, and how bought people are held
bonded in the economy's hours. Each rule is called on built inputs; no game."""
QUICK_TOPIC = True

import math

from .harness import *  # noqa: F401,F403

from sim.economy import bondage_hours
from sim.economy.types import LabourBid, LabourOffer
from sim.labour.market import bonded_worth
from sim.labour.market.expectations import annuity_factor
from sim.labour.market.records import Route

RATE, CAREER, HOURS = 0.05, 30.0, 2000.0

# the worth of hours: present value over a working life at the lenders' ask
check("a person's worth is the wage times the year's hours times the annuity factor",
      abs(bonded_worth.worth_of_hours(0.01, HOURS, CAREER, RATE) - 0.01 * HOURS * annuity_factor(RATE, CAREER)) < 1e-9)
check("a dearer money (a higher ask) makes the same hours worth less",
      bonded_worth.worth_of_hours(0.01, HOURS, CAREER, 0.10) < bonded_worth.worth_of_hours(0.01, HOURS, CAREER, 0.03))
check("a longer working life is worth more", bonded_worth.worth_of_hours(0.01, HOURS, 40.0, RATE)
      > bonded_worth.worth_of_hours(0.01, HOURS, 20.0, RATE))
check("no wage, no worth", bonded_worth.worth_of_hours(0.0, HOURS, CAREER, RATE) == 0.0)

# trained against untrained: the trade's training years are repaid in the wage a trained hour fetches
untrained = bonded_worth.trained_wage_per_hour(None, 0.01, 0.0, RATE, CAREER)
trained = bonded_worth.trained_wage_per_hour(None, 0.01, 6.0, RATE, CAREER)
check("with no training years a person's hour fetches the floor wage", abs(untrained - 0.01) < 1e-12, untrained)
check("a trade with training years fetches more than the floor even where nobody practises it", trained > untrained, (trained, untrained))
check("a longer training makes the trained person dearer",
      bonded_worth.trained_wage_per_hour(None, 0.01, 10.0, RATE, CAREER) > trained)
check("where the trade is practised its wage counts when it is higher",
      bonded_worth.trained_wage_per_hour(trained * 2.0, 0.01, 6.0, RATE, CAREER) == trained * 2.0)
check("a practised wage below the premium wage does not price the person under it",
      bonded_worth.trained_wage_per_hour(untrained, 0.01, 6.0, RATE, CAREER) == trained)

# carriage: the cheapest way along the routes, several hops
routes = {"a": [Route("b", 2.0), Route("c", 10.0)], "b": [Route("c", 3.0)], "c": []}
check("no move costs nothing", bonded_worth.cheapest_carriage(routes, "a", "a") == 0.0)
check("carriage takes the cheaper way over several hops", bonded_worth.cheapest_carriage(routes, "a", "c") == 5.0)
check("no way in is no carriage", bonded_worth.cheapest_carriage(routes, "c", "a") is None)

# lots: cheapest landed price first, never above the bid, drawn from what is for sale
for_sale = {"a": 10.0, "b": 10.0, "far": 10.0}
lots = bonded_worth.buy_lots("c", "smith", 15.0, 100.0, for_sale, {"a": 40.0, "b": 50.0, "far": 10.0},
                             {"a": 5.0, "b": 3.0, "far": None})
check("people are bought where ask plus carriage is lowest, cheapest first", [lot.origin for lot in lots] == ["a", "b"]
      and abs(lots[0].people - 10.0) < 1e-9 and abs(lots[1].people - 5.0) < 1e-9, lots)
check("an area with no way in sells none", all(lot.origin != "far" for lot in lots))
check("what is bought is drawn off what is for sale", for_sale == {"a": 0.0, "b": 5.0, "far": 10.0}, for_sale)
check("the lot's price is its ask plus its carriage", abs(lots[0].price - 45.0) < 1e-9, lots[0].price)
check("nothing is bought above the buyers' bid",
      bonded_worth.buy_lots("c", "smith", 5.0, 44.0, {"a": 10.0}, {"a": 40.0}, {"a": 5.0}) == [])
check("a cheaper-landed origin farther off beats a nearer dear one",
      bonded_worth.buy_lots("c", "smith", 1.0, 100.0, {"a": 10.0, "b": 10.0}, {"a": 90.0, "b": 20.0},
                            {"a": 0.0, "b": 30.0})[0].origin == "b")

# a trained bonded person sells dearer than an untrained one from the same owner (the rule 644 asks for)
floor_hour = 0.01
ask_trained = bonded_worth.worth_of_hours(bonded_worth.trained_wage_per_hour(None, floor_hour, 6.0, RATE, CAREER), HOURS, CAREER, RATE)
ask_untrained = bonded_worth.worth_of_hours(floor_hour, HOURS, CAREER, RATE)
check("the owner's ask for a trained person exceeds the ask for an untrained one", ask_trained > ask_untrained, (ask_trained, ask_untrained))


# held bonded people work in their holder's works, off the market, and the holder pays their keep
def offers_in(area, trade, *hours_by_cohort):
    return [LabourOffer("cohort%d" % index, trade, area, hours, 0.001) for index, hours in enumerate(hours_by_cohort)]


held = {"t1": {"smith": {"forge": 3.0}}}
offers = offers_in("work@t1", "smith", 4000.0, 6000.0)
bids = [LabourBid("forge", "smith", "work@t1", 5000.0, 1.0), LabourBid("mill", "smith", "work@t1", 5000.0, 1.0)]
placement = bondage_hours.place_held(held, lambda area, trade: 10.0, offers, bids, HOURS, {"work@t1": 50.0}, lambda tile: "work@" + tile)
check("the held people's hours come off the households' offers", abs(sum(offer.hours for offer in placement.offers) - (10000.0 - 5000.0)) < 1e-6,
      placement.offers)
check("the offers are cut in proportion", abs(placement.offers[0].hours - 4000.0 * 0.5) < 1e-6, placement.offers[0])
check("the holder is credited the hours and no one else", placement.hired == {"forge": {"smith": 5000.0}}, placement.hired)
check("the holder's bid falls by the hours worked (it wanted fewer than the people held could give), the other's is untouched",
      abs(placement.bids[0].hours) < 1e-6 and placement.bids[1].hours == 5000.0, placement.bids)
check("the holder pays the keep of the people working for it, to the households whose hours were taken",
      abs(sum(amount for _, _, amount in placement.keep) - 5000.0 / HOURS * 50.0) < 1e-6 and {cohort for _, cohort, _ in placement.keep} == {"cohort0", "cohort1"},
      placement.keep)

held = {"t1": {"smith": {"forge": 3.0}}}
placement = bondage_hours.place_held(held, lambda area, trade: 1.0, offers_in("work@t1", "smith", 4000.0), bids, HOURS,
                                     {"work@t1": 50.0}, lambda tile: "work@" + tile)
check("deaths and retirements thin the people held: no more than the trade's workers there",
      abs(held["t1"]["smith"]["forge"] - 1.0) < 1e-9 and placement.hired == {"forge": {"smith": HOURS}}, (held, placement.hired))
placement = bondage_hours.place_held({"t1": {"smith": {"forge": 3.0}}}, lambda area, trade: 10.0,
                                     offers_in("work@t1", "smith", 1000.0), [LabourBid("forge", "smith", "work@t1", 0.0, 1.0)], HOURS,
                                     {}, lambda tile: "work@" + tile)
check("a holder with no work for them leaves their hours on the market", placement.hired == {} and placement.offers[0].hours == 1000.0)

record = {}
bondage_hours.hold(record, {("t1", "smith"): {"forge": 2.0}})
bondage_hours.hold(record, {("t1", "smith"): {"forge": 1.0, "mill": 4.0}})
check("holdings add up by tile, trade and employer", record == {"t1": {"smith": {"forge": 3.0, "mill": 4.0}}}, record)
