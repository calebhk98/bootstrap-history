"""Complaint 604, the wiring (the reading-share rules are test_country_literacy_totals, test_complaint_62_literacy_ceiling and
test_household_capacity_and_literacy): a country's literacy is read from that country's strata alone, the research a seat or a foreign
player does runs at its own country's lettered share, and the hours a project can call on follow it. Each method runs on a stand-in."""

QUICK_TOPIC = True

from types import SimpleNamespace

from .harness import check

from sim.agents.country_view import CountryWorld
from sim.diffusion.module import Diffusion
from sim.engine import bridge_diffusion
from sim.tests import module_harness
from sim.labour.labour_training import TrainingMixin


def stratum(country, members, literacy, propertied=False):
    plan = {"property_share": 0.3} if propertied else {}
    return SimpleNamespace(record=SimpleNamespace(country=country, members=members, literacy=literacy, exited_year=None, plan=plan))


STRATA = [stratum(None, 90.0, 0.1), stratum(None, 10.0, 0.9, propertied=True), stratum("other", 50.0, 0.3), stratum("other", 5.0, 0.6, propertied=True)]


class Society:
    """The actors a country's literacy is read from: a registry of strata and the home country's name."""

    def __init__(self):
        self.actors = SimpleNamespace(of_kind=lambda kind: list(STRATA), state=SimpleNamespace(home_country="home"))
        self.view = lambda name: lambda: self.actors   # the seeded registry


def literacy_of(country=None, field="literacy_general"):
    game = Society()
    return bridge_diffusion.legacy_country_literacy(game, country).get(field)


check("the home country's literacy is read from the home strata, whether named or not", abs(literacy_of() - 0.18) < 1e-12
      and abs(literacy_of("home") - 0.18) < 1e-12, literacy_of())
check("another country's literacy is read from its own strata and not the home people's", abs(literacy_of("other") - (50 * 0.3 + 5 * 0.6) / 55) < 1e-12, literacy_of("other"))
check("the lettered share is the propertied strata's", abs(literacy_of(field="literacy_elite") - 0.9) < 1e-12 and abs(literacy_of("other", "literacy_elite") - 0.6) < 1e-12, None)


# ---- research follows the lettered share
class Reading:
    """The diffusion module for a country whose lettered share is `elite`; `asked` records what it was asked."""

    def __init__(self, elite):
        self.asked = []

        class Lettered(Diffusion):
            def literacy(module, field, country=None):
                self.asked.append((field, country))
                return elite
        self.module = module_harness.build(Lettered, views={
            "literacy_references": lambda: {"factor_cap": 3.0, "reference_elite": 0.5, "reference_general": 0.1}})

    def research_productivity(self, country):
        return self.module.research_productivity(country)


check("research productivity is the lettered share over the reference", Reading(0.25).research_productivity("other") == 0.5, None)
game = Reading(0.1)
low = game.research_productivity(None)
check("a more lettered country researches faster", Reading(0.7).research_productivity(None) > low, None)
check("the lettered share asked about is the country's", game.asked == [("literacy_elite", None)], game.asked)
check("research productivity is capped", Reading(10.0).research_productivity(None) == 3.0, None)
check("no letters, no research", Reading(0.0).research_productivity(None) == 0.0, None)

asked = []
view = CountryWorld(SimpleNamespace(research_productivity=lambda country: asked.append(country) or 0.8), SimpleNamespace(country="other"),
                    SimpleNamespace(of_kind=lambda kind: list(STRATA), state=SimpleNamespace(home_country="home")))
check("a foreign player's research runs at its own country's productivity", view.research_productivity() == 0.8 and asked == ["other"], asked)
check("a foreign player reads the literacy of its own country's strata", abs(view.literacy("literacy_elite") - 0.6) < 1e-12, view.literacy("literacy_elite"))


# ---- the hours a project can call on
class Labour(TrainingMixin):
    def __init__(self, supply, contract, productivity):
        self.supply, self.productivity = supply, productivity
        self._world = SimpleNamespace(state=SimpleNamespace(household=SimpleNamespace(contract_hours={"scholar": contract})))

    def market_supply(self, trade):
        return self.supply

    def labour_productivity(self, trade):
        return self.productivity


check("the hours a project can call on are the market's supply and the contracted hours, times what an hour is worth",
      Labour(100.0, 20.0, 1.5).hours_you_can_call_on("scholar") == 180.0, None)
check("a more productive trade gives more hours from the same people", Labour(100.0, 0.0, 1.4).hours_you_can_call_on("scholar") > Labour(100.0, 0.0, 0.2).hours_you_can_call_on("scholar"), None)
