"""The one labour market quotes a person-year in another country's labour markets from the wages those markets
set, and says nothing for a country that is not part of the economy (stand-ins, no game)."""

QUICK_TOPIC = True

from .harness import check

from sim.labour.labour_market_api import LabourMarket


class Answers:
    def pay_per_person_year(self, trade):
        return {"labourer": 250.0}.get(trade)


class Economy:
    def agent_country(self, country):
        return Answers() if country == "han" else None


class World:
    economy = Economy()


class Labour:
    _world = World()


market = LabourMarket(Labour())
check("a person-year in a partner country is what its own markets pay", market.quote_annual_in("labourer", "han") == 250.0, None)
check("a trade its markets pay nothing for has no quote", market.quote_annual_in("scribe", "han") is None, None)
check("a country outside the economy has no quote", market.quote_annual_in("labourer", "norse") is None, None)
