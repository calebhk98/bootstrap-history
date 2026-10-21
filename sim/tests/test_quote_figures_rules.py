"""The two figures every screen quotes (Complaint 640): the cost of a project started today and the yearly running cost of a
concern, called on numbers built here. The same figures through the dispatcher are test_start_and_upkeep_quotes_scenario."""
QUICK_TOPIC = True

from .harness import check
from sim.engine.quote_figures import cost_if_started_now, upkeep_quote

check("a project costs labour and capital plus the missing materials",
      cost_if_started_now(1000.0, 250.0, 1.0, 1.0) == 1250.0)
check("the geography factor and the opposition factor each scale the whole bill",
      cost_if_started_now(1000.0, 250.0, 1.2, 1.5) == 1250.0 * 1.2 * 1.5)
check("materials already held cost nothing more", cost_if_started_now(1000.0, 0.0, 1.0, 1.0) == 1000.0)

quote = upkeep_quote(400.0, 600.0, 1.5)
check("the running cost is quoted at the price level, as staffed and at full staffing",
      quote == {"now": 600.0, "at_full_staffing": 900.0}, quote)
check("an ordinary concern costs the same staffed or not", upkeep_quote(400.0, 400.0, 2.0)["now"] == 800.0
      and upkeep_quote(400.0, 400.0, 2.0)["at_full_staffing"] == 800.0)
