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

    # SUPERVISION, NOT OPERATION: a node's sch/art figures are what it takes
    # to BUILD the thing, and its upkeep already pays the people who run it
    # once built, so charging the full build crew against your own staff
    # forever would bill you twice for the same hands. What your own
    # trained people actually owe a going concern is supervision -
    # somebody of yours has to keep an eye on it - and that is a fraction
    # of what it took to build.
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
    # AND A FLOOR FROM ITS SIZE: charging a fraction of the BUILD crew alone
    # would mean concerns that take nobody to build - a bottling shed, a
    # butter trade, a chaff cutter - would take nobody to RUN either,
    # letting a fleet of such concerns run on nought employees and nought
    # in wages, which is precisely what the opening screen promises the
    # model will not do. A going concern needs somebody of yours to keep
    # an eye on it whether or not it was hard to build, and a bigger one
    # needs more: one pair of hands per 1,500 a year of takings, which
    # puts a 130-a-year bottling shed at a tenth of a person and a
    # 12,000-a-year fleet at eight.
    VENTURE_HANDS_PER_REVENUE = declare(
        "VENTURE_HANDS_PER_REVENUE", 1500.0, kind="temporary_heuristic",
        unit="denarii/year of revenue per pair of hands", source=None,
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

    def venture_hands(self, node_id):
        """(scholars, craftsmen) of your own that running this ties up."""
        node = self.nodes[node_id]
        # A SCHOOL DOES NOT COST YOU SCHOLARS. What these establishments take
        # is money - a patron's cultivation, a school's stipends - and what
        # they hand back is exactly the people every other concern is
        # supervised by. Charging supervision against them made the loop
        # impossible to enter: school_founded's build crew is twelve scholars,
        # so keeping it open wanted three of them, and the only source of three
        # scholars was the school you could not keep open. A founder opened
        # the school and the staffing rule shut it the same turn, for ever.
        # Only the ones that lose money qualify: a blast furnace is in this set
        # too, and a blast furnace certainly needs somebody watching it.
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
        for node_id in sorted(self.household.operating):
            if node_id == excluding or node_id not in self.nodes:
                continue
            trade, fte = self.venture_foreman(node_id)
            if trade:
                used[trade] += fte * self.institution_units(node_id)
        return dict(used)

    def venture_foreman_free(self, trade, excluding=None):
        """Employed specialists still free to supervise another concern."""
        return max(0.0, self.household.employees.get(trade, 0.0)
                   - self.venture_foremen_used(excluding).get(trade, 0.0))

    def venture_staff_who_is_watching_what(self):
        """Which concerns are holding your people, and how many each holds.

        Mothballing every concern the game shows elsewhere can still free
        no scholars at all, if some of them are held by something that
        screen never lists. This is that something, shown. Largest holder
        first, because that is the one to close.
        """
        rows = []
        for node_id in sorted(self.household.operating):
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
        for node_id in sorted(self.household.operating):
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
        own = self.FOUNDER_IS_WORTH if self.founder_alive else 0.0
        return (max(0.0, self.effective_scholars() - sch_used),
                max(0.0, self.household.artisans + own - art_used))


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
        if node_id not in self.household.done:
            return False, ("you have not worked out how to do that yet, so there "
                           "is nothing to open")
        if node_id in self.household.granted:
            if self._practisable(node_id):
                # The SKILL is the society's, and you are already practising
                # it - which is why it pays, and why there is nothing here
                # to open. `money` itemises this as your revenue, and the
                # refusal below must not contradict that by calling it only
                # the society's.
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
        if node_id in self.household.operating:
            if node_id in self.SCALABLE_INSTITUTIONS and units and float(units) > 0:
                return self._expand_institution(node_id, float(units), pay)
            return False, "you are already running that"
        node = self.nodes[node_id]
        scalable = node_id in self.SCALABLE_INSTITUTIONS
        # A STARTER FOUNDING IS STILL A FOUNDING, NOT A TOY. Below a fifth of
        # the ordinary size there would be nothing left standing between "a
        # schoolroom" and "no school at all", so this is a floor on what
        # `units` may ask for on a first opening, not a ceiling.
        #
        # REOPENING RESTORES WHAT WAS THERE, not the default single unit. A
        # closed school does not un-build the extra wings it grew before it
        # shut; only `units` explicitly asked for here changes the size.
        if scalable and units is not None:
            unit_count = max(self.STARTER_FOUNDING_MIN_UNITS, float(units))
        elif scalable:
            unit_count = getattr(self.household, "inst_units", {}).get(node_id, 1.0)
        else:
            unit_count = 1.0
        sch_free, art_free = self.venture_staff_free()
        need_sch, need_art = self.venture_hands(node_id)
        need_sch, need_art = need_sch * unit_count, need_art * unit_count
        foreman_trade, foreman_fte = self.venture_foreman(node_id)
        foreman_fte *= unit_count
        # A HUNDREDTH OF A PERSON IS NOBODY: comparing exact floats while
        # rounding the message to one decimal can print "it needs 0.0
        # craftsmen to supervise, and you have 0.0" - a refusal that
        # contradicts itself on its own line - so the comparison needs a
        # small tolerance rather than an exact one.
        if need_sch > sch_free + 0.01 or need_art > art_free + 0.01:
            return False, ("nobody free to keep an eye on it: it needs %.2f "
                           "scholars and %.2f craftsmen to supervise, and you "
                           "have %.2f and %.2f not already watching something "
                           "else. Hire, teach, or close something."
                           % (need_sch, need_art, sch_free, art_free))
        if (foreman_trade and foreman_fte
                > self.venture_foreman_free(foreman_trade) + 0.01):
            return False, ("no qualified foreman is free: this concern needs "
                           "%.2f %s FTE to supervise its specialist work, and "
                           "you have %.2f free. Hire a %s or close another "
                           "concern using one. Generic artisans cannot "
                           "substitute for this trade."
                           % (foreman_fte, foreman_trade,
                              self.venture_foreman_free(foreman_trade),
                              foreman_trade))
        fee = self.venture_capex(node_id) * (unit_count if scalable else 1.0)
        # A SHOP THAT LOST ITS KEEPER IS NOT A SHOP YOU HAVE TO BUILD AGAIN:
        # staff attrition runs at 3.5% a year, so a household sitting near
        # the supervision line can lose a concern in most years. The
        # premises are still standing and the stock is still on the
        # shelves; what is missing is somebody to watch it. Reopening
        # within a few years must cost the difference, not the whole thing
        # again.
        _shut = getattr(self.household, "shut_for_staff", {})
        if node_id in _shut and self.year - _shut[node_id] <= self.STAFF_CLOSURE_GRACE:
            fee *= self.STAFF_CLOSURE_DISCOUNT
        if pay:
            if fee > self.spending_power("open"):
                # SAY WHAT WAS COUNTED: the test allows cash plus what can be
                # borrowed, so the refusal must quote that same figure, not
                # cash alone - quoting cash alone tells a player they cannot
                # afford something the test itself would let them buy.
                return False, ("opening it costs %s denarii in stock and premises, "
                               "and between %s in cash and what anyone will "
                               "advance against a purchase you can raise %s"
                               % ("{:,.0f}".format(fee),
                                  "{:,.0f}".format(self.household.capital),
                                  "{:,.0f}".format(self.spending_power("buy"))))
            self.household.capital -= fee
        self.household.operating.add(node_id)
        self.household.mothballed.discard(node_id)
        _shut.pop(node_id, None)
        self.household.shut_for_staff = _shut
        if scalable:
            inst_units = getattr(self.household, "inst_units", None)
            if inst_units is None:
                inst_units = self.household.inst_units = {}
            inst_units[node_id] = unit_count
        # WHEN THE DOORS OPENED, which is when custom starts to find you: see
        # venture_ramp, which reads this rather than the year the capability
        # was worked out, so opening late does not skip the ramp. Reopening
        # something you had running does not restart it: the shop is known.
        _oy = getattr(self.household, "opened_year", None)
        if _oy is None:
            _oy = self.household.opened_year = {}
        _oy.setdefault(node_id, self.year)
        rev_now, up_now = node["rev"] * unit_count, node["up"] * unit_count
        # SAID NOW, NOT DISCOVERED LATER IN A FOOTNOTE: a newly opened
        # concern takes revenue_ramp_years to reach the figure just quoted -
        # custom takes time to find the shop - and that has to be said
        # here, at the moment of opening, not only in `money`'s
        # still_ramping(), read after the fact once the ledger already
        # looks like it disagrees with what was promised.
        _ramp_note = (
            " It reaches that over the first %d years as custom finds it - "
            "expect less at first, not a mistake in the figure."
            % self.cfg["revenue_ramp_years"]) if rev_now > 0 else ""
        # SUBTRACT THE TWO NUMBERS, DO NOT LEAVE THEM SIDE BY SIDE: earn and
        # upkeep sitting next to each other on the screen does not tell a
        # reader which is bigger, so a net-loss concern has to say so
        # explicitly rather than relying on the reader doing the
        # subtraction. Capability institutions are deliberately excluded: a
        # school or a workshop losing money is the normal, intended shape of
        # the trade (see CAPABILITY_INSTITUTIONS and venture_hands), not a
        # mistake to flag on the one screen a player could still back out
        # from.
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

    # HOW A PLAYER OPENS A SECOND SCHOOL: send `units` to the SAME "open"
    # command. {"cmd":"open","id":"school_founded"} founds the first,
    # ordinary one, and {"cmd":"open","id":"school_founded",
    # "units":2} on a school already open founds a second, taking it to 2.0
    # units of capacity. Reusing "open" rather than adding a new verb means a
    # save and an agent that has never heard of expansion still speaks a
    # protocol that works: the field is simply absent from every call it never
    # makes.
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
                                  "{:,.0f}".format(self.household.capital),
                                  "{:,.0f}".format(self.spending_power("buy"))))
            self.household.capital -= fee
        inst_units = getattr(self.household, "inst_units", None)
        if inst_units is None:
            inst_units = self.household.inst_units = {}
        inst_units[node_id] = have + add_units
        self.household._inst_units_ver = getattr(self.household, "_inst_units_ver", 0) + 1
        rev_now, up_now = node["rev"] * inst_units[node_id], node["up"] * inst_units[node_id]
        return True, ("%s expanded from %.2f to %.2f units for %s denarii: it "
                      "now earns about %s a year and costs about %s to run"
                      % (node_id, have, inst_units[node_id], "{:,.0f}".format(fee),
                         "{:,.0f}".format(rev_now), "{:,.0f}".format(up_now)))

    def close_venture(self, node_id):
        """Stop running it. You keep the knowledge; you stop paying for it and
        stop being paid by it."""
        if node_id not in self.household.operating:
            return False, "you are not running that"
        self.household.operating.discard(node_id)
        self.household.mothballed.add(node_id)
        node = self.nodes[node_id]
        return True, ("%s closed: you stop paying %s a year and stop earning %s"
                      % (node_id, "{:,.0f}".format(node["up"]), "{:,.0f}".format(node["rev"])))

