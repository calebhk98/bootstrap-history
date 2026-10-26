"""One-line forwarders from `Sim` to the agriculture module, for callers not yet in a module.

Each goes when its last caller reads the view (`sim.view(name)`) or sends the command (`sim.send(command)`) itself."""
from sim.agriculture.api import InvestFarm, SellFarm
from sim.refusal import Refusal

from .units_prose import area_text


class ForwardAgricultureMixin:

    def farm_sites(self):
        return self.view("farm_sites")()

    def refresh_farm_territory(self):
        """The farm's ladder, ceiling and cleared ground's quality from the held tiles as they now are: the soil nitrogen
        stock and the society's rotation both move a tile's yield factor and cropped hectares. The ladder, the ceiling and
        the farm area are the farm workforce's, so they are set here until it moves."""
        territory = self.view("farm_territory")()
        self._farm_ladder = territory.ladder
        self._farm_arable_ceiling = territory.cropped_hectares
        self.labour.set_farm_area(self.farm_land.hectares)

    def _farm_year_weather_seed(self, year, region=None):
        return self.view("weather_seed")(year, region)

    def _pooled_farm_weather_multiplier(self, year, weather_stdev_fraction=None, harmed=True):
        return self.view("harvest_weather")(year, weather_stdev_fraction, harmed)

    def farm_weather_by_tile(self, year):
        return self.view("farm_weather")[year]

    def farm_price_per_hectare(self):
        """What one hectare of farmland costs now (`buy farm`, `quote farm`)."""
        return self.view("farm_land_price")()

    def invest_farm(self, hectares):
        """Buy productive farmland that lowers the household staple price; the hectares bought, 0.0 when refused."""
        answer = self.send(InvestFarm(hectares))
        return 0.0 if isinstance(answer, Refusal) else answer

    def sell_farm(self, hectares):
        """Sell farmland back to the land market at what `buy farm` charges per hectare, nothing taken as a fee."""
        answer = self.send(SellFarm(hectares))
        if isinstance(answer, Refusal):
            if answer.cause == "not_owned":
                return {"ok": False, "error": "you own %s of farmland, not %s" % (
                    area_text(answer.facts["owned"], self, digits=1), area_text(answer.facts["hectares"], self, digits=1))}
            return {"ok": False, "error": str(answer)}
        return {"ok": True, "sold_farm_hectares": answer["hectares"], "price": round(answer["price"], 1),
                "farm_hectares": round(answer["remaining"], 1), "capital": round(self.household.capital, 1)}
