"""SMOKE: the game runs on the agent economy (sim/economy/, through sim/engine/economy_port*.py): prices and wages come
from it and move, money is conserved, the state's tax grain no longer swamps the wheat market (Complaint 383), a saved
game resumes the same economy, and every civilisation plays on it. Seven wiring scenarios between the engine and the
economy package, whose own rules are tested in sim/tests/test_economy_*.py."""
from .harness import *  # noqa: F401,F403
import math
import os
import tempfile

from sim.tests import fingerprint as perf_fingerprint
from sim.engine.saveload import save_state, load_state
from sim.economy import api as economy_api


def agent_game(civ, seed=1):
    game = S.Sim(NODES, ORDER, random.Random(seed), events=True, manual=False, civ=S.load_civ(civ))
    game.goal, game.done_year = GOAL, {}
    return game


rome = agent_game("rome_100ad")
opened = rome.economy.agent.economy().record
default = sim()
check("scenario: a game asked for the agent economy, and one that says nothing, run on it; after the hidden spin-up "
      "households' last price level is the rebased index, so the rebase is not read as inflation (Complaint 548)",
      rome.economy.agent is not None and default.economy.agent is not None
      and all(cohort.last_basket_price_level == 1.0 and math.isfinite(cohort.expected_inflation)
              for cohort in opened.cohorts.values()),
      sorted({(cohort.expected_inflation, cohort.last_basket_price_level) for cohort in opened.cohorts.values()})[:3])

# the opening price, then the price after the first year
prices, wages = [rome.economy.material_price("wheat_kg")], []
rome.step()
prices.append(rome.economy.material_price("wheat_kg"))
wages.append(rome.economy.labour.quote("labourer"))
old_wheat = rome._material_prices()["wheat_kg"]
opening_wage = rome.state.economy.agent_economy["opening"]["wages"]["labourer"]
check("scenario: wheat is priced by the agent economy, not at the engine's own cost, and moves from year to year; "
      "the labourer's wage comes from the agent economy's labour market",
      abs(prices[-1] / old_wheat - 1.0) > 1e-6 and len({round(price, 9) for price in prices}) > 1
      and abs(wages[-1] / opening_wage - 1.0) > 1e-6,
      "agent %r engine %r wages %r opening %r" % (prices[-1], old_wheat, wages[-1], opening_wage))

economy = rome.economy.agent.economy()
report = economy.record.book.check_conservation(1e-9)
state = economy.setup.state_agent
state_wheat = sum(sum(tiles.values()) for good, tiles in economy.record.book.holdings(state)["goods"].items()
                  if good == "wheat_kg")
wheat_traded = sum(volume for key, volume in economy.record.volumes.items() if key.startswith("wheat_kg|"))
check("scenario: money and goods are conserved in the agent economy's book; the state holds the grain it took in tax "
      "and wheat still trades, not pinned at a floor price (Complaint 383)",
      report.ok and state_wheat > 0.0 and wheat_traded > 0.0 and prices[-1] > 0.0 and len(set(prices)) > 1,
      (report.breaches[:5], state_wheat, wheat_traded))

# The founder's concern sells through the market at what its output costs to make at the economy's
# own prices and wages, never at the engine's old price table (CLAUDE.md 4.5).
founder = agent_game("rome_100ad")
founder.state.projects.done.add("finery_puddling")
founder.state.projects.operating.add("finery_puddling")
founder.state.projects.business.set_opened_year("finery_puddling", founder.state.scenario.year - 5)
founder._done_changed()


def _no_price_table():
    raise AssertionError("the founder's offers read the old price table")


founder._material_prices = _no_price_table
founder_orders = founder.economy.agent._seat_orders()
founder_offers = [offer for orders in founder_orders.values() for offer in orders.offers]
check("scenario: the founder's concern output is offered without the old price table, at a finite reservation",
      founder_offers and all(0.0 <= offer.reservation_price < float("inf") for offer in founder_offers),
      founder_offers[:2])

played = {}
conserved = {}
for civ in ("han_china_100ad", "norse_900ad"):
    game = played[civ] = agent_game(civ)
    game.step()
    conserved[civ] = game.economy.agent.economy().record.book.check_conservation(1e-9).ok
check("scenario: the other civilisations play a year on the agent economy with money conserved",
      all(conserved.values()), conserved)

# One owner for credit: the founder's room and the rate both come from the agent economy's market.
credit_game = rome
agent_market = credit_game.economy.agent.economy()
# the market answers None until lenders have met (no savings on offer): then the engine's room is None too
market_room = economy_api.credit_room(agent_market, credit_game.state.acting_seat)
engine_room = credit_game.market_credit_room(credit_game.state.acting_seat)
check("scenario: on the agent economy the credit room is the agent market's, in coin, as the rate is",
      (engine_room is None if market_room is None
       else engine_room is not None
       and abs(engine_room - market_room * agent_market.setup.coin_per_unit) <= 1e-9 * abs(engine_room))
      and credit_game.market_rate() == economy_api.interest_rate(agent_market),
      (engine_room, market_room))

# The Norse game, already a year in, is the one saved and resumed (the smallest whole game to step twice).
unbroken = played["norse_900ad"]
save_path = os.path.join(tempfile.mkdtemp(), "agent_save.json")
save_state(unbroken, save_path)
resumed = agent_game("norse_900ad")
load_state(resumed, save_path)
unbroken.step()
resumed.step()
# the stored record is exported when a game is saved, so both are brought up to their live economies first
unbroken.economy.flush_record()
resumed.economy.flush_record()
check("scenario: a saved game on the agent economy resumes the same economy and the same game state",
      unbroken.state.economy.agent_economy == resumed.state.economy.agent_economy
      and perf_fingerprint.digest(perf_fingerprint.state_of(unbroken)) == perf_fingerprint.digest(perf_fingerprint.state_of(resumed)))
