"""One-line forwarders from the old `Sim` methods of the projects topic to the projects module's views and commands.

Callers outside the module (the screens, fog, the autostart rules, hazards, labour, ventures, the year's money phase) still
say `sim.can_start(node)` or `sim.close_work(node, reason)`; each line goes when its last caller reads the view or sends the
command itself."""
from sim.agents.api import business_review
from sim.projects.api import (BLOCKER_KINDS, AutoOpenVentures, Bribe, CloseLapsedDependents, CloseUnstaffedVentures, CloseWork,
                              CompleteProject, MothballWork, NoteVentureYear, PostBounty, ReopenRestaffedVentures, RestoreWork,
                              ReviewVentures, StartProject, StopProject, closure_reasons, constants)


class ProjectsForwardsMixin:

    BLOCKER_KINDS = BLOCKER_KINDS
    # numbers other topics' code, the screens and the tests still read off the game (sim/projects/constants.py declares them)
    vars().update({name: value for name, value in vars(constants).items() if name.isupper()})
    CLOSED_FOR_STAFF = closure_reasons.CLOSED_FOR_STAFF
    CLOSED_BY_CHOICE = closure_reasons.CLOSED_BY_CHOICE
    CLOSED_LOSS_MAKING = closure_reasons.CLOSED_LOSS_MAKING
    CLOSED_CREDITOR_SEIZURE = closure_reasons.CLOSED_CREDITOR_SEIZURE
    CLOSED_GATE_LAPSED = closure_reasons.CLOSED_GATE_LAPSED

    # ---- starting, stopping, buying ----

    def start_reason(self, node_id, ignore_trade=False, _memo=None, _why=True):
        return self.view("start_check")(node_id, ignore_trade, _memo, _why)

    def can_start(self, node_id, _memo=None):
        return self.view("start_check")(node_id, False, _memo, False)[0]

    def start_refusal(self, node_id, extra_owed=0.0):
        return self.view("start_refusal")(node_id, extra_owed)

    def start_blockers(self, node_id, extra_owed=0.0):
        return self.view("start_blockers")(node_id, extra_owed)

    def bounty_eligible(self, node_id):
        return self.view("bounty_eligible")(node_id)

    def start_project(self, node_id, precaution=False):
        return self.send(StartProject(node_id, precaution))

    def stop_project(self, node_id):
        return self.send(StopProject(node_id))

    def post_bounty(self, node_id):
        return self.send(PostBounty(node_id))

    def bribe(self, amount):
        return self.send(Bribe(amount))

    def _visible_to_player(self, node_id):
        return self.view("visible_to_player")(node_id)

    @property
    def materials_paid_at_last_start(self):
        return self.view("last_start")()

    # ---- risk, calendar and cost ----

    def calendar_floor(self, node_id):
        return self.view("calendar_floor")(node_id)

    def effective_risk(self, node_id, precaution=None):
        return self.view("effective_risk")(node_id, precaution)

    def payment_schedule_years(self, node_id):
        return self.view("payment_schedule_years")(node_id)

    def earliest_completion_years(self, node_id):
        return self.view("earliest_completion_years")(node_id)

    def expected_calendar_years(self, node_id):
        return self.view("expected_calendar_years")(node_id)

    def precaution_quote(self, node_id):
        return self.view("precaution_quote")(node_id)

    def reputation_gain_of(self, node_id):
        return self.view("reputation_gain_of")(node_id)

    def rebuild_work_factor(self, node_id):
        return self.view("rebuild_work_factor")(node_id)

    def rebuild_explanation(self, node_id):
        return self.view("rebuild_explanation")(node_id)

    def rebuild_retained_share(self, node_id):
        return self.view("rebuild_retained_share")(node_id)

    # ---- hours and trades ----

    def project_hour_pace(self, node_id):
        return self.view("project_hour_pace")(node_id)

    def project_useful_hours(self, node_id):
        return self.view("project_useful_hours")(node_id)

    def active_hours_still_wanted(self):
        return self.view("active_hours_still_wanted")()

    def hour_priority_queue(self):
        return self.view("hour_priority_queue")()

    def hour_standing(self, node_id):
        return self.view("hour_standing")(node_id)

    def trade_demand_vs_supply(self):
        return self.view("trade_demand_vs_supply")()

    def trade_draw_plan(self, node_id, lab_left=None):
        return self.view("trade_draw_plan")(node_id, lab_left)

    def trade_shortage_kind(self, trade_id, need, total_demand=None):
        return self.view("trade_shortage_kind")(trade_id, need, total_demand)

    def trades_the_project_waits_for(self, node_id):
        return self.view("trades_the_project_waits_for")(node_id)

    # ---- the goal and what finishing does ----

    def goal_snapshot(self):
        return self.view("goal_snapshot")()

    def opening_shortfall(self, node_id):
        return self.view("opening_shortfall")(node_id)

    def _complete(self, node_id):
        self.send(CompleteProject(node_id))

    # ---- exclusions, gates and closures ----

    def exclusion_reason(self, node_id):
        return self.view("exclusion_reason")[node_id]

    def exclusion_entry_known(self, entry):
        return self.view("exclusion_entry_known")(entry)

    def relied_on_running(self, node_id):
        return self.view("relied_on_running")[node_id]

    def gate_blocked(self, node_id):
        return self.view("gate_blocked")(node_id)

    def open_refusal(self, node_id, unit_count=None, with_advice=True):
        return self.view("open_refusal")(node_id, unit_count, with_advice)

    def staffing_open_refusal(self, node_id, unit_count=1.0, with_advice=True):
        return self.view("staffing_open_refusal")(node_id, unit_count, with_advice)

    def staff_closure_age(self, node_id):
        return self.view("staff_closure_age")[node_id]

    def close_work(self, node_id, reason, year=None, cascade=True):
        self.send(CloseWork(node_id, reason, year, cascade))

    def close_lapsed_dependents(self, year):
        return self.send(CloseLapsedDependents(year))

    # ---- the staffing rule and the works built ----

    def concerns_to_close_for_staffing(self):
        return self.view("concerns_to_close_for_staffing")()

    def staffing_held_totals(self):
        return self.view("staffing_held_totals")()

    def staffing_missing_to_open(self, node_id, held_totals=None):
        return self.view("staffing_missing_to_open")(node_id, held_totals)

    def staffing_closure_summary(self):
        return self.view("staffing_closure_summary")()

    def staffing_closure_warnings(self, limit=3):
        return self.view("staffing_closure_warnings")(limit)

    def close_unstaffed_ventures(self, year):
        return self.send(CloseUnstaffedVentures(year))

    def reopen_restaffed_ventures(self, year):
        return self.send(ReopenRestaffedVentures(year))

    def auto_open_ventures(self):
        return self.send(AutoOpenVentures())

    def note_venture_year(self):
        self.send(NoteVentureYear())

    def review_ventures(self, rules=business_review.ALL_RULES, year=None):
        return self.send(ReviewVentures(tuple(rules), year))

    def mothball_work(self, node_id):
        return self.send(MothballWork(node_id))

    def restore_work(self, node_id):
        return self.send(RestoreWork(node_id))
