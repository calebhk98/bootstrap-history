"""What finishing a piece of work actually does.

_complete() is the single largest method in projects.py's original file
(see that file's own docstring for why this lives separately) - what a
finished (or, on the risk roll, a failed) attempt does to `done`, tech
effects, standing, scandal, state interest, and the staff a handful of
institutions grant on completion. The HAZARD_COUNTERS table that follows it
in the class body is a distinct but related subject: it is not read by
_complete() itself, but by society_hazards.py's `_shocks` (self.HAZARD_
COUNTERS - see that file), and it lists exactly the completed technologies
that blunt a hazard's effect, so it belongs beside the other consequence of
having finished something rather than in any of this split's other files.

These are methods of Sim; they are a mixin only so that they can live in a
file of their own.
"""
from sim.constants import declare
from .data import closure
from .failure_cause import failure_cause

FAILED_PREFIX = "FAILED at"
MINOR_MARK = "(minor)"

# What a goal measure is called and how it is shown; unknown metrics print raw.
_FRACTION_METRICS = frozenset(("literacy_general", "literacy_elite", "epidemic_relief"))
_GOAL_DETERMINANTS = {
    "literacy_general": (("literacy ceiling", "literacy_ceiling_general"),),
    "literacy_elite": (("elite literacy ceiling", "literacy_ceiling_elite"),),
}


def format_goal_value(value, is_fraction):
    return "%.1f%%" % (value * 100.0) if is_fraction else "%.3g" % value


def goal_movement(before, after):
    """(label, before text, after text) for each goal measure that moved
    between two goal_snapshot() results, plus the road steps gained."""
    if not before or not after:
        return [], 0
    moved = []
    for label, (old_value, is_fraction) in before["measures"].items():
        new_value = after["measures"].get(label, (old_value, is_fraction))[0]
        if abs(new_value - old_value) > 1e-9:
            moved.append((label, format_goal_value(old_value, is_fraction),
                          format_goal_value(new_value, is_fraction)))
    return moved, after["road_done"] - before["road_done"]


