"""mine_stock_accounting: complaint 148, the mines screen columns (Complaint 640: rows built from stub workings, no game;
the banked stock through a game year is test_mine_stock_accounting_scenario)."""
import types

from .harness import check
from sim.ui.proto.economy import _mine_rows_for_material

QUICK_TOPIC = True


class _Founder:
    """Only what a mines row reads of a game: the working's yield, cost and note."""

    def __init__(self, yield_per_capacity):
        self._factor = yield_per_capacity

    def mine_yield_t_for(self, working):
        return self._factor * working["capacity"]

    def mine_operating_cost_for(self, working):
        return 0.0

    def mine_depletion_note_for(self, working):
        return ""


def _rows(factor, workings, want):
    return _mine_rows_for_material(_Founder(factor), "galena_kg", workings, want)


row = _rows(2.0, [{"capacity": 280.0, "opened_year": 1}], 100.0)[0]
check("ACTUAL can exceed RATED once technology raises the yield",
      row["actual_output_t_per_yr"] == 2 * row["rated_capacity_t_per_yr"], row)
# presentation: the utilisation column is a percentage string
check("UTIL is the share of ACTUAL that demand draws (100 t of 560 t is 18%), never above 100%",
      row["utilization"] == "18%", row["utilization"])
check("a working that demand draws on is flagged as supplying", row["actually_supplying_demand"] is True, row)

drawn_all = _rows(1.0, [{"capacity": 50.0, "opened_year": 1}], 500.0)[0]
# presentation: the utilisation column is a percentage string
check("demand beyond what a working raises is capped at 100%", drawn_all["utilization"] == "100%", drawn_all)

idle = _rows(1.0, [{"capacity": 50.0, "opened_year": 1}], 0.0)[0]
check("a working nothing draws on is not supplying", idle["actually_supplying_demand"] is False, idle)

two = _rows(1.0, [{"capacity": 100.0, "opened_year": 5}, {"capacity": 300.0, "opened_year": 2}], 40.0)
check("every working of a material carries the material demand, ordered by commissioning year",
      abs(two[0]["material_demand_t_per_yr"] - 40.0) < 1e-9 and [row["rated_capacity_t_per_yr"] for row in two] == [300.0, 100.0],
      two)
check("workings read as a chronology, oldest first", [row["commissioned_year"] for row in two] == [2, 5], two)
dead = _rows(0.0, [{"capacity": 50.0, "opened_year": 1}], 10.0)[0]
# presentation: a working that raises nothing shows a dash
check("a working that raises nothing shows no utilisation and supplies nothing",
      dead["utilization"] == "-" and dead["actually_supplying_demand"] is False, dead)
