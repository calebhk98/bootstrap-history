"""A foreign country that is part of the economy answers pay, output and cost of living from its own markets;
one that is not keeps the labelled estimate scaled from the home answers (stand-ins, no game)."""

QUICK_TOPIC = True

from .harness import check

from sim.agents.country_view import CountryWorld
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


class HomeState:
    home_country = "alpha"
    countries = {"alpha": CountryProfile(country="alpha", population=1_000_000, wage_index=1.0, price_index=1.0)}


class Holder:
    state = HomeState


beta = CountryProfile(country="beta", population=500_000, wage_index=0.5, price_index=2.0)
inside = CountryWorld(Shared(Own()), beta, Holder())
check("a country in the economy pays what its own labour markets pay, not the home pay scaled",
      inside.pay_per_person_year("labourer") == 321.0, inside.pay_per_person_year("labourer"))
check("its output is what its own producers make", inside.society_output() == 9.0e6, None)
check("its cost of living is its own floor, not the home figure over its price index",
      inside.subsistence_cost_per_person_year() == 77.0 and inside.need_floor_costs_per_person_year()["shelter"] == 11.0, None)
check("a trade its markets have no wage for falls back to the labelled scaling",
      inside.pay_per_person_year("scribe") == 100.0 * 0.5, inside.pay_per_person_year("scribe"))

outside = CountryWorld(Shared(None), beta, Holder())
check("a country not in the economy keeps the estimate scaled from the home answers",
      outside.pay_per_person_year("labourer") == 50.0
      and outside.society_output() == 1.0e9 * 0.5 * 0.5
      and outside.subsistence_cost_per_person_year() == 80.0, None)


class NoEconomy:
    """A shared world with no country_economy member at all."""

    def pay_per_person_year(self, trade):
        return 10.0

    def society_output(self):
        return 1.0

    def subsistence_cost_per_person_year(self):
        return 1.0

    def need_floor_costs_per_person_year(self):
        return {}


check("a shared world that cannot answer for countries leaves the estimate in place",
      CountryWorld(NoEconomy(), beta, Holder()).pay_per_person_year("labourer") == 5.0, None)
