"""The game on the agent economy (sim/economy/, through sim/engine/economy_port*.py): prices and wages
come from it and move, money is conserved, the state's tax grain no longer swamps the wheat market
(Complaint 383), a saved game resumes the same economy, and every civilisation plays on it."""
from .harness import *  # noqa: F401,F403
import os

from sim.tests import fingerprint as perf_fingerprint
from sim.engine.economy_port_year import SWITCH_ENVIRONMENT, switch_requested
from sim.engine.saveload import save_state, load_state
from sim.economy import api as economy_api


def agent_game(civ, seed=1):
    game = S.Sim(NODES, ORDER, random.Random(seed), events=True, manual=False, civ=S.load_civ(civ),
                 cfg={"agent_economy": True})
    game.goal, game.done_year = GOAL, {}
    return game


rome = agent_game("rome_100ad")
check("a game asked for the agent economy runs on it", rome.economy.agent is not None)
opened = rome.economy.agent.economy().record
check("after the hidden spin-up households expect stable prices, so the rebased index is not read as inflation",
      all(cohort.expected_inflation == 0.0 and cohort.last_price_level == 1.0 for cohort in opened.cohorts.values()),
      sorted({(cohort.expected_inflation, cohort.last_price_level) for cohort in opened.cohorts.values()})[:3])
default = perf_fingerprint.build(dict(civ="rome_100ad", seed=1, years=1, events=True, fog=False))
check("a game that says nothing runs on the agent economy", default.economy.agent is not None
      and default.state.economy.agent_economy.get("on"))
# the opt-out is the subject here: the switch itself is under test
off = S.Sim(NODES, ORDER, random.Random(1), events=True, manual=False, civ=S.load_civ("rome_100ad"),
            cfg={"agent_economy": False})
check("a game that opts out keeps the engine's own economy", off.economy.agent is None
      and not off.state.economy.agent_economy)

saved_switch = os.environ.pop(SWITCH_ENVIRONMENT, None)
try:
    check("the switch is on with no config", switch_requested({}) and switch_requested({"agent_economy": True}))
    check("only an explicit False opts out", not switch_requested({"agent_economy": False}))
    os.environ[SWITCH_ENVIRONMENT] = "1"
    check("the environment forces it on over an opt-out", switch_requested({"agent_economy": False}))
    os.environ[SWITCH_ENVIRONMENT] = "0"
    check("the environment forces it off over the default", not switch_requested({}))
finally:
    os.environ.pop(SWITCH_ENVIRONMENT, None)
    if saved_switch is not None:
        os.environ[SWITCH_ENVIRONMENT] = saved_switch

prices, wages = [], []
for _year in range(4):
    rome.step()
    prices.append(rome.economy.material_price("wheat_kg"))
    wages.append(rome.economy.labour.quote("labourer"))
old_wheat = off.economy.material_price("wheat_kg")
check("wheat is priced by the agent economy, not at the engine's own cost", abs(prices[0] / old_wheat - 1.0) > 1e-6,
      "agent %r engine %r" % (prices[0], old_wheat))
check("the wheat price moves from year to year", len({round(price, 9) for price in prices}) > 1, prices)
check("the labourer's wage comes from the agent economy's labour market",
      abs(wages[0] / off.economy.labour.quote("labourer") - 1.0) > 1e-6)

economy = rome.economy.agent.economy()
report = economy.record.book.check_conservation(1e-9)
check("money and goods are conserved in the agent economy's book", report.ok, report.breaches[:5])

state = economy.setup.state_agent
state_wheat = sum(sum(tiles.values()) for good, tiles in economy.record.book.holdings(state)["goods"].items()
                  if good == "wheat_kg")
wheat_traded = sum(volume for key, volume in economy.record.volumes.items() if key.startswith("wheat_kg|"))
check("Complaint 383: the state holds the grain it took in tax, and wheat still trades",
      state_wheat > 0.0 and wheat_traded > 0.0, (state_wheat, wheat_traded))
check("Complaint 383: wheat is not pinned at a floor price", prices[-1] > 0.0 and len(set(prices)) > 1)

# The founder's concern sells through the market at what its output costs to make at the economy's
# own prices and wages, never at the engine's old price table (CLAUDE.md 4.5).
founder = agent_game("rome_100ad")
founder.state.projects.done.add("finery_puddling")
founder.state.projects.operating.add("finery_puddling")
founder.state.projects.opened_year["finery_puddling"] = founder.state.scenario.year - 5
founder._done_changed()


def _no_price_table():
    raise AssertionError("the founder's offers read the old price table")


founder._material_prices = _no_price_table
founder_orders = founder.economy.agent._founder_orders()
founder_offers = [offer for orders in founder_orders.values() for offer in orders.offers]
check("the founder's concern output is offered without the old price table, at a finite reservation",
      founder_offers and all(0.0 <= offer.reservation_price < float("inf") for offer in founder_offers),
      founder_offers[:2])

unbroken = agent_game("rome_100ad")
save_path = os.path.join(tempfile.mkdtemp(), "agent_save.json")
for _year in range(2):
    unbroken.step()
save_state(unbroken, save_path)
resumed = agent_game("rome_100ad")
load_state(resumed, save_path)
unbroken.step()
resumed.step()
check("a saved game on the agent economy resumes the same economy",
      unbroken.state.economy.agent_economy == resumed.state.economy.agent_economy)
check("and the same game state", perf_fingerprint.digest(perf_fingerprint.state_of(unbroken))
      == perf_fingerprint.digest(perf_fingerprint.state_of(resumed)))

for civ in ("england_1300", "han_china_100ad", "mexica_1500", "norse_900ad"):
    game = agent_game(civ)
    for _year in range(3):
        game.step()
    book = game.economy.agent.economy().record.book
    check("%s plays three years on the agent economy with money conserved" % civ,
          book.check_conservation(1e-9).ok)

# One owner for credit: the founder's room and the rate both come from the agent economy's market.
credit_game = agent_game("rome_100ad")
for _year in range(2):
    credit_game.step()
agent_market = credit_game.economy.agent.economy()
check("on the agent economy the credit room is the agent market's, as the rate is",
      credit_game.market_credit_room("founder") == economy_api.credit_room(agent_market, "founder")
      and credit_game.market_rate() == economy_api.interest_rate(agent_market),
      (credit_game.market_credit_room("founder"), economy_api.credit_room(agent_market, "founder")))