class CompletionMixin:
    MINOR_FAILURE_SHARE = declare(
        "MINOR_FAILURE_SHARE", 0.05, kind="temporary_heuristic",
        unit="fraction of funding capacity", source=None, confidence="D",
        why="A failed attempt that costs less than this share of what the "
            "player could fund is reported as one compact line; only the "
            "presentation depends on it, not the loss itself.")
    GOAL_PATH_FAILURE_WEIGHT = declare(
        "GOAL_PATH_FAILURE_WEIGHT", 2.0, kind="temporary_heuristic",
        unit="multiplier on the loss share", source=None, confidence="D",
        why="A failure on the goal's own prerequisite road blocks the goal, "
            "so its loss counts for more when deciding how loudly to say "
            "it. Presentation only.")

    def goal_closure_ids(self):
        """Every node the current goal needs, cached per goal."""
        cache = self.__dict__.setdefault("_goal_closure_by_goal", {})
        if self.goal not in cache:
            try:
                cache[self.goal] = set(closure(self.nodes, self.goal))
            except Exception:
                cache[self.goal] = set()
        return cache[self.goal]

    def failure_severity(self, node_id, lost, means):
        """'minor' or 'major', from the loss against the player's means and
        whether the failed project sits on the goal's road."""
        weight = self.GOAL_PATH_FAILURE_WEIGHT if node_id in self.goal_closure_ids() else 1.0
        return "minor" if lost * weight < self.MINOR_FAILURE_SHARE * max(means, 1.0) else "major"

    def goal_snapshot(self):
        """The goal's live measure(s) and road progress, or None without a goal."""
        goal = self.goal
        if goal not in self.nodes:
            return None
        road = self.goal_closure_ids()
        measures = {}
        condition = self.nodes[goal].get("win_condition")
        if condition and goal not in self.state.projects.done:
            try:
                metric = condition.get("metric") or "goal measure"
                fraction = metric in _FRACTION_METRICS
                measures[metric.replace("_", " ")] = (self._win_condition_value(condition), fraction)
                for label, getter in _GOAL_DETERMINANTS.get(metric, ()):
                    measures[label] = (float(getattr(self, getter)()), True)
            except (ValueError, AttributeError):
                pass
        return {"measures": measures,
                "road_done": len(road & self.state.projects.done),
                "road_total": len(road)}

    def goal_effect_lines(self, node_id, before):
        """Log lines saying how finishing `node_id` moved the goal."""
        after = self.goal_snapshot()
        moved, _gained = goal_movement(before, after)
        lines = ["goal effect: %s %s -> %s" % row for row in moved]
        if (before and node_id != self.goal and node_id in self.goal_closure_ids()
                and self.goal not in self.state.projects.done):
            if self.fog:
                lines.append("goal effect: this is on the road to your goal")
            else:
                lines.append("goal effect: on the road to your goal, %d of %d steps done"
                             % (after["road_done"], after["road_total"]))
        return lines

    def opening_shortfall(self, node_id):
        """(need scholars, need craftsmen, free scholars, free craftsmen) when
        today's free staff could not supervise this concern, else None."""
        need_scholars, need_craftsmen = self.venture_hands(node_id)
        free_scholars, free_craftsmen = self.venture_staff_free()
        if need_scholars > free_scholars + 0.01 or need_craftsmen > free_craftsmen + 0.01:
            return need_scholars, need_craftsmen, free_scholars, free_craftsmen
        return None

    FAILURE_RESET_SHARE = declare(
        "FAILURE_RESET_SHARE", 0.4, kind="temporary_heuristic",
        unit="fraction of founder-hours and of total cost", source=None,
        confidence="D",
        why="What a failed attempt costs and leaves still to do: forty "
            "per cent of the node's founder-hours are to do again, and "
            "forty per cent of its total cost (money-scaled) is lost - "
            "the SAME figure used for both, and used again to build the "
            "log message's own '%d%%' so the number cannot drift from "
            "what the arithmetic actually charges (see this method's own "
            "comment on the '40, NOT 60' bug, where the message once said "
            "sixty while the code charged forty). Tuned penalty, not "
            "measured against any real cost of a failed technical "
            "programme.")
    REPUTATION_GAIN_BASE = declare(
        "REPUTATION_GAIN_BASE", 0.6, kind="temporary_heuristic",
        unit="reputation points, per completed technology", source=None,
        confidence="D",
        why="The baseline standing any completed technology earns, before "
            "state interest or visible revenue add anything further. "
            "Tuned game balance, not measured.")
    REPUTATION_GAIN_STATE_INTEREST_COEFFICIENT = declare(
        "REPUTATION_GAIN_STATE_INTEREST_COEFFICIENT", 0.5, kind="temporary_heuristic",
        unit="reputation points per point of positive state_interest",
        source=None, confidence="D",
        why="How much extra standing a technology the state actually "
            "welcomes earns, on top of REPUTATION_GAIN_BASE - only the "
            "positive side of state_interest counts here (state "
            "opposition is priced elsewhere, in start_reason's own "
            "gates, not by shrinking a reward). Tuned, not measured.")
    REPUTATION_GAIN_REVENUE_BONUS = declare(
        "REPUTATION_GAIN_REVENUE_BONUS", 1.2, kind="temporary_heuristic",
        unit="reputation points, if the node earns any revenue",
        source=None, confidence="D",
        why="Visible, useful, revenue-earning work builds standing faster "
            "than obscure laboratory work of equal difficulty - a real "
            "and annoying fact about how credibility accrues (this "
            "method's own comment), captured here as a flat bonus rather "
            "than a function of the revenue's actual size. Tuned, not "
            "measured.")
    REPUTATION_CEILING = declare(
        "REPUTATION_CEILING", 100.0, kind="temporary_heuristic",
        unit="reputation points", source=None, confidence="D",
        why="The top of the reputation scale this engine uses throughout "
            "(REPUTATION_EASE_SCALE in economy.py reads reputation "
            "against this same implicit ceiling). A scale choice, not a "
            "measured social fact.")

    def _complete(self, node_id):
        node = self.nodes[node_id]
        projects = self.state.projects
        household = self.state.household
        scenario = self.state.scenario
        governance = self.state.governance
        _risk_this_attempt = self.effective_risk(node_id)
        if self.rng.random() < _risk_this_attempt:
            _yrs_before = projects.active[node_id]["yrs"]
            projects.failed_attempts[node_id] += 1
            claimed = node_id in projects.bountied
            # A bounty's claimant redoes the work: the poster's prize holds and
            # no hours or money fall on the poster.
            projects.active[node_id]["ph_left"] = (
                0.0 if claimed else
                node["ph"] * self.rebuild_work_factor(node_id) * self.FAILURE_RESET_SHARE)
            # THE CALENDAR CLOCK IS NOT WIPED: a failed attempt must not
            # reset the multi-year diffusion clock to zero, restarting the
            # whole process from nothing. Even ONE failed attempt already
            # does real social groundwork (workshops retooled, a workforce
            # that has seen it once, a regulator who already sat through
            # the pitch), so the first failure already banks a real share
            # of the elapsed clock, not zero - it is the risk term above,
            # not this one, that has nothing to show after only one
            # failure. What this banks keeps growing, with diminishing
            # returns, as failed_attempts[node_id] grows, and is capped well
            # short of the whole clock (RETRY_CALENDAR_CAP) so a retried
            # programme is only ever readier, never instantly ready.
            _retain = self._retry_calendar_retain(node_id)
            projects.active[node_id]["yrs"] = _yrs_before * _retain
            _lost = 0.0 if claimed else self.failure_loss(node_id)
            _severity = self.failure_severity(node_id, max(0.0, _lost), self.funding_capacity())
            household.capital -= _lost
            # A failure always announces itself; its size sets how loudly.
            _next_risk = self.effective_risk(node_id)
            _banked = projects.active[node_id]["yrs"]
            if claimed:
                household.log.append((scenario.year,
                    "%s %s: the claimant's attempt failed. The prize you posted holds "
                    "and they try again (attempt %d, chance of failing %d%%); nothing "
                    "more falls on you."
                    % (FAILED_PREFIX, node["name"],
                       projects.failed_attempts[node_id] + 1, round(_next_risk * 100))))
                return
            if _severity == "minor":
                household.log.append((scenario.year,
                    "%s %s %s: lost %s denarii, %d%% of the hours to redo; "
                    "attempt %d, next attempt's live chance of failing %d%%."
                    % (FAILED_PREFIX, node["name"], MINOR_MARK,
                       "{:,.0f}".format(max(0.0, _lost)),
                       round(self.FAILURE_RESET_SHARE * 100),
                       projects.failed_attempts[node_id] + 1,
                       round(_next_risk * 100))))
                return
            household.log.append((scenario.year,
                             FAILED_PREFIX + " %s: it did not work. What failed: %s. "
                             "%d%% of the hours "
                             "are to do again (%s of your own) and %s is gone. "
                             "Attempt %d. What went wrong is now understood well "
                             "enough that the next attempt's live chance of failing "
                             "(the figure `risk`, `why` and `portfolio` now quote) "
                             "is %d%%, down from the %d%% this attempt "
                             "just faced, and %.1f of the %.1f years already "
                             "spent count toward next time's wait."
                             % (node["name"], failure_cause(self, node_id),
                                round(self.FAILURE_RESET_SHARE * 100),
                                "{:,.0f}".format(node["ph"] * self.FAILURE_RESET_SHARE),
                                "{:,.0f}".format(max(0.0, _lost)),
                                projects.failed_attempts[node_id] + 1,
                                round(_next_risk * 100),
                                round(_risk_this_attempt * 100),
                                _banked, _yrs_before)))
            return
        goal_before = self.goal_snapshot()
        del projects.active[node_id]
        projects.bountied.discard(node_id)
        # A FINISHED PROJECT CANNOT BE GIVEN MORE HOURS. Unlike stopping or
        # halting one - both of which carry what was already paid forward
        # if the player starts the same id again, see start_project's own
        # `_paid_now` - there is no "again" once it is done, so a standing
        # order aimed at this id would otherwise sit in `allocate`'s list
        # for ever, pointed at nothing.
        household.hour_allocations.pop(node_id, None)
        projects.done.add(node_id)
        self._done_changed()
        if projects.done_year is None:
            projects.done_year = {}
        projects.done_year[node_id] = scenario.year
        # A technology changes the society that built it. Only for work YOU
        # completed: a society is not altered by owning something it always had.
        self.apply_tech_effects(node_id)
        self.reveal_from(node_id)
        # Visible, useful, State-approved work builds standing. Obscure laboratory
        # work does not, however important it is, which is a real and annoying fact
        # about how credibility actually accrues.
        gain = (self.REPUTATION_GAIN_BASE
                + self.REPUTATION_GAIN_STATE_INTEREST_COEFFICIENT * max(0.0, self.state_interest(node))
                + (self.REPUTATION_GAIN_REVENUE_BONUS if node["rev"] > 0 else 0.0))
        household.reputation = min(self.REPUTATION_CEILING, household.reputation + gain)
        household.scandal += self.alarm_of(node)
        governance.gov += self.state_interest(node)
        # _grant_staff, NOT a bare += on household.scholars/household.artisans:
        # _resync_pools(), which step() calls unconditionally every year,
        # always treats household.scholars and household.artisans
        # as computed purely from household.employees, so a bare
        # direct addition here would be overwritten out of existence the
        # very next time it runs. See _grant_staff.
        #
        # ONLY WITHOUT auto_hire: with it on - the optimizer's default, off
        # for a player - staff_capacity() already counts this same
        # institution toward sc_cap/ar_cap and step()'s smoothing grows
        # household.scholars/household.artisans toward that ceiling on its own; the
        # long civilization runs are calibrated against that smoothing alone
        # (see core.py, "1. staff"). Granting it a second time here as well
        # would double-count every one of these three institutions against
        # a tree calibrated to open up much more slowly.
        if not self.policy.get("auto_hire", not self.manual):
            grant = self.mechanic(node_id, "staff_grant")
            if grant:
                self._grant_staff(**grant)
        if self.is_venture(node_id) and not self.policy.get("auto_open", not self.manual):
            # Built is not open: say what is switched off until it is opened.
            benefit = self.NOT_OPERATING_BENEFIT.get(node_id)
            household.log.append((scenario.year,
                "completed: %s. STATUS: CLOSED / NOT OPERATING. %s Open it "
                "('open %s') to begin and to start paying upkeep."
                % (node["name"],
                   ("Not in effect until open: %s." % benefit) if benefit
                   else "Nothing is earning yet.", node_id)))
            shortfall = self.opening_shortfall(node_id)
            if shortfall:
                household.log.append((scenario.year,
                    "with today's staff you could not open it: it needs %.1f "
                    "scholars and %.1f craftsmen to supervise, and %.1f and %.1f "
                    "are free." % shortfall))
        else:
            household.log.append((scenario.year, "completed: " + node["name"]))
        for line in self.goal_effect_lines(node_id, goal_before):
            household.log.append((scenario.year, line))
        if node_id == self.goal and scenario.goal_year is None:
            scenario.goal_year = scenario.year

    # -- shocks -------------------------------------------------------------
    # WHAT YOU CAN DO ABOUT HISTORY.
    #
    # A game that tells you on turn one exactly which disasters are coming
    # has to let some completed technologies counter them - a mine that
    # arms Rome against a raid, a medicine that blunts a plague - findably,
    # not as hardcoded checks nowhere the player can see. Hazards are not
    # weather. They are the thing the whole programme is for.
    #
    # Each entry is (node id, how much of the harm it removes, what it is).
    # They compound, and none of them takes a hazard to zero on its own: no
    # amount of sanitation stops a plague, it decides how many of your people
    # are still alive at the end of it.
    _HAZARD_COUNTER_WHY = (
        "How much of this hazard one mitigating technology removes, "
        "compounding with every other counter for the same hazard and "
        "never reaching zero on its own (no amount of sanitation stops a "
        "plague; it decides how many people are still alive after). The "
        "MECHANISM this technology relieves this hazard through is real "
        "and named at its own declaration; the specific fraction removed "
        "is tuned game balance sized so the hazard remains real even "
        "fully countered, not measured against any historical mortality, "
        "sack or currency-debasement reduction.")
    HAZARD_EROSION_OWN_GOLD = declare(
        "HAZARD_EROSION_OWN_GOLD", 0.55, kind="temporary_heuristic",
        unit="fraction of real-erosion hazard removed",
        source="your own gold, dug not minted", confidence="D",
        why=_HAZARD_COUNTER_WHY)
    HAZARD_EROSION_OWN_SILVER = declare(
        "HAZARD_EROSION_OWN_SILVER", 0.35, kind="temporary_heuristic",
        unit="fraction of real-erosion hazard removed",
        source="your own silver", confidence="D", why=_HAZARD_COUNTER_WHY)
    # HAZARD_COUNTERS: {kind: [(node, share, label)]} from each node's `hazard_counters` (MechanicsMixin).
