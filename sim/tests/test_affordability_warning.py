"""affordability_warning: the aggregate affordability warning's rule (`stacked_commitment`) and the parts of the funding
capacity (`funding_parts`), tested on built numbers. Three named scenarios run the Rome opening through `start`, `money`
and `available`, and the director's project start gate, in test_affordability_warning_scenario."""

QUICK_TOPIC = True
from .harness import *  # noqa: F401,F403

from sim.engine.project_funding import funding_parts
from sim.ui.proto.start_commitment import stacked_commitment

# --- the warning: only when several projects together owe more than the cash held
warned = stacked_commitment(644.0, 400.0, 2, lambda: 1500.0)
check("two projects owing more than the cash held are warned of, with the total, the cash and the draw on credit",
      warned == {"you_have_promised": 644.0, "across_projects_in_hand": 2, "you_currently_hold": 400.0,
                 "likely_to_draw_on_credit_between_them": 244.0, "your_real_ceiling_if_it_comes_to_that": 1500.0}, warned)
check("a single active project never gets the aggregate warning, however large: on_credit answers for it alone",
      stacked_commitment(5000.0, 400.0, 1, lambda: 1500.0) is None)
check("plenty of cash on hand: no aggregate warning even with several things started together",
      stacked_commitment(644.0, 1.0e6, 3, lambda: 1500.0) is None and stacked_commitment(644.0, 644.0, 3, lambda: 1.0) is None)
check("a household in arrears holds no cash, so what is owed is all drawn on credit",
      stacked_commitment(300.0, -50.0, 2, lambda: 10.0)["you_currently_hold"] == 0.0
      and stacked_commitment(300.0, -50.0, 2, lambda: 10.0)["likely_to_draw_on_credit_between_them"] == 300.0)
asked = []
stacked_commitment(100.0, 1000.0, 2, lambda: asked.append(1) or 5.0)
check("the ceiling is only worked out when there is a warning", asked == [])

# --- the funding capacity in parts: cash, the drawable credit, the surplus over the planning years
solvent = funding_parts(1000.0, 900.0, 600.0, 0.1, 400.0, 0.5, 5.0, 250.0)
check("cash held, half the credit line, and the planning years of the yearly surplus make up the funding capacity",
      solvent["cash_on_hand"] == 1000.0 and solvent["credit_available_now"] == 200.0
      and solvent["sustainable_annual_surplus"] == 300.0 and solvent["surplus_allowance_over_years"] == 1500.0
      and solvent["surplus_years_counted"] == 5.0 and solvent["already_committed"] == 250.0, solvent)
arrears = funding_parts(-100.0, 900.0, 600.0, 0.1, 400.0, 0.5, 5.0, 0.0)
check("arrears hold no cash, use up the room on the credit line, and their interest is a fixed cost that shrinks the surplus",
      arrears["cash_on_hand"] == 0.0 and arrears["credit_available_now"] == 100.0
      and abs(arrears["sustainable_annual_surplus"] - (900.0 - 610.0)) < 1e-9, arrears)
check("revenue short of fixed costs leaves no surplus, and arrears past the credit line leave no credit",
      funding_parts(1000.0, 500.0, 600.0, 0.1, 400.0, 0.5, 5.0, 0.0)["surplus_allowance_over_years"] == 0.0
      and funding_parts(-900.0, 0.0, 0.0, 0.1, 400.0, 0.5, 5.0, 0.0)["credit_available_now"] == 0.0)

