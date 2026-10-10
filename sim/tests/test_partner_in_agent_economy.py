"""A partner country in the agent economy, in a whole game (slow: builds a game and its spun-up economy).

Rome with the Han economy switched into the agent economy: its people sit on the tiles it holds as its census
places them, its producers run only what its techniques allow, its pay, prices and output are read from its own
markets, the foreign government's budget follows them, and the home answers are not mixed with them."""

from .harness import *  # noqa: F401,F403
from sim.engine import foreign_economies as foreign_module
from sim.economy import api as economy_api

original = foreign_module.foreign_economy_records
records = original()
switched = tuple(dict(record, agent_economy=True) if record["civilization"] == "han_china_100ad" else record
                 for record in records)
foreign_module.foreign_economy_records = lambda: switched

game = sim(civ="rome_100ad")
check("the partner is in the agent economy and no longer trades by the partner books",
      "han_china_100ad" in game.partners_in_agent_economy() and "han_china_100ad" not in game.foreign_economies()
      and "han_china_100ad" in game.partner_countries(), game.partners_in_agent_economy())

agent = game.economy.agent
economy = agent.economy()
setup = economy.setup
check("the economy holds two countries", setup.countries() == ("rome_100ad", "han_china_100ad"), setup.countries())
han_people = economy_api.country_figures.population(economy, "han_china_100ad")
check("the Han people on its tiles are the census total", abs(han_people - 57_671_402) < 0.5 * 57_671_402 * 0.01 + 1.0, han_people)

han_recipes = set(setup.recipes_by_country["han_china_100ad"])
producers = economy_api.producers_of(economy, "han_china_100ad")
check("Han producers run only recipes its techniques allow", producers and all(p.recipe_id in han_recipes for p in producers.values()), None)
rome_producers = economy_api.producers_of(economy)
check("Rome's producers are on Rome's tiles", all(setup.country_of(p.tile) == "rome_100ad" for p in rome_producers.values()), None)

game.step()
answers = game.economy.agent_country("han_china_100ad")
check("the economy answers for Han once its labour markets have a wage", answers is not None and answers.pay_per_person_year("labourer") > 0.0, answers)
check("Han's pay is its own markets', not Rome's rescaled",
      abs(answers.pay_per_person_year("labourer") - game.labour.market.quote_annual("labourer")) > 1e-9, None)
check("money and goods are conserved across both countries", economy.record.book.check_conservation(1e-6).breaches == (), None)

foreign_module.foreign_economy_records = original
