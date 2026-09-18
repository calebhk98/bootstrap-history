"""Opening and closing a venture by hand: cost, staff, and the two verbs.

Split out of sim/engine/projects.py (see that file's own docstring for why):
this is what it costs to open a completed capability's doors (venture_capex),
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
of Sim; they are a mixin only so that they can live in a file of their own.
Behaviour is unchanged and verified byte-identical.
"""
import collections

from constants import declare


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

    def venture_capex(self, k):
        """What it costs to open the doors, over and above having worked out
        how. Stock, premises, the first year's materials: a fraction of what
        the work itself cost, and never less than a year of its running cost,
        so that a thing which is cheap to invent and expensive to run cannot
        be opened for nothing."""
        node = self.nodes[k]
        return max(self.project_cost(k) * self.VENTURE_CAPEX_SHARE_OF_BUILD_COST,
                   node["up"] * self.VENTURE_CAPEX_MIN_UPKEEP_YEARS)

    # SUPERVISION, NOT OPERATION. A node's sch/art figures are what it takes to
    # BUILD the thing, and its upkeep already pays the people who run it once
    # built - so charging the full build crew against your own staff for ever
    # would be billing you twice for the same hands, and it measurably was:
    # Rome fell from half its runs reaching the goal to a quarter when the
    # operating cost was the whole build crew. What your own trained people
    # actually owe a going concern is supervision - somebody of yours has to
    # keep an eye on it - and that is a fraction of what it took to build.
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
    # AND A FLOOR FROM ITS SIZE. Charging a fraction of the BUILD crew alone
    # meant that the 19% of concerns which take nobody to build - a bottling
    # shed, a butter trade, a chaff cutter - took nobody to RUN either. A break
    # tester ended a Han run with between 51 and 94 concerns going at once,
    # among them a whaling fleet, a coal seam, an inn and a gambling house,
    # on nought employees and nought in wages, and pointed out that this is
    # precisely what the opening screen promises the model will not do. A
    # going concern needs somebody of yours to keep an eye on it whether or not
    # it was hard to build, and a bigger one needs more: one pair of hands per
    # 1,500 a year of takings, which puts a 130-a-year bottling shed at a tenth
    # of a person and a 12,000-a-year fleet at eight.
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

    def venture_hands(self, k):
        """(scholars, craftsmen) of your own that running this ties up."""
        node = self.nodes[k]
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
        if (k in self.CAPABILITY_INSTITUTIONS and node["rev"] <= node["up"]):
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

    def venture_foreman(self, k):
        """Return the skilled trade and FTE needed to supervise a concern.

        A concern whose build crew mixes generic artisans with a skilled trade
        cannot be supervised by interchangeable generic hands alone.  Retain
        the largest non-generic skilled contribution as its operating foreman;
        one specialist can oversee at most four ordinary concerns.  Purely
        generic concerns and knowledge/capability institutions keep the older
        scholar/craftsman rule.
        """
        node = self.nodes[k]
        lab = node.get("lab") or {}
        if (k in self.CAPABILITY_INSTITUTIONS or node.get("rev", 0) <= 0
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

        A play tester spent about seventy in-game years on the endgame's
        staffing and wrote: "mothballing all 259 running concerns freed zero
        scholars - about 17 are held by something the game never shows". This
        is that something, shown. Largest holder first, because that is the one
        to close.
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
        # over a set, floating point addition is not associative, and the total
        # gates open_venture with a hard comparison. A break tester ran the
        # same seed three times and got 587,300 / 6,664,218 / 6,652,459 in
        # capital; PYTHONHASHSEED=0 made all three identical. Every float sum
        # over `operating` or `done` has to fix its order.
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


    def open_venture(self, k, pay=True, units=None):
        """Start actually running something you have worked out how to do.

        `units` only means anything for SCALABLE_INSTITUTIONS (see that set's
        comment, above CAPABILITY_INSTITUTIONS): how much capacity to found,
        where 1.0 is the ordinary, historically-calibrated size every other
        figure in the engine assumes. Omit it and a first founding is 1.0,
        exactly as before. Ask for LESS and you found a starter place - a
        fraction of the cost, a fraction of the yearly bleed, a fraction of
        what it gives back - which is the actual bridge running() needed: the
        old rule could not be afforded at any income because there was no
        smaller size to start at. Ask for units on something ALREADY open and
        you are asking to expand it - see _expand_institution.
        """
        if k not in self.nodes:
            return False, "no such node"
        if k not in self.household.done:
            return False, ("you have not worked out how to do that yet, so there "
                           "is nothing to open")
        if k in self.household.granted:
            if self._practisable(k):
                # A tester put this best: "my entire un-chosen livelihood is
                # drilling holes in Han skulls, and the game denies it's mine."
                # `money` itemises this as their revenue and `open` called it
                # the society's. Both are half right: the SKILL is the
                # society's, and you are already practising it - which is why
                # it pays, and why there is nothing here to open.
                return False, ("you are already doing that - it is your practice, "
                               "and it is where most of your income comes from. "
                               "It is a skill this society has, not a concern "
                               "you opened, so there is nothing to open and "
                               "nothing to close")
            return False, ("that is something the society has, not a concern of "
                           "yours to run")
        if not self.is_venture(k):
            return False, ("that is knowledge, not a going concern: there is "
                           "nothing to open and nothing it would earn. It has "
                           "already changed what you can build")
        if k in self.household.operating:
            if k in self.SCALABLE_INSTITUTIONS and units and float(units) > 0:
                return self._expand_institution(k, float(units), pay)
            return False, "you are already running that"
        node = self.nodes[k]
        scalable = k in self.SCALABLE_INSTITUTIONS
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
            unit_count = getattr(self.household, "inst_units", {}).get(k, 1.0)
        else:
            unit_count = 1.0
        sch_free, art_free = self.venture_staff_free()
        need_sch, need_art = self.venture_hands(k)
        need_sch, need_art = need_sch * unit_count, need_art * unit_count
        foreman_trade, foreman_fte = self.venture_foreman(k)
        foreman_fte *= unit_count
        # A HUNDREDTH OF A PERSON IS NOBODY. The comparison was exact and the
        # message rounded to one decimal, so a break tester read "it needs 0.0
        # craftsmen to supervise, and you have 0.0" - a refusal that
        # contradicts itself on its own line - and then found that mothballing
        # two hundred and fifty-nine concerns freed nothing, because every one
        # of them was holding a rounding error.
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
        fee = self.venture_capex(k) * (unit_count if scalable else 1.0)
        # A SHOP THAT LOST ITS KEEPER IS NOT A SHOP YOU HAVE TO BUILD AGAIN.
        # Staff attrition runs at 3.5% a year, so a household sitting near the
        # supervision line loses a concern most years and pays the full stock
        # and premises to reopen it - a play tester watched four close at once,
        # every year, and wrote that it cost them hundreds a year and they
        # could never get ahead of it. The premises are still standing and the
        # stock is still on the shelves; what was missing was somebody to
        # watch it. Reopening within a few years costs the difference, not the
        # whole thing.
        _shut = getattr(self.household, "shut_for_staff", {})
        if k in _shut and self.year - _shut[k] <= self.STAFF_CLOSURE_GRACE:
            fee *= self.STAFF_CLOSURE_DISCOUNT
        if pay:
            if fee > self.spending_power("open"):
                # SAY WHAT WAS COUNTED. The test allows cash plus half the
                # credit line and the refusal quoted the cash alone, so a play
                # tester at -1,608 with a 3,684 line 44% used read "opening it
                # costs 40 denarii and you have -1,608" and left seven finished
                # concerns worth 1,713 a year shut, believing they could not
                # spend forty denarii they had already been allowed to borrow
                # sixteen hundred of.
                return False, ("opening it costs %s denarii in stock and premises, "
                               "and between %s in cash and what anyone will "
                               "advance against a purchase you can raise %s"
                               % ("{:,.0f}".format(fee),
                                  "{:,.0f}".format(self.household.capital),
                                  "{:,.0f}".format(self.spending_power("buy"))))
            self.household.capital -= fee
        self.household.operating.add(k)
        self.household.mothballed.discard(k)
        _shut.pop(k, None)
        self.household.shut_for_staff = _shut
        if scalable:
            inst_units = getattr(self.household, "inst_units", None)
            if inst_units is None:
                inst_units = self.household.inst_units = {}
            inst_units[k] = unit_count
        # WHEN THE DOORS OPENED, which is when custom starts to find you. See
        # venture_ramp: this used to read the year you worked the thing OUT, so
        # opening late skipped the ramp entirely. Reopening something you had
        # running does not restart it: the shop is known.
        _oy = getattr(self.household, "opened_year", None)
        if _oy is None:
            _oy = self.household.opened_year = {}
        _oy.setdefault(k, self.year)
        rev_now, up_now = node["rev"] * unit_count, node["up"] * unit_count
        # SAID NOW, NOT DISCOVERED LATER IN A FOOTNOTE. A newly opened
        # concern takes revenue_ramp_years to reach the figure just quoted -
        # custom takes time to find the shop - and the only place this was
        # ever said was `money`'s still_ramping(), read after the fact. A
        # player told "it earns 2,000 a year" at the moment of opening and
        # then watching 650 land in the ledger had no way to know, right
        # then, that both numbers were correct.
        _ramp_note = (
            " It reaches that over the first %d years as custom finds it - "
            "expect less at first, not a mistake in the figure."
            % self.cfg["revenue_ramp_years"]) if rev_now > 0 else ""
        # SUBTRACT THE TWO NUMBERS YOU JUST PRINTED. A Han playtester opened
        # a net-loss concern four separate times - three of them after
        # having already caught the mistake once and written it up - and
        # said, correctly, that the earn and upkeep figures sit side by side
        # on every screen and nothing ever does the subtraction for the
        # reader. Capability institutions are deliberately excluded: a
        # school or a workshop losing money is the normal, intended shape of
        # the trade (see CAPABILITY_INSTITUTIONS and venture_hands), not a
        # mistake to flag on the one screen a player could still back out
        # from.
        _loss_note = (
            " !! this costs more than it earns (%s a year net), even once "
            "it is fully ramped up - that may be the right call for what it "
            "unlocks, but check 'why %s' if it is not what you meant."
            % ("{:,.0f}".format(up_now - rev_now), k)
            if up_now > rev_now and k not in self.CAPABILITY_INSTITUTIONS
            else "")
        return True, ("%s open%s: it earns %s a year and costs %s a year to "
                      "run.%s%s"
                      % (k, "" if unit_count == 1.0 else " at %.2f of a full founding" % unit_count,
                         "{:,.0f}".format(rev_now), "{:,.0f}".format(up_now),
                         _ramp_note, _loss_note))

    # HOW A PLAYER OPENS A SECOND SCHOOL. Send `units` to the SAME "open"
    # command: {"cmd":"open","id":"school_founded"} founds the first, ordinary
    # one exactly as it always did, and {"cmd":"open","id":"school_founded",
    # "units":2} on a school already open founds a second, taking it to 2.0
    # units of capacity. Reusing "open" rather than adding a new verb means a
    # save and an agent that has never heard of expansion still speaks a
    # protocol that works: the field is simply absent from every call it never
    # makes.
    def _expand_institution(self, k, add_units, pay=True):
        """Found more of an institution that is already open."""
        have = self.institution_units(k)
        ceiling = self.institution_unit_ceiling(k)
        room = max(0.0, ceiling - have)
        if room < 0.02:
            return False, ("%s is already as big as this many people can fill: "
                           "about %.1f units of it, bounded by the population "
                           "(and, for a school or an academy, by how much of it "
                           "literacy says is not needed on the land)"
                           % (k, ceiling))
        add_units = min(add_units, room)
        node = self.nodes[k]
        sch_free, art_free = self.venture_staff_free()
        need_sch, need_art = self.venture_hands(k)
        need_sch, need_art = need_sch * add_units, need_art * add_units
        if need_sch > sch_free + 0.01 or need_art > art_free + 0.01:
            return False, ("nobody free to keep an eye on the extra %.2f units "
                           "of it: it needs %.2f more scholars and %.2f more "
                           "craftsmen to supervise, and you have %.2f and %.2f "
                           "not already watching something else"
                           % (add_units, need_sch, need_art, sch_free, art_free))
        fee = self.institution_unit_cost(k, have, add_units)
        if pay:
            if fee > self.spending_power("buy"):
                return False, ("expanding %s by %.2f units costs %s denarii, and "
                               "between %s in cash and what anyone will advance "
                               "against a purchase you can raise %s"
                               % (k, add_units, "{:,.0f}".format(fee),
                                  "{:,.0f}".format(self.household.capital),
                                  "{:,.0f}".format(self.spending_power("buy"))))
            self.household.capital -= fee
        inst_units = getattr(self.household, "inst_units", None)
        if inst_units is None:
            inst_units = self.household.inst_units = {}
        inst_units[k] = have + add_units
        rev_now, up_now = node["rev"] * inst_units[k], node["up"] * inst_units[k]
        return True, ("%s expanded from %.2f to %.2f units for %s denarii: it "
                      "now earns about %s a year and costs about %s to run"
                      % (k, have, inst_units[k], "{:,.0f}".format(fee),
                         "{:,.0f}".format(rev_now), "{:,.0f}".format(up_now)))

    def close_venture(self, k):
        """Stop running it. You keep the knowledge; you stop paying for it and
        stop being paid by it."""
        if k not in self.household.operating:
            return False, "you are not running that"
        self.household.operating.discard(k)
        self.household.mothballed.add(k)
        node = self.nodes[k]
        return True, ("%s closed: you stop paying %s a year and stop earning %s"
                      % (k, "{:,.0f}".format(node["up"]), "{:,.0f}".format(node["rev"])))

