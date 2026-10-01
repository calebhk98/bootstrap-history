"""Opening and closing a venture by hand: cost, staff, and the two verbs.

This is what it costs to open a completed capability's doors (venture_capex),
who it ties up (venture_hands/venture_foreman and the venture_staff_*
accounting of who is watching what), and the two player-facing actions
themselves (open_venture, close_venture) plus the shared institution-
expansion helper (_expand_institution) open_venture calls when `units` asks
for more than a first founding.

The automatic, year-by-year counterparts of these two verbs - closing what
staffing can no longer cover, reopening what can be covered again, warning
before either happens, and opening what plainly pays for itself - are a
separate subject and live in projects_staffing.py; see that file's own
docstring for why the split falls there rather than here. These are methods
of Sim; they are a mixin only so that they can live in a file of their own
(see projects.py's own docstring for why).
"""
import collections

from sim.constants import declare
from . import money_units


class VenturesMixin:
    VENTURE_CAPEX_SHARE_OF_BUILD_COST = declare(
        "VENTURE_CAPEX_SHARE_OF_BUILD_COST", 0.15, kind="temporary_heuristic",
        unit="fraction of project_cost", source=None, confidence="D",
        why="What opening a completed venture's doors costs relative to "
            "what building it cost - stock, premises, the first year's "
            "materials. Tuned so opening is a real but secondary "
            "commitment next to the research itself; not derived from any "
            "real ratio of working capital to fixed investment.")
    VENTURE_CAPEX_MIN_UPKEEP_YEARS = declare(
        "VENTURE_CAPEX_MIN_UPKEEP_YEARS", 1.0, kind="temporary_heuristic",
        unit="years of upkeep", source=None, confidence="D",
        why="A floor under venture_capex so a thing which is cheap to "
            "invent and expensive to run cannot be opened for nothing: it "
            "always costs at least one year of its own running upkeep. "
            "Tuned floor, not measured.")

    def venture_capex(self, node_id):
        """What it costs to open the doors, over and above having worked out
        how. Stock, premises, the first year's materials: a fraction of what
        the work itself cost, and never less than a year of its running cost,
        so that a thing which is cheap to invent and expensive to run cannot
        be opened for nothing."""
        node = self.nodes[node_id]
        return max(self.project_cost(node_id) * self.VENTURE_CAPEX_SHARE_OF_BUILD_COST,
                   node["up"] * self.VENTURE_CAPEX_MIN_UPKEEP_YEARS)

    # Supervision share of build crew, not full crew (avoids double-billing).
    VENTURE_SUPERVISION = declare(
        "VENTURE_SUPERVISION", 0.25, kind="temporary_heuristic",
        unit="fraction of the build crew", source=None, confidence="D",
        why="What fraction of a concern's BUILD crew (sch/art) its own "
            "staff must go on owing it in supervision once it is running, "
            "rather than the whole crew - charging the whole crew every "
            "year billed the same hands twice and measurably hurt Rome's "
            "own outcomes (see this constant's own comment). Tuned to "
            "avoid double-billing, not measured from any real supervisory "
            "ratio.")
    # Floor on supervision: a zero-build concern still needs staff watching.
    # One pair of hands per this much revenue.
    VENTURE_HANDS_PER_REVENUE_LABOUR_HOURS = declare(
        "VENTURE_HANDS_PER_REVENUE_LABOUR_HOURS", 30000.0, kind="temporary_heuristic",
        unit="labour hours per year of revenue per pair of hands", source=None,
        confidence="D",
        why="A floor under venture_supervision's own build-crew share: "
            "even a concern that took nobody to build (a bottling shed, a "
            "chaff cutter - 19% of concerns, per this constant's own "
            "comment) still needs somebody watching it once it earns "
            "real money, at one pair of hands per this many denarii of "
            "takings. Tuned so a fleet of loss-free, zero-build concerns "
            "cannot run itself for nothing (see the Han break-test this "
            "constant's own comment describes); not a measured "
            "supervisor-to-revenue ratio for any real enterprise.")
    VENTURE_HANDS_PER_REVENUE = money_units.PricedInLabourHours("VENTURE_HANDS_PER_REVENUE_LABOUR_HOURS")

    def venture_hands(self, node_id):
        """(scholars, craftsmen) of your own that running this ties up."""
        node = self.nodes[node_id]
        # Capability institutions (school, workshop) and net-loss concerns
        # don't tie up supervision staff (avoids circular dependency).
        if (node_id in self.CAPABILITY_INSTITUTIONS and node["rev"] <= node["up"]):
            return 0.0, 0.0
        supervision_share = self.VENTURE_SUPERVISION
        by_size = max(0.0, node["rev"]) / self.VENTURE_HANDS_PER_REVENUE
        return node["sch"] * supervision_share, max(node["art"] * supervision_share, by_size)

    VENTURE_FOREMAN_SHARE = declare(
        "VENTURE_FOREMAN_SHARE", 0.25, kind="temporary_heuristic",
        unit="FTE per concern supervised", source=None, confidence="D",
        why="How much of a skilled specialist's time supervising one "
            "concern that needs their trade ties up - one specialist can "
            "oversee at most four ordinary concerns of that kind. Tuned "
            "game balance, not a measured foreman-to-shop ratio.")

    def venture_foreman(self, node_id):
        """Return the skilled trade and FTE needed to supervise a concern.

        A concern whose build crew mixes generic artisans with a skilled trade
        cannot be supervised by interchangeable generic hands alone.  Retain
        the largest non-generic skilled contribution as its operating foreman;
        one specialist can oversee at most four ordinary concerns.  Purely
        generic concerns and knowledge/capability institutions keep the older
        scholar/craftsman rule.
        """
        node = self.nodes[node_id]
        lab = node.get("lab") or {}
        if (node_id in self.CAPABILITY_INSTITUTIONS or node.get("rev", 0) <= 0
                or lab.get("artisan", 0) <= 0):
            return None, 0.0
        skilled = [(hours, trade) for trade, hours in lab.items()
                   if trade not in ("artisan", "labourer", "slave")
                   and hours > 0]
        if not skilled:
            return None, 0.0
        _hours, trade = max(skilled, key=lambda row: (row[0], row[1]))
        return trade, self.VENTURE_FOREMAN_SHARE

    def venture_foremen_used(self, excluding=None):
        """Skilled-foreman FTE held by operating concerns, by trade."""
        used = collections.defaultdict(float)
        for node_id in sorted(self.state.projects.operating):
            if node_id == excluding or node_id not in self.nodes:
                continue
            trade, fte = self.venture_foreman(node_id)
            if trade:
                used[trade] += fte * self.institution_units(node_id)
        return dict(used)

    def venture_foreman_free(self, trade, excluding=None):
        """Employed specialists still free to supervise another concern."""
        return max(0.0, self.state.household.employees.get(trade, 0.0)
                   - self.venture_foremen_used(excluding).get(trade, 0.0))

    def venture_staff_who_is_watching_what(self):
        """Which concerns are holding your people, and how many each holds.

        Mothballing every concern the game shows elsewhere can still free
        no scholars at all, if some of them are held by something that
        screen never lists. This is that something, shown. Largest holder
        first, because that is the one to close.
        """
        rows = []
        for node_id in sorted(self.state.projects.operating):
            if node_id not in self.nodes:
                continue
            scholars, craftsmen = self.venture_hands(node_id)
            if scholars > 0.005 or craftsmen > 0.005:
                rows.append({"id": node_id, "scholars": round(scholars, 2),
                             "craftsmen": round(craftsmen, 2)})
        rows.sort(key=lambda r: -(r["scholars"] + r["craftsmen"]))
        return rows

    def venture_staff_used(self):
        """People of your own tied up supervising what you already have open."""
        # SORTED, for the same reason done_in_order exists: this sums FLOATS
        # over a set, floating point addition is not associative, and the
        # total gates open_venture with a hard comparison. Iterating an
        # unordered set gives a different, PYTHONHASHSEED-dependent sum
        # each run; every float sum over `operating` or `done` has to fix
        # its order.
        sch = art = 0.0
        for node_id in sorted(self.state.projects.operating):
            if node_id not in self.nodes:
                continue
            scholars, craftsmen = self.venture_hands(node_id)
            sch += scholars
            art += craftsmen
        return sch, art


    def venture_staff_free(self):
        """People you could put behind something new. You cannot run fifty
        businesses with three people, and this is the whole of why choosing
        WHICH to run is a decision rather than an accounting formality."""
        sch_used, art_used = self.venture_staff_used()
        own = self.FOUNDER_IS_WORTH if self.state.founder.founder_alive else 0.0
        return (max(0.0, self.effective_scholars() - sch_used),
                max(0.0, self.state.household.artisans + own - art_used))


    def opening_fee(self, node_id, units=None):
        """(charge, size) for opening a concern now; `open` charges exactly this.

        A starter founding of a scalable institution has a floor on its size;
        reopening restores the prior size, not a full founding."""
        if node_id in self.SCALABLE_INSTITUTIONS and units is not None:
            unit_count = max(self.STARTER_FOUNDING_MIN_UNITS, float(units))
        else:
            unit_count = self.reopen_units(node_id)
        return self.reopen_fee(node_id, unit_count), unit_count

    def open_venture(self, node_id, pay=True, units=None):
        """Start actually running something you have worked out how to do.

        `units` only means anything for SCALABLE_INSTITUTIONS (see that set's
        comment, above CAPABILITY_INSTITUTIONS): how much capacity to found,
        where 1.0 is the ordinary, historically-calibrated size every other
        figure in the engine assumes. Omit it and a first founding is 1.0.
        Ask for LESS and you found a starter place - a fraction of the
        cost, a fraction of the yearly bleed, a fraction of what it gives
        back - which running() needs to be affordable at low income, since
        a fixed 1.0 size has no smaller step to start at. Ask for units on
        something ALREADY open and you are asking to expand it - see
        _expand_institution.
        """
        if node_id not in self.nodes:
            return False, "no such node"
        projects = self.state.projects
        if node_id not in projects.done:
            return False, ("you have not worked out how to do that yet, so there "
                           "is nothing to open")
        if node_id in projects.granted:
            if self._practisable(node_id):
                # Society skill already in your practice: it's where your income
                # comes from. Cannot open it again.
                return False, ("you are already doing that - it is your practice, "
                               "and it is where most of your income comes from. "
                               "It is a skill this society has, not a concern "
                               "you opened, so there is nothing to open and "
                               "nothing to close")
            return False, ("that is something the society has, not a concern of "
                           "yours to run")
        if not self.is_venture(node_id):
            return False, ("that is knowledge, not a going concern: there is "
                           "nothing to open and nothing it would earn. It has "
                           "already changed what you can build")
        if node_id in projects.operating:
            if node_id in self.SCALABLE_INSTITUTIONS and units and float(units) > 0:
                return self._expand_institution(node_id, float(units), pay)
            return False, "you are already running that"
        scalable = node_id in self.SCALABLE_INSTITUTIONS
        fee, unit_count = self.opening_fee(node_id, units)
        refusal = self.staffing_open_refusal(node_id, unit_count)
        if refusal:
            return False, refusal
        projects = self.state.projects
        household = self.state.household
        scenario = self.state.scenario
        governance = self.state.governance
        if pay:
            if fee > self.spending_power("open"):
                # Report the same spending power the test checked.
                return False, ("opening it costs %s denarii in stock and premises, "
                               "and between %s in cash and what anyone will "
                               "advance against a purchase you can raise %s"
                               % ("{:,.0f}".format(fee),
                                  "{:,.0f}".format(household.capital),
                                  "{:,.0f}".format(self.spending_power("buy"))))
            household.debit(fee, "opening a venture")
        projects.operating.add(node_id)
        projects.mothballed.discard(node_id)
        self.clear_closure(node_id)
        if scalable:
            inst_units = getattr(governance, "inst_units", None)
            if inst_units is None:
                inst_units = governance.inst_units = {}
            inst_units[node_id] = unit_count
        # Record when doors opened for venture_ramp. Reopening doesn't restart it.
        _oy = getattr(projects, "opened_year", None)
        if _oy is None:
            _oy = projects.opened_year = {}
        _oy.setdefault(node_id, scenario.year)
        rev_now = self.venture_real_earnings(node_id, unit_count, fully_ramped=True)
        up_now = self.venture_real_upkeep(node_id, unit_count)
        # A reopened concern keeps its original start, so it only mentions a ramp it is still climbing.
        still_ramping = self.venture_ramp(node_id) < 1.0
        _ramp_note = (
            " It reaches that over the first %d years as custom finds it - "
            "expect less at first, not a mistake in the figure."
            % self.cfg["revenue_ramp_years"]) if rev_now > 0 and still_ramping else ""
        # Flag net-loss concerns explicitly; exclude capability institutions.
        _loss_note = (
            " !! this costs more than it earns (%s a year net), even once "
            "it is fully ramped up - that may be the right call for what it "
            "unlocks, but check 'why %s' if it is not what you meant."
            % ("{:,.0f}".format(up_now - rev_now), node_id)
            if up_now > rev_now and node_id not in self.CAPABILITY_INSTITUTIONS
            else "")
        return True, ("%s open%s: it earns %s a year and costs %s a year to "
                      "run.%s%s"
                      % (node_id, "" if unit_count == 1.0 else " at %.2f of a full founding" % unit_count,
                         "{:,.0f}".format(rev_now), "{:,.0f}".format(up_now),
                         _ramp_note, _loss_note))

    # Expansion: reusing "open" with units field keeps protocol backward-compatible.
    def _expand_institution(self, node_id, add_units, pay=True):
        """Found more of an institution that is already open."""
        have = self.institution_units(node_id)
        ceiling = self.institution_unit_ceiling(node_id)
        room = max(0.0, ceiling - have)
        if room < 0.02:
            return False, ("%s is already as big as this many people can fill: "
                           "about %.1f units of it, bounded by the population "
                           "(and, for a school or an academy, by how much of it "
                           "literacy says is not needed on the land)"
                           % (node_id, ceiling))
        add_units = min(add_units, room)
        node = self.nodes[node_id]
        sch_free, art_free = self.venture_staff_free()
        need_sch, need_art = self.venture_hands(node_id)
        need_sch, need_art = need_sch * add_units, need_art * add_units
        if need_sch > sch_free + 0.01 or need_art > art_free + 0.01:
            return False, ("nobody free to keep an eye on the extra %.2f units "
                           "of it: it needs %.2f more scholars and %.2f more "
                           "craftsmen to supervise, and you have %.2f and %.2f "
                           "not already watching something else"
                           % (add_units, need_sch, need_art, sch_free, art_free))
        fee = self.institution_unit_cost(node_id, have, add_units)
        if pay:
            if fee > self.spending_power("buy"):
                return False, ("expanding %s by %.2f units costs %s denarii, and "
                               "between %s in cash and what anyone will advance "
                               "against a purchase you can raise %s"
                               % (node_id, add_units, "{:,.0f}".format(fee),
                                  "{:,.0f}".format(self.state.household.capital),
                                  "{:,.0f}".format(self.spending_power("buy"))))
            self.state.household.debit(fee, "expanding a venture")
        governance = self.state.governance
        inst_units = getattr(governance, "inst_units", None)
        if inst_units is None:
            inst_units = governance.inst_units = {}
        inst_units[node_id] = have + add_units
        governance._inst_units_ver = getattr(governance, "_inst_units_ver", 0) + 1
        rev_now, up_now = node["rev"] * inst_units[node_id], node["up"] * inst_units[node_id]
        return True, ("%s expanded from %.2f to %.2f units for %s denarii: it "
                      "now earns about %s a year and costs about %s to run"
                      % (node_id, have, inst_units[node_id], "{:,.0f}".format(fee),
                         "{:,.0f}".format(rev_now), "{:,.0f}".format(up_now)))

    def close_venture(self, node_id):
        """Stop running it. You keep the knowledge; you stop paying for it and
        stop being paid by it."""
        projects = self.state.projects
        if node_id not in projects.operating:
            return False, "you are not running that"
        self.close_work(node_id, self.CLOSED_BY_CHOICE)
        node = self.nodes[node_id]
        return True, ("%s closed: you stop paying %s a year and stop earning %s"
                      % (node_id, "{:,.0f}".format(node["up"]), "{:,.0f}".format(node["rev"])))

