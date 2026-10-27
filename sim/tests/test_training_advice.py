"""The figures a trade-shortage refusal quotes for teaching a trade are the labour market's own."""

QUICK_TOPIC = True

from .harness import check

from sim.tests import module_harness
from sim.workforce.module import Workforce


class FakeLabour:
    def __init__(self, source):
        self.source = source

    def _source_trade_for(self, trade_id):
        return self.source

    def training_hours_per_person(self, trade_id, source):
        return 400.0 if source == "smith" else -1.0

    def training_years_from(self, trade_id, source):
        return 3.5 if source == "smith" else -1.0


def training_advice(labour, trade_id):
    """The workforce module's `training_advice` over this labour market."""
    module = module_harness.build(Workforce)
    module.labour = labour
    return module.training_advice(trade_id)


taught = training_advice(FakeLabour("smith"), "engineer")
check("the advice carries the labour market's hours and years for the trade",
      taught == {"trade": "engineer", "source_trade": "smith", "hours_each": 400.0, "years": 3.5}, taught)

untaught = training_advice(FakeLabour(None), "engineer")
check("with no trade to teach it from, the advice carries no hours or years",
      untaught["source_trade"] is None and untaught["hours_each"] is None and untaught["years"] is None, untaught)
