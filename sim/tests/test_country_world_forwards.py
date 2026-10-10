"""A foreign country answers pay, output and cost of living from its own markets and only from them; a country
with no economy of its own, or one that cannot answer a figure, raises NoCountryEconomy (stand-ins, no game)."""

QUICK_TOPIC = True

from .harness import check

from sim.agents.country_view import CountryWorld, NoCountryEconomy
from sim.agents.records import CountryProfile
from sim.agents.stratum_year import FOOD_NEED


class Own:
    """What the economy answers for the country."""

    def pay_per_person_year(self, trade):
        return {"labourer": 321.0}.get(trade)

    def society_output(self):
        return 9.0e6

    def need_floor_costs_per_person_year(self):
        return {FOOD_NEED: 77.0, "shelter": 11.0}


class Shared:
    """The home country's world."""

    def __init__(self, own):
        self.own = own

    def country_economy(self, country):
        return self.own if country == "beta" else None

    def pay_per_person_year(self, trade):
        return 100.0

    def society_output(self):
        return 1.0e9

    def subsistence_cost_per_person_year(self):
        return 40.0

    def need_floor_costs_per_person_year(self):
        return {FOOD_NEED: 40.0}


class Holder:
    pass


def raises(call):
    try:
        call()
    except NoCountryEconomy:
        return True
    return False


beta = CountryProfile(country="beta", population=500_000, wage_index=0.5, price_index=2.0)
inside = CountryWorld(Shared(Own()), beta, Holder())
check("a country in the economy pays what its own labour markets pay, not the home pay scaled",
      inside.pay_per_person_year("labourer") == 321.0, inside.pay_per_person_year("labourer"))
check("its output is what its own producers make", inside.society_output() == 9.0e6, None)
check("its cost of living is its own floor, not the home figure over its price index",
      inside.subsistence_cost_per_person_year() == 77.0 and inside.need_floor_costs_per_person_year()["shelter"] == 11.0, None)
check("a trade its markets have no wage for raises rather than take the home pay",
      raises(lambda: inside.pay_per_person_year("scribe")), None)

outside = CountryWorld(Shared(None), beta, Holder())
check("a country with no economy raises for pay, output and both cost figures",
      raises(lambda: outside.pay_per_person_year("labourer")) and raises(outside.society_output)
      and raises(outside.subsistence_cost_per_person_year) and raises(outside.need_floor_costs_per_person_year), None)


class NoEconomy:
    """A shared world with no country_economy member at all."""

    def pay_per_person_year(self, trade):
        return 10.0


check("a shared world that cannot answer for countries raises, it does not answer with the home figure",
      raises(lambda: CountryWorld(NoEconomy(), beta, Holder()).pay_per_person_year("labourer")), None)
check("the error is a LookupError naming the country",
      issubclass(NoCountryEconomy, LookupError) and "beta" in str(NoCountryEconomy("beta")), None)
