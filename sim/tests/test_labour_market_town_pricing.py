"""Complaint 368: the housing term of a wage comes from the town the work is in, not from one
household, and commission, bondage and workshop pay take the same cost factors as a hired hour."""
from .harness import *  # noqa: F401,F403
from functools import partial

sim = partial(sim, agent_economy=False)   # these checks pin the engine's own loanable-funds market, wage table and state budget


from sim.agents.api import SimWorld
from sim.engine.state import ActorRecord

TRADE = "artisan"


def crowded_game(founder_staff, firm_staff):
    """A game whose town holds `founder_staff` people on the founder's books and `firm_staff` on a firm's."""
    game = sim()
    game.state.household.employees = {"labourer": float(founder_staff)} if founder_staff else {}
    if firm_staff:
        firm = game.actors.add("firm:crowd", ActorRecord(kind="firm", money=1.0e6))
        firm.workforce["labourer"] = float(firm_staff)
        game.actors.refresh_staff()
    return game


# ---- housing is a fact about the town, whoever employs the people ---------------------------------
town_room = sim().labour.market.town_housing_room()
full_town = town_room * 1.2
by_founder = crowded_game(full_town, 0)
by_firm = crowded_game(0, full_town)
split = crowded_game(full_town / 2, full_town / 2)
empty = sim()
founder_housing = by_founder.labour.market.cost_factors(TRADE)["housing"]
check("a crowded town raises the housing factor", founder_housing > 1.0 + 1e-9, founder_housing)
check("the same people on a firm's books give the same housing factor as on the founder's",
      abs(by_firm.labour.market.cost_factors(TRADE)["housing"] - founder_housing) < 1e-12)
check("the housing factor does not depend on how the people are split between employers",
      abs(split.labour.market.cost_factors(TRADE)["housing"] - founder_housing) < 1e-12)
check("the quote for the same hour is the same whichever employer's staff crowd the town",
      abs(by_firm.labour.market.quote(TRADE) - by_founder.labour.market.quote(TRADE)) < 1e-12)
check("a firm's crowding reaches the founder's quote",
      by_firm.labour.market.quote(TRADE) > empty.labour.market.quote(TRADE))
check("a firm and the founder hiring the same trade are quoted the same hour",
      by_firm.labour.market.quote(TRADE, 0.0, employer="a firm")
      == by_firm.labour.market.quote(TRADE, 0.0, employer=by_firm.state.household))
check("an empty town has no housing premium", empty.labour.market.cost_factors(TRADE)["housing"] == 1.0)
built = crowded_game(full_town, 0)
built.state.household.worker_housing_places = full_town
check("housing built in the town eases the factor for everyone",
      built.labour.market.cost_factors(TRADE)["housing"] < founder_housing)


# ---- commission, bondage and the workshop carry the wage's cost factors ---------------------------
def priced(crowd):
    game = crowded_game(0, full_town if crowd else 0)
    game.price_index = 1.5
    game._wage_index_base = 1.3
    game.labour.market.press("smith", game.labour.market_supply("smith") * 0.5)
    return game


plain, crowded = priced(False), priced(True)
premium = 1.7
for label, game in (("an uncrowded town", plain), ("a crowded town", crowded)):
    market = game.labour.market
    check("%s: a commissioned hour is the market's quoted hour times the shop's premium" % label,
          abs(market.commission_cost("smith", 100.0, premium) - 100.0 * premium * market.quote("smith")) < 1e-6,
          (market.commission_cost("smith", 100.0, premium), 100.0 * premium * market.quote("smith")))
check("a commission costs more where housing is dearer",
      crowded.labour.market.commission_cost("smith", 100.0, premium)
      > plain.labour.market.commission_cost("smith", 100.0, premium))

for label, game in (("an uncrowded town", plain), ("a crowded town", crowded)):
    household = game.state.household
    household.bondage_years_left = 5
    household.bondage_debt = 1.0e9
    game._step_bondage()
    repaid = 1.0e9 - household.bondage_debt
    expected = (game.cfg["founder_hours_per_year"] * game.BONDAGE_LABOUR_SHARE
                * game.BONDAGE_WAGE_MARKUP * game.labour.market.quote("labourer"))
    check("%s: a year of bondage repays the market's labourer hour" % label,
          abs(repaid - expected) < 1e-6 * expected, (repaid, expected))

ratios = []
for game in (plain, crowded):
    game.state.household.employees = {"smith": 2.0}
    game.running_with_mechanic = lambda mechanic: True
    ratios.append(game.workshop_output() / game.labour.market.quote_annual("smith"))
check("the workshop values a craft hand at the market's annual wage, cost factors included",
      abs(ratios[0] - ratios[1]) < 1e-9 * ratios[0] and ratios[0] > 0, ratios)

# ---- a released hire eases the pressure it put on the trade ---------------------------------------
released = sim()
released.state.household.employees = {TRADE: 3.0}
released.labour.market.hire(released.state.household, TRADE, 3 * released.HOURS_PER_PERSON_YEAR)
pressed = released.labour.market.pressure(TRADE)
released.labour.fire(TRADE, 2)
check("firing staff eases the pressure their hiring put on the trade",
      released.labour.market.pressure(TRADE) < pressed - 1.9 * released.HOURS_PER_PERSON_YEAR,
      (pressed, released.labour.market.pressure(TRADE)))

shedding = sim()
firm = shedding.actors.add("firm:shed", ActorRecord(kind="firm", money=1.0e6))
firm.workforce[TRADE] = 4.0
firm.press_new_staff({}, SimWorld(shedding))
pressed = shedding.labour.market.pressure(TRADE)
firm.workforce[TRADE] = 1.0
firm.press_new_staff({TRADE: 4.0}, SimWorld(shedding))
check("a firm shedding staff eases the pressure too",
      shedding.labour.market.pressure(TRADE) < pressed - 2.9 * shedding.HOURS_PER_PERSON_YEAR,
      (pressed, shedding.labour.market.pressure(TRADE)))
