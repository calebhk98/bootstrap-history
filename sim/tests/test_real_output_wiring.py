"""Real output wired to the economy (Complaints 101, 112, 354, 640): the reporting module reads the economy's opening
basket (`Reporting.base_basket`), closes a year's output per head against it (`Reporting.close_real_output`), and the
society's output is that valued in money less the share under arms (`EconomyPort.output_value`,
`output_rules.share_producing`). The arithmetic is test_real_output_measure."""
QUICK_TOPIC = True

from types import SimpleNamespace

from .harness import check

from sim.engine.economy_port import EconomyPort
from sim.reporting.api import CloseRealOutput, ReportingWorld, output_rules
from sim.reporting.module import Reporting
from sim.tests import module_harness

OPENED = ({"grain": 100.0, "cloth": 20.0, "salt": 0.0, "pearl": 3.0}, {"grain": 2.0, "cloth": 5.0, "salt": 10.0, "pearl": 0.0})


def a_game(opened=OPENED, baseline=None, volumes=None, people=1.0, opening_people=1.0):
    """The reporting module over a world of its own, reading plain values for the economy's facts."""
    views = {"agent_opening_basket": lambda: opened, "agent_volume_baseline": lambda: baseline,
             "agent_traded_volumes": lambda: volumes, "new_goods_units": {}, "household_prices": {},
             "money_per_labour_hour": 1.0, "population_total": people, "opening_population": opening_people}
    return module_harness.build(Reporting, views=views, world=ReportingWorld())


# --- the opening basket is the economy's own, goods with a quantity and a price only
basket = a_game().base_basket()
check("the opening basket holds the goods households bought at a price, in sorted order",
      basket["units"] == {"cloth": 20.0, "grain": 100.0} and list(basket["units"]) == ["cloth", "grain"], basket)
check("...with the economy's own prices", basket["prices"] == OPENED[1], basket["prices"])
check("while the economy opens the basket is empty", a_game(opened=None).base_basket() == {"prices": {}, "units": {}})
cached_game = a_game()
first = cached_game.base_basket()
cached_game.needs.agent_opening_basket = lambda: None
check("the basket is read once and kept", cached_game.base_basket() is first)

# --- a closed year's output per head: output over the opening's, per head over the opening's
baseline = {"grain": 50.0, "cloth": 10.0}
game = a_game(baseline=baseline, volumes=dict(baseline))
game.close_real_output(CloseRealOutput())
check("the baseline year closes at one", abs(game.real_output_per_head() - 1.0) < 1e-12, game.real_output_per_head())
game = a_game(baseline=baseline, volumes={"grain": 100.0, "cloth": 20.0}, people=2.0, opening_people=2.0)
game.close_real_output(CloseRealOutput())
check("a year that clears twice the baseline volumes closes at two", abs(game.real_output_per_head() - 2.0) < 1e-12, game.real_output_per_head())
game = a_game(baseline=baseline, volumes={"grain": 50.0, "cloth": 10.0}, people=0.6, opening_people=1.0)
game.close_real_output(CloseRealOutput())
check("the same volumes among fewer people are more output per head", abs(game.real_output_per_head() - 1.0 / 0.6) < 1e-9, game.real_output_per_head())
game = a_game(baseline=baseline, volumes={"grain": 25.0, "cloth": 5.0}, people=0.5, opening_people=1.0)
game.close_real_output(CloseRealOutput())
check("a population that falls without a technique lowers output with the people and leaves it per head where it was",
      abs(game.real_output_hours() / game.opening_output_hours() - 0.5) < 1e-9 and abs(game.real_output_per_head() - 1.0) < 1e-9,
      (game.real_output_hours(), game.opening_output_hours(), game.real_output_per_head()))

# --- society output: real output in money, less the share under arms
port = SimpleNamespace(_sim=SimpleNamespace(real_output_hours=lambda: 40.0, labour=SimpleNamespace(money_per_labour_hour=lambda: 3.0),
                                            output_factor=0.5))
check("output value is the real output in labour hours, in this civilisation's money, times the output factor",
      EconomyPort.output_value(port) == 60.0, EconomyPort.output_value(port))
check("the share producing is the working people not under arms",
      output_rules.share_producing(1000.0, 250.0) == 0.75 and output_rules.share_producing(1000.0, 0.0) == 1.0)
check("...never below nothing when more are under arms than work", output_rules.share_producing(100.0, 400.0) == 0.0)
check("...and one when there are no working people to take", output_rules.share_producing(0.0, 0.0) == 1.0)
