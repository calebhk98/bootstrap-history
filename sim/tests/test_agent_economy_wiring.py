"""The game on the agent economy (sim/economy/, through sim/engine/economy_port*.py): prices and wages
come from it and move, money is conserved, the state's tax grain no longer swamps the wheat market
(Complaint 383), a saved game resumes the same economy, and every civilisation plays on it."""
from .harness import *  # noqa: F401,F403
from sim import perf_fingerprint
from sim.engine.proto.saveload import save_state, load_state


def agent_game(civ, seed=1):
    game = S.Sim(NODES, ORDER, random.Random(seed), events=True, manual=False, civ=S.load_civ(civ),
                 cfg={"agent_economy": True})
    game.goal, game.done_year = GOAL, {}
    return game


rome = agent_game("rome_100ad")
check("a game asked for the agent economy runs on it", rome.economy.agent is not None)
off = perf_fingerprint.build(dict(civ="rome_100ad", seed=1, years=1, events=True, fog=False))
check("a game not asked for it keeps the engine's own economy", off.economy.agent is None
      and not off.state.economy.agent_economy)

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
