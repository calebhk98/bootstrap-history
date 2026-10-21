"""Serving out a debt and the workshop's output (Complaint 640): the arithmetic called on values built here, no game."""
QUICK_TOPIC = True

from .harness import *  # noqa: F401,F403
from sim.engine.bondage_workshop_rules import (bondage_repayment, serve_bondage_year, workshop_craft_wages,
                                               workshop_output_value)

# --- a year of bondage
repayment = bondage_repayment(2000.0, 0.8, 1.25, 0.5)
check("a year repays the creditor's share of the debtor's hours at the labourer hour and the markup",
      abs(repayment - 2000.0 * 0.8 * 1.25 * 0.5) < 1e-9, repayment)
check("a dearer labourer hour repays more of the debt", bondage_repayment(2000.0, 0.8, 1.25, 0.6) > repayment)
check("a larger share of the hours repays more of the debt", bondage_repayment(2000.0, 0.9, 1.25, 0.5) > repayment)
check("a year of bondage takes a year off the term and the repayment off the debt",
      serve_bondage_year(5, 10_000.0, 1000.0) == (4, 9000.0, False))
check("a term that runs out discharges the debt that is left and ends the service",
      serve_bondage_year(1, 10_000.0, 1000.0) == (0.0, 0.0, True))
check("a debt repaid early ends the term and the service",
      serve_bondage_year(5, 800.0, 1000.0) == (0.0, 0.0, True))
check("a debt exactly repaid ends the term", serve_bondage_year(5, 1000.0, 1000.0) == (0.0, 0.0, True))
check("a debt is never taken below nothing", serve_bondage_year(5, 10.0, 1000.0)[1] == 0.0)
check("a debt still owing with years left is not discharged", serve_bondage_year(3, 5000.0, 1000.0)[2] is False)

# --- the workshop
QUOTES = {"smith": 100.0, "carpenter": 80.0, "scholar": 300.0, "artisan": 60.0}


def is_craft(trade):
    return trade != "scholar"


check("the craft staff draw their trades' own annual wages",
      workshop_craft_wages({"smith": 2.0, "carpenter": 1.0}, is_craft, QUOTES.get, 0.0, QUOTES["artisan"]) == 280.0)
check("a scholar on the books is not a craft hand",
      workshop_craft_wages({"smith": 2.0, "scholar": 5.0}, is_craft, QUOTES.get, 0.0, QUOTES["artisan"]) == 200.0)
check("the freed and enslaved count at the artisan wage in proportion to the workers they are worth",
      workshop_craft_wages({}, is_craft, QUOTES.get, 3.5, QUOTES["artisan"]) == 210.0)
check("no staff, no wages", workshop_craft_wages({}, is_craft, QUOTES.get, 0.0, QUOTES["artisan"]) == 0.0)
check("a dearer trade quote raises the wages",
      workshop_craft_wages({"smith": 2.0}, is_craft, lambda trade: 150.0, 0.0, 60.0) > 200.0)
check("the workshop values its staff at their wages times the markup and the capability factor",
      abs(workshop_output_value(280.0, 1.55, 1.2) - 280.0 * 1.55 * 1.2) < 1e-9)
check("a workshop with no staff produces nothing, however capable", workshop_output_value(0.0, 1.55, 3.0) == 0.0)
check("a more capable society makes the same hands produce more",
      workshop_output_value(280.0, 1.55, 1.4) > workshop_output_value(280.0, 1.55, 1.2))
check("the output scales with the market wage so cost factors in the wage carry through unchanged as a ratio",
      abs(workshop_output_value(2 * 280.0, 1.55, 1.2) / workshop_output_value(280.0, 1.55, 1.2) - 2.0) < 1e-12)
