"""`PopulationMixin.population_report` gives one row per trade in the wage table and names the civilisation, on a stand-in `self`."""
QUICK_TOPIC = True

from types import SimpleNamespace

from .harness import check

from sim.labour.labour_population import PopulationMixin


class Labour(PopulationMixin):
    def __init__(self, wages):
        self._world = SimpleNamespace(civ={"id": "rome_100ad", "short_name": "Rome", "population": 1000.0},
                                      population=SimpleNamespace(total=900.0), urban_fraction=lambda: 0.2, wages=wages,
                                      plain_number=lambda number: "%d" % number)

    def home_town_population_estimate(self):
        return 100.0

    def national_trade_population(self, trade):
        return 50.0

    def reachable_trade_population(self, trade):
        return 5.0

    def trade_available(self, trade):
        return trade != "machinist"

    def employed(self, trade):
        return 1.0

    def _density_is_placeholder(self, trade):
        return False


report = Labour({"smith": 1.0, "mason": 1.0, "machinist": 1.0}).population_report()
check("the report names the civilisation", report["civilisation"] == "Rome", report["civilisation"])
check("every trade in the wage table gets a row, available here or not",
      [row["trade"] for row in report["trades"]] == ["machinist", "mason", "smith"], report["trades"])
check("a trade that cannot be had here has no reach", {row["trade"]: row["within_your_reach"] for row in report["trades"]}
      == {"machinist": 0.0, "mason": 5.0, "smith": 5.0}, report["trades"])
check("the share employed is the headcount over the reachable pool", report["trades"][2]["share_of_the_reachable_pool_you_employ"] == 0.2,
      report["trades"][2])
