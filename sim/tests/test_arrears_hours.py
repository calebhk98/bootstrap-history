"""arrears_hours: a household in arrears must not lose the hours of a project that owes nothing further (Complaint:
"in arrears freezes ALL founder-hour progress even on fully-paid projects"), and a concern shut on purpose must
never reappear on its own. The rules are tested on built inputs (`project_funding`, `business_review.reopen`);
the afford gate that runs the first is in test_arrears_wiring (what the yearly reopening does with
the plants brought back is in test_reopen_restaffed_wiring)."""
QUICK_TOPIC = True

from .harness import check

from sim.agents import business_review
from sim.agents.api import Business
from sim.projects.api import funding as project_funding

# --- the purse a project may draw on
check("the purse is capital and part of the credit line, less the shortfall of fixed costs over revenue",
      abs(project_funding.project_purse(1000.0, 500.0, 900.0, 400.0)
          - (1000.0 + 500.0 * project_funding.CREDIT_DRAW_SHARE - 500.0)) < 1e-9)
check("revenue that covers the fixed costs reserves nothing",
      project_funding.project_purse(1000.0, 0.0, 300.0, 400.0) == 1000.0)

# --- the year's funding of one project
nothing_owed = project_funding.fund_year(0.0, -5000.0, 400.0, 0.0, 500.0, True)
check("a project that owes nothing further is paid whole and keeps its hours, however deep the household's arrears",
      nothing_owed.money == 0.0 and nothing_owed.gave_back == 0.0 and nothing_owed.refunded == 0.0, nothing_owed)
check("...and it is not marked underfunded, because nothing was short", not nothing_owed.underfunded and nothing_owed.why is None)
covered = project_funding.fund_year(300.0, 300.0, 400.0, 0.0, 500.0, False)
check("a bill the purse covers is paid whole with no hours given back",
      covered.money == 300.0 and covered.gave_back == 0.0 and not covered.underfunded, covered)
half = project_funding.fund_year(400.0, 200.0, 500.0, 0.0, 500.0, False)
check("a bill beyond the purse is paid what the purse holds and gives back the hours of the unfunded part",
      half.money == 200.0 and half.gave_back == 250.0 and half.underfunded and half.refunded == 250.0, half)
broke = project_funding.fund_year(400.0, -100.0, 500.0, 0.0, 500.0, True)
check("a purse gone negative pays the project nothing and gives back every hour offered, but no more than was taken",
      broke.money == 0.0 and broke.gave_back == 500.0
      and project_funding.fund_year(400.0, -100.0, 300.0, 0.0, 500.0, True).gave_back == 300.0, broke)
check("hours already handed back by the trade shortage are not handed back twice",
      project_funding.fund_year(400.0, 0.0, 500.0, 400.0, 500.0, False).gave_back == 100.0
      and project_funding.fund_year(400.0, 0.0, 500.0, 500.0, 500.0, False).gave_back == 0.0)
check("the cause given is arrears when the household is in arrears, the instalment otherwise",
      broke.why == project_funding.WHY_IN_ARREARS and half.why == project_funding.WHY_INSTALMENT)
check("only hours lost while in arrears, and worth noticing, are reported as lost to arrears",
      broke.hours_lost_to_arrears == 500.0 and half.hours_lost_to_arrears == 0.0
      and project_funding.fund_year(400.0, 399.5, 500.0, 0.0, 500.0, True).hours_lost_to_arrears == 0.0)

# --- a concern shut on purpose is never reopened by the staffing rule
class Owner(business_review.Reviewable):
    """An owner that can staff anything."""

    def __init__(self, business):
        self.business = business

    def reopens_staffed_plant(self, entry_key, world):
        return True


plants = Business.running(["short_of_staff", "shut_by_player", "running"], opened_year=0)
plants.mothball("short_of_staff", 5, business_review.STAFF_SHORT)
plants.mothball("shut_by_player", 5, "player")
check("only the plants the staffing rule shut come back, and only when the owner can staff them; one shut on purpose never does",
      business_review.reopen(plants, Owner(plants), None) == ["short_of_staff"], business_review.reopen(plants, Owner(plants), None))
