"""Small screen items: Complaints/92 (hazard hedge timing), 93 (four funding concepts), 86 (knowledge apart from held
living stock). The timing rule is called on built hedges, the screens are rendered from replies built here (each such
check is presentation: what the screen prints), and the funding parts are test_affordability_warning. The
funding capacity, the fog rule for the stock a node brings and the order of the state screen's blocks are
test_funding_and_stock_rows_rules."""

QUICK_TOPIC = True

from .harness import check

from sim.hazards.hedge_timing import add_timing_to_steps, hedge_timing
from sim.ui.proto.render_screen_why import render_why
from sim.ui.proto.render_screens_economy import _money_funding_lines
from sim.ui.proto.render_screens_status import render_risk

# --- 92: every hedge with a calendar floor says whether it finishes before the window opens
early = hedge_timing(3.2, 100, 110, False)
check("a hedge's earliest finish is the calendar floor, rounded up, counted from the year now",
      early["earliest_finish_year"] == 104 and early["window_opens_year"] == 110, early)
check("finishing in a year before the window opens is in time", early["in_time_if_started_today"] is True, early)
check("finishing in the year the window opens is too late", hedge_timing(10.0, 100, 110, False)["in_time_if_started_today"] is False)
check("a window already open cannot be beaten, whatever the floor", hedge_timing(0.5, 100, 90, True)["in_time_if_started_today"] is False)
steps = [{"id": "timed", "years_even_if_you_start_today": 3.2}, {"id": "no_floor"}]
advice = {"build": {"you_could_begin_now_toward_it": steps}, "note": "not a dict of steps"}
add_timing_to_steps(advice, 100, 110, False)
check("only the steps that carry a calendar floor get a timing", "timing" in steps[0] and "timing" not in steps[1], steps)
risk = {"year": 100, "knowledge_risk": {"known_hazards_ahead": [
    {"name": "Sack", "years": [110, 120], "what_you_can_do": {"build": {"you_could_begin_now_toward_it": steps}}}]}}
# presentation: the risk screen prints the timing beside the hedge
check("the risk screen prints the timing beside the hedge", "window opens" in render_risk(risk), render_risk(risk)[:400])

# --- 93: money names cash, credit, surplus and what is owed apart
funding = {"cash_on_hand": 1000.0, "credit_available_now": 400.0, "sustainable_annual_surplus": 90.0,
           "surplus_years_counted": 5.0, "surplus_allowance_over_years": 450.0, "already_committed": 250.0}
shown = "\n".join(_money_funding_lines({"funding": funding, "you_could_actually_fund_up_to": 1850.0}))
# presentation: the money screen's labels
check("the money screen prints cash, credit, surplus and commitments on separate lines",
      all(any(line.strip().startswith(label) for line in shown.splitlines())
          for label in ("CASH ON HAND", "CREDIT AVAILABLE", "ANNUAL SURPLUS", "ALREADY COMMITTED")), shown)
check("a reply without funding prints no funding block", _money_funding_lines({}) == [])

# --- 86: what you know and what you hold are separate lines, and an unheld herd is a supply blocker
treadmill = {"id": "pwr_animal_treadmill", "name": "Animal treadmill",
             "living_stock": [{"material": "draught_animal_kg", "held": 0.0, "needed": 1000, "brought_by": "exp_import_draught_animals"}],
             "blockers": [{"kind": "supply", "text": "no draught animal stock held"}]}
shown_why = render_why(treadmill)
# presentation: the why screen's knowledge and held lines
check("the why screen prints knowledge and held animals as separate lines",
      any(line.startswith("KNOWLEDGE:") for line in shown_why.splitlines())
      and any(line.strip().startswith("HELD:") and "draught_animal_kg" in line for line in shown_why.splitlines()),
      shown_why[-600:])
check("the why screen names the node that brings the stock", "exp_import_draught_animals" in shown_why, shown_why[-300:])
