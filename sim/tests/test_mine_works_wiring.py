"""The mining methods that compose figures from a working: the ceiling bound on opening, the running cost of a working, what a quote
states and what closing refunds. Called on the stand-in founder of test_mine_names_a_deposit with the collaborators' figures written
out; the works technology that sets the hours per tonne is test_mine_techniques."""
from .harness import *  # noqa: F401,F403
from sim.reporting.api import RecordEvent
from sim.resources.api import CloseMine
from sim.tests import module_harness
from sim.tests.test_mine_names_a_deposit import _Host

QUICK_TOPIC = True
UNDER_TEST = {"open_mine"}

NO_DEPOSIT_MATERIAL = "aluminium_kg"   # no deposit data: bounded by the ceiling alone


class _Mining(_Host):
    """A founder with a written-out ceiling, capex and opex per tonne a year, and a working's depletion scale."""

    def __init__(self, ceiling=40.0, opex=2.0, scale=1.0):
        super().__init__()
        module = self.module
        module.mine_land_ceiling = lambda material: ceiling
        module.mine_opex = lambda material: opex
        module.capex_opex = lambda material: (10.0, opex)
        module.cost_scale_of = lambda working: scale
        module.cost_scale_for_material = lambda material: scale
        self.price_index = 1.0


# --- open_mine delivers only the room under the ceiling.
host = _Mining(ceiling=40.0)
check("asking for far more than the ceiling allows opens only the ceiling", host.open_mine(NO_DEPOSIT_MATERIAL, 5000.0, partial=False) == 40.0)
on_order = _Mining(ceiling=40.0)
on_order.holdings.mine_pending = {NO_DEPOSIT_MATERIAL: 40.0}
check("what is on order counts against the ceiling, so an ask with the ceiling on order opens nothing",
      on_order.open_mine(NO_DEPOSIT_MATERIAL, 5000.0, partial=False) == 0.0)
check("a ceiling of nothing opens nothing", _Mining(ceiling=0.0).open_mine(NO_DEPOSIT_MATERIAL, 5.0) == 0.0)

# --- a working's running cost is capacity times the material's opex times the price index times its own depletion scale.
working = {"material": "coal", "capacity": 10.0, "intensity_yrs": 0.0}
cheap_works, dear_works = _Mining(opex=1.0), _Mining(opex=2.0)
check("a working costs capacity times opex per tonne times the price index times its scale",
      dear_works.module.operating_cost_of(working) == 10.0 * 2.0 * dear_works.price_index * 1.0)
check("works that need fewer hours per tonne (a lower opex) lower the running cost of the same working",
      cheap_works.module.operating_cost_of(working) < dear_works.module.operating_cost_of(working))
worn = _Mining(opex=2.0, scale=1.5)
check("a depleted working costs its depletion scale times more", worn.module.operating_cost_of(working) == 1.5 * dear_works.module.operating_cost_of(working))

# --- the quote states the ceiling, the room left and the yield fraction.
quoting = _Mining(ceiling=40.0)
quoting.module.mine_depletion = lambda material: 0.8
quoted = quoting.module.mine_quote(NO_DEPOSIT_MATERIAL, 10.0)
check("a quote names the ground's ceiling and the room left under it",
      quoted["the_ground_here_could_ever_support"] == 40.0 and quoted["room_left_before_geology_stops_you"] == 40.0, quoted)
check("a quote states the share of day-one yield the workings have left", quoted["current_yield_is_this_fraction_of_day_one"] == 0.8, quoted)
check("a quote's price to sink is tonnes times capex times the price index times the scale",
      quoted["to_sink_it"] == round(10.0 * 10.0 * quoting.price_index * 1.0, 1), quoted)
check("a quote's yearly cost is what a new working of that size is charged",
      quoted["every_year_it_stands"] == round(quoting.module.operating_cost_of(
          {"material": NO_DEPOSIT_MATERIAL, "capacity": 10.0, "intensity_yrs": 0.0}), 1), quoted)
quoting.holdings.mine_pending = {NO_DEPOSIT_MATERIAL: 15.0}
check("a quote's room is what the ceiling leaves after what is on order",
      quoting.module.mine_quote(NO_DEPOSIT_MATERIAL, 10.0)["room_left_before_geology_stops_you"] == 25.0)

# --- closing a material refunds the sum of each working's own running cost.
closing = _Mining(opex=2.0)
closing.holdings.mines.extend([
    {"material": "coal", "capacity": 10.0, "opened_year": 1, "capex_paid": 0.0, "intensity_yrs": 0.0},
    {"material": "coal", "capacity": 5.0, "opened_year": 2, "capex_paid": 0.0, "intensity_yrs": 0.0},
    {"material": "tin", "capacity": 7.0, "opened_year": 2, "capex_paid": 0.0, "intensity_yrs": 0.0}])
expected_saving = (10.0 + 5.0) * 2.0 * closing.price_index   # coal capacity times opex per tonne times the price index
closed = closing.module.close_mine(CloseMine("coal"))
closing_line = [command for command in module_harness.sent(closing.module) if isinstance(command, RecordEvent)][-1]
check("closing a material saves the sum of its workings' own running costs",
      closed and closing_line.kind == "workings_closed" and closing_line.facts["saved_per_year"] == expected_saving
      and closing_line.facts["material"] == "coal", closing_line.facts)
check("...and every working of that material is gone while another material's stays",
      [row["material"] for row in closing.holdings.mines] == ["tin"], closing.holdings.mines)

# --- capacity by material is listed in the order the workings stand, not by anything a hash seed decides.
ordered = _Mining()
ordered.holdings.mines.extend([{"material": name, "capacity": 1.0, "opened_year": 1, "capex_paid": 0.0, "intensity_yrs": 0.0}
                               for name in ("tin", "coal", "iron", "coal", "copper")])
check("mine_capacity lists materials in the order their first working stands", list(ordered.module.mine_capacity()) == ["tin", "coal", "iron", "copper"],
      list(ordered.module.mine_capacity()))
