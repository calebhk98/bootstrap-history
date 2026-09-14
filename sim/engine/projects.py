"""Starting, stopping, finishing and abandoning a piece of work.

Split out of simulator.py, which had grown to 5,600 lines. These are
methods of Sim; they are a mixin only so that they can live in a file of
their own. Behaviour is unchanged and verified byte-identical.
"""
import collections, json, math, os, random
from collections import defaultdict

from .data import *          # the shared tables and loaders
from .data import (closure)


class ProjectsMixin:
    # ---- knowing how, and actually running it -------------------------------
    # THE DEEPEST THING ANY PLAYTESTER SAID ABOUT THIS MODEL was not a bug
    # report. It was: "you research the finance stuff and instantly make money
    # -- but shouldn't that just unlock the ABILITY to do it? You research
    # loans, now you can give out loans. What if you didn't give out any? And
    # inventing stock market maths without building a stock market, or the
    # assembly line without a factory, is a bit unlikely to pay."
    #
    # That was right, and it went to the middle of the economy. 1,337 of the
    # 2,831 nodes carry revenue and 1,256 of those also carry upkeep, so the
    # tree ALREADY described them as going concerns that cost money to run and
    # pay money back. The only thing missing was the act of choosing to run
    # one. Completing the research paid you whether or not you ever opened the
    # doors.
    #
    # So: `done` is what you KNOW. `operating` is what you RUN. Revenue and
    # upkeep follow `operating`, and nothing else does - the goal, the tree,
    # the prerequisites and the standing you earn all still follow `done`,
    # because knowing how to make a transistor is the achievement and does not
    # require you to sell any.
    def is_venture(self, k):
        """Is this something you could run as a going concern, as opposed to a
        piece of knowledge that simply changes what you can do?"""
        n = self.nodes.get(k)
        if n is None or k in self.granted:
            return False
        return n["rev"] > 0 or n["up"] > 0

    # Concerns whose whole point is what they let you DO - scholars a school
    # supports, household places a workshop adds, credit a patron's name
    # unlocks, knowledge a corpus preserves - as opposed to what they take at
    # the door. Every one of these is gated through running() somewhere in this
    # engine, and several of them lose money outright, so the margin test in
    # auto_open_ventures would leave them shut for ever. Kept honest by a
    # regression check that greps the engine for running() gates and fails if
    # any node named in one is missing from this set.
    # fin_company_town and fin_chain_store joined this set together with the
    # STAFF_CAPACITY_SOURCES entries that run() -gate them (labour.py): both
    # are going concerns whose entire point is the household places they
    # support, exactly like a school or a workshop, and both run at a loss on
    # the books by design (fin_chain_store: upkeep 2,000 against revenue
    # 1,500) - the intended shape of the trade, not a mistake to be flagged
    # the way an ordinary money-losing venture is. fin_societas and
    # fin_trial_balance are NOT here: neither has any revenue or upkeep of
    # its own (is_venture() is false for both), so neither is ever opened,
    # closed, or capable of losing money - there is nothing for this set to
    # protect.
    CAPABILITY_INSTITUTIONS = frozenset((
        "academy_network", "blast_furnace", "collegium_licensed",
        "corpus_dispersed", "corpus_written", "crucible_steel",
        "endowment_land", "exp_trade_route_extend", "fin_argentarii",
        "fin_chain_store", "fin_company_town", "fin_university",
        "freedman_staff", "identity_cover",
        "interchangeable_parts", "patron_imperial", "patron_local",
        "patron_senatorial", "plague_preparedness", "power_grid", "railway",
        "sanitation_antisepsis", "school_founded", "steam_high_pressure",
        "telegraph_electric", "workshop_first"))

    # ---- DONE VERSUS OPERATING, MADE LOUD --------------------------------
    # The corpus bug (see core.py's Sim.corpus_hedge, and the commit that
    # introduced it) was one specific case of a general shape: a screen
    # promised a running()-gated payout by reading has(). That one case is
    # fixed now. This is the general case - every OTHER capability in
    # CAPABILITY_INSTITUTIONS whose running()-gated effect a player can
    # actually lose without any screen ever saying so.
    #
    # Each value names what switches off, in the player's own words, not a
    # number - the numbers already live with the one function that computes
    # each effect (update_protection, standing_floor, credit_limit,
    # goods_reach_factor, staff_capacity, workshop_output - see the running()
    # call sites in each). This table only says WHICH of those just went
    # quiet, so nothing here can drift out of step with what those functions
    # actually pay: a number is never invented here, only named.
    #
    # plague_preparedness is the one CAPABILITY_INSTITUTIONS member
    # deliberately absent: its only running()-gated reference left in the
    # engine is a dead local (`prep` in society.py's _shocks) that nothing
    # reads, and its real hazard relief (HAZARD_COUNTERS) is has()-gated like
    # corpus - so closing it costs nothing measurable today. Warning about it
    # anyway would be exactly the false alarm this exists to avoid.
    NOT_OPERATING_BENEFIT = {
        "academy_network": "Scholar and artisan training, standing, and its "
                           "reduction of eminence risk",
        "blast_furnace": "Artisan training capacity",
        "collegium_licensed": "Scholar capacity, protection and credit",
        "corpus_dispersed": "Standing, and the faster diffusion of "
                            "technology through the economy",
        "corpus_written": "Standing",
        "crucible_steel": "Artisan training capacity",
        "endowment_land": "Protection, credit and the lower interest rate",
        "exp_trade_route_extend": "The trade-route revenue bonus",
        "fin_argentarii": "The lower interest rate",
        "fin_university": "Protection",
        "freedman_staff": "Artisan capacity",
        "identity_cover": "Protection, credit and standing",
        "interchangeable_parts": "The price markup and staff-capacity bonus",
        "patron_imperial": "Protection, credit, state funding and status",
        "patron_local": "Protection and credit",
        "patron_senatorial": "Protection, credit and status",
        "power_grid": "The price markup and staff-capacity bonus",
        "railway": "The trade-reach revenue bonus and staff capacity",
        "sanitation_antisepsis": "Your extra life-expectancy",
        "school_founded": "Scholar and artisan training and the standing it earns",
        "steam_high_pressure": "Artisan training capacity",
        "telegraph_electric": "The trade-reach revenue bonus and staff capacity",
        "workshop_first": "Artisan capacity",
    }

    def capability_gaps(self):
        """Completed capability institutions that are NOT currently operating,
        each with the real running()-gated benefit it is not collecting right
        now. See NOT_OPERATING_BENEFIT above for why the list this walks is
        CAPABILITY_INSTITUTIONS minus plague_preparedness.

        fin_university is the one entry needing its own gate here rather than
        in the table: its sole running()-gated effect (update_protection,
        society.py) is an `or` with school_founded, so closing it costs
        nothing while school_founded is still open, and warning anyway would
        be a false alarm.
        """
        out = []
        for k in sorted(self.NOT_OPERATING_BENEFIT):
            if k not in self.nodes or not self.has(k) or self.running(k):
                continue
            if k == "fin_university" and self.running("school_founded"):
                continue
            benefit = self.NOT_OPERATING_BENEFIT[k]
            out.append({
                "id": k,
                "benefit_switched_off": benefit,
                "warning": ("Critical capability completed but not "
                           "operating: %s. %s is currently inactive."
                           % (k, benefit)),
                "fix": "open %s" % k,
            })
        return out

    # ---- AN INSTITUTION IS A QUANTITY, WHERE A SECOND ONE MEANS ANYTHING --
    # "Can you have multiple things? What if I wanted to raise literacy to
    # 90%+, and wanted to open 5,000 schools?" is the question that exposed
    # the asymmetry running()'s own parked comment names: a mine is
    # open_mine(material, tonnes_per_year) and a forest is forest_ha, both
    # quantities you sink more into as the money and the people to staff them
    # turn up, while school_founded, workshop_first and their kind are one
    # boolean, ever, however rich or literate the household becomes.
    #
    # Not every CAPABILITY_INSTITUTIONS entry gets this. A patronage
    # (patron_local/senatorial/imperial) is one man's opinion of you, not a
    # building - "five imperial patrons" is not a richer version of one, it is
    # nonsense. A singular achievement (endowment_land, corpus_written,
    # sanitation_antisepsis, identity_cover, the heavy-industry techniques)
    # is a state the whole household is in, not a count of sites. What a
    # school, a workshop, a licensed collegium, an academy and a freedman
    # staff have that those do not is exactly the thing the parked comment
    # points at: each is a PLACE that supports a number of people
    # (institution_places, economy.py), and a second school built across town
    # supports more people for a reason a second emperor's goodwill does not.
    # fin_chain_store joined this set for the same reason school_founded is
    # in it: "a second school built across town" IS the model this node's own
    # note already describes ("operates identical stores in multiple
    # cities"), a second unit is simply a second town rather than a second
    # schoolroom. It falls through to this function's own generic ceiling
    # below (population, not literacy - a branch network draws on merchants
    # and clerks, not the lettered few a second academy needs), so nothing
    # else here had to change to seat it.
    SCALABLE_INSTITUTIONS = frozenset((
        "workshop_first", "school_founded", "academy_network",
        "freedman_staff", "collegium_licensed", "fin_chain_store"))

    def institution_units(self, k):
        """How much of this institution is actually running, as a number
        rather than a flag.

        0 if it is not open. 1.0 is a single, ordinary founding - exactly the
        size every rev/up/places/room figure elsewhere in the engine was
        always calibrated against, so a run that never expands one of these
        behaves EXACTLY as it did before this existed. Above 1.0 is genuine
        expansion; below 1.0 (see open_venture's `units` argument) is a
        starter founding smaller than the historically-calibrated size, which
        is the actual bridge running() needed: the reason the first workshop
        was never affordable was that there was no way to found a SMALL one.
        For anything not in SCALABLE_INSTITUTIONS this is just running() cast
        to a float, because there is nothing to found a second of.
        """
        if k not in self.SCALABLE_INSTITUTIONS:
            return 1.0 if self.running(k) else 0.0
        if k not in self.operating:
            return 0.0
        return max(0.0, getattr(self, "inst_units", {}).get(k, 1.0))

    def institution_unit_ceiling(self, k):
        """The most units of this institution the empire can actually fill.

        Bounded by population, and - the user's own instinct, and a real,
        historically sound one - by food: "a lot of rural people without good
        farming don't really want their kids to go to school, they want them
        working for food or money". This model has no literal tonnes-of-grain
        ledger, but it already has the right proxy for exactly that
        constraint: literacy_general, civ data's measure of how much of the
        population is NOT tied to subsistence farming and so could plausibly
        be literate at all (see labour.py's LITERACY_REFERENCE_GENERAL and its
        own comment on why Rome's is 0.12). A school's ceiling rising with
        literacy_general is not a coincidence dressed up as a rule: it is the
        same fact - a farming society can spare few hands for a classroom -
        counted from the other side, and it is also the virtuous circle the
        user was reaching for, because schools are one of the things that
        raise literacy_general in the first place (apply_tech_effects,
        society.py).

        One unit here is NOT one literal schoolhouse; at this model's scale
        # one unit is already the whole of Rome's original school_founded (34
        # places, institution_places, economy.py) and "5,000 schools" is the
        # player's mental picture of what investing several further units of
        # capacity buys, not a count this engine tracks building by building -
        # the same abstraction a "tonnes_per_year" mine already uses for
        # however many actual shafts that tonnage comes out of.
        """
        if k not in self.SCALABLE_INSTITUTIONS:
            return 1.0
        if k in ("school_founded", "academy_network"):
            lit = max(0.02, float(self.civ.get("literacy_general", 0.12)))
            return max(1.0, 6.0 * self.pop_scale ** 0.5 * (lit / 0.12) ** 0.5)
        # Workshops, collegia and a freedman staff draw on craftsmen rather
        # than the literate few, so population alone bounds them, not literacy.
        return max(1.0, 4.0 * self.pop_scale ** 0.5)

    # HOW MUCH DEARER EACH FURTHER UNIT IS, past the first. A second school
    # does not double the supply of people fit to teach in one: it draws on
    # the same small pool of the literate and the propertied the first one
    # already drew down, so founding it costs more than the first did, by a
    # growing margin, well before the population/literacy ceiling above ever
    # bites. 0.5 means the tenth unit's marginal founding cost is 5.5 times
    # the first's - steep enough that a founder pursues the ceiling by
    # raising literacy and population rather than by brute-force spending,
    # which is the whole reason the ceiling and the cost curve are two
    # separate mechanisms rather than one.
    INSTITUTION_EXPANSION_CONVEXITY = 0.5

    def institution_unit_cost(self, k, have_units, add_units):
        """Denarii to take this institution from `have_units` to
        `have_units + add_units`, where 1.0 unit costs exactly what founding
        it has always cost (venture_capex) - so a run that only ever founds
        the original single unit pays exactly what it always paid.
        """
        base = self.venture_capex(k)
        c = self.INSTITUTION_EXPANSION_CONVEXITY

        def f(u):
            return u + c * 0.5 * max(0.0, u - 1.0) ** 2
        return base * max(0.0, f(have_units + add_units) - f(have_units))

    # ---- BUILT, versus BUILT AND STILL RUNNING ----------------------------
    # `has` answers "do you know how / did you build it", and for a piece of
    # knowledge that is the whole story. For an establishment it is not. A
    # school with nobody paid to keep it open trains no scholars; a patron you
    # stopped cultivating does not lend his name; a workshop whose doors are
    # shut houses nobody. Every capability in this engine was gated on `has`,
    # which meant a founder collected the twelve scholars a school supports,
    # the ten household places a workshop adds and the sixty thousand of credit
    # an imperial patron unlocks WITHOUT EVER OPENING ANY OF THEM - and, since
    # upkeep follows what you run, without paying a denarius of their running
    # cost either. A play tester put it exactly right: "I never worked out what
    # `open` does for a work that earns nothing... paying to open them looked
    # like pure loss, and I ignored them for two centuries with no visible
    # penalty." They were correct, and that is the bug.
    #
    # This is the honest test, and it is `has` for everything that has no doors
    # to shut: a technique costs nothing to keep and cannot be closed.
    def running(self, k):
        """Built, and still being maintained - which is what a capability needs.

        True for anything you have done that is not a going concern (knowledge
        does not close), for this society's own crafts, and for a concern you
        actually have open.
        """
        if k not in self.done:
            return False
        if k in self.granted or not self.is_venture(k):
            return True
        # UNPARKED. This returned True unconditionally for a long time, with a
        # comment recording why: requiring the doors to be open sent Rome from
        # 38% of runs reaching the goal to none, because a workshop or a
        # school was a single boolean, one size, ever, so a founder who could
        # not afford the WHOLE of it could not afford any of it - "there is no
        # ladder to climb, only a single step that is either affordable or
        # not". Two earlier bridges (scaling an institution's upkeep by how
        # full it is, in economy.py; letting one be opened against what you
        # could raise rather than only what you were clearing, in
        # auto_open_ventures below) both survive and both helped Han without
        # ever recovering Rome, because neither one touched the actual defect:
        # there was no smaller size to start at.
        #
        # SCALABLE_INSTITUTIONS is that smaller size. institution_units(k) can
        # now sit below 1.0 - a starter founding, a fraction of the cost and
        # the yearly bleed of the historically-calibrated full size - and
        # auto_open_ventures founds exactly as much of one as the household's
        # surplus will carry rather than refusing the whole thing. Measured
        # the same way the parked comment was: eight runs a civilisation at
        # horizon 700, `captured_han_386.json` (the strategy that scores 100%
        # on both civilisations with this rule parked). See the measurement
        # recorded in this file's own test suite / the commit that unparked
        # this for the numbers; the short version is that Rome's median year
        # reached and median technologies built held, where requiring the
        # doors open with institutions still booleans had cost Rome the run
        # outright.
        return k in self.operating

    def venture_capex(self, k):
        """What it costs to open the doors, over and above having worked out
        how. Stock, premises, the first year's materials: a fraction of what
        the work itself cost, and never less than a year of its running cost,
        so that a thing which is cheap to invent and expensive to run cannot
        be opened for nothing."""
        n = self.nodes[k]
        return max(self.project_cost(k) * 0.15, n["up"] * 1.0)

    # SUPERVISION, NOT OPERATION. A node's sch/art figures are what it takes to
    # BUILD the thing, and its upkeep already pays the people who run it once
    # built - so charging the full build crew against your own staff for ever
    # would be billing you twice for the same hands, and it measurably was:
    # Rome fell from half its runs reaching the goal to a quarter when the
    # operating cost was the whole build crew. What your own trained people
    # actually owe a going concern is supervision - somebody of yours has to
    # keep an eye on it - and that is a fraction of what it took to build.
    VENTURE_SUPERVISION = 0.25
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
    VENTURE_HANDS_PER_REVENUE = 1500.0

    def venture_hands(self, k):
        """(scholars, craftsmen) of your own that running this ties up."""
        n = self.nodes[k]
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
        if (k in self.CAPABILITY_INSTITUTIONS and n["rev"] <= n["up"]):
            return 0.0, 0.0
        f = self.VENTURE_SUPERVISION
        by_size = max(0.0, n["rev"]) / self.VENTURE_HANDS_PER_REVENUE
        return n["sch"] * f, max(n["art"] * f, by_size)

    def venture_staff_who_is_watching_what(self):
        """Which concerns are holding your people, and how many each holds.

        A play tester spent about seventy in-game years on the endgame's
        staffing and wrote: "mothballing all 259 running concerns freed zero
        scholars - about 17 are held by something the game never shows". This
        is that something, shown. Largest holder first, because that is the one
        to close.
        """
        rows = []
        for k in sorted(self.operating):
            if k not in self.nodes:
                continue
            a, b = self.venture_hands(k)
            if a > 0.005 or b > 0.005:
                rows.append({"id": k, "scholars": round(a, 2),
                             "craftsmen": round(b, 2)})
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
        for k in sorted(self.operating):
            if k not in self.nodes:
                continue
            a, b = self.venture_hands(k)
            sch += a
            art += b
        return sch, art

    # YOU ARE A PAIR OF HANDS TOO. Requiring staff for every concern, however
    # small, meant a founder with nobody could open nothing at all - not a
    # bottling shed, not an inn - and since revenue now follows what you RUN,
    # that closed the only door out of an empty household: no hands, so no
    # concern; no concern, so no income; no income, so no hands. Rome ran to
    # year 800 with 270 technologies, no craftsmen and one open concern, and
    # Norse sat solvent at 317 in hand with none. One person can keep an eye on
    # one small shop, which is exactly how every one of these fortunes started.
    FOUNDER_IS_WORTH = 1.0

    def venture_staff_free(self):
        """People you could put behind something new. You cannot run fifty
        businesses with three people, and this is the whole of why choosing
        WHICH to run is a decision rather than an accounting formality."""
        sch_used, art_used = self.venture_staff_used()
        own = self.FOUNDER_IS_WORTH if self.founder_alive else 0.0
        return (max(0.0, self.effective_scholars() - sch_used),
                max(0.0, self.artisans + own - art_used))

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
        if k not in self.done:
            return False, ("you have not worked out how to do that yet, so there "
                           "is nothing to open")
        if k in self.granted:
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
        if k in self.operating:
            if k in self.SCALABLE_INSTITUTIONS and units and float(units) > 0:
                return self._expand_institution(k, float(units), pay)
            return False, "you are already running that"
        n = self.nodes[k]
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
            u = max(0.2, float(units))
        elif scalable:
            u = getattr(self, "inst_units", {}).get(k, 1.0)
        else:
            u = 1.0
        sch_free, art_free = self.venture_staff_free()
        need_sch, need_art = self.venture_hands(k)
        need_sch, need_art = need_sch * u, need_art * u
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
        fee = self.venture_capex(k) * (u if scalable else 1.0)
        # A SHOP THAT LOST ITS KEEPER IS NOT A SHOP YOU HAVE TO BUILD AGAIN.
        # Staff attrition runs at 3.5% a year, so a household sitting near the
        # supervision line loses a concern most years and pays the full stock
        # and premises to reopen it - a play tester watched four close at once,
        # every year, and wrote that it cost them hundreds a year and they
        # could never get ahead of it. The premises are still standing and the
        # stock is still on the shelves; what was missing was somebody to
        # watch it. Reopening within a few years costs the difference, not the
        # whole thing.
        _shut = getattr(self, "shut_for_staff", {})
        if k in _shut and self.year - _shut[k] <= self.STAFF_CLOSURE_GRACE:
            fee *= 0.1
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
                                  "{:,.0f}".format(self.capital),
                                  "{:,.0f}".format(self.spending_power("buy"))))
            self.capital -= fee
        self.operating.add(k)
        self.mothballed.discard(k)
        _shut.pop(k, None)
        self.shut_for_staff = _shut
        if scalable:
            iu = getattr(self, "inst_units", None)
            if iu is None:
                iu = self.inst_units = {}
            iu[k] = u
        # WHEN THE DOORS OPENED, which is when custom starts to find you. See
        # venture_ramp: this used to read the year you worked the thing OUT, so
        # opening late skipped the ramp entirely. Reopening something you had
        # running does not restart it: the shop is known.
        _oy = getattr(self, "opened_year", None)
        if _oy is None:
            _oy = self.opened_year = {}
        _oy.setdefault(k, self.year)
        rev_now, up_now = n["rev"] * u, n["up"] * u
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
                      % (k, "" if u == 1.0 else " at %.2f of a full founding" % u,
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
        n = self.nodes[k]
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
                                  "{:,.0f}".format(self.capital),
                                  "{:,.0f}".format(self.spending_power("buy"))))
            self.capital -= fee
        iu = getattr(self, "inst_units", None)
        if iu is None:
            iu = self.inst_units = {}
        iu[k] = have + add_units
        rev_now, up_now = n["rev"] * iu[k], n["up"] * iu[k]
        return True, ("%s expanded from %.2f to %.2f units for %s denarii: it "
                      "now earns about %s a year and costs about %s to run"
                      % (k, have, iu[k], "{:,.0f}".format(fee),
                         "{:,.0f}".format(rev_now), "{:,.0f}".format(up_now)))

    def close_venture(self, k):
        """Stop running it. You keep the knowledge; you stop paying for it and
        stop being paid by it."""
        if k not in self.operating:
            return False, "you are not running that"
        self.operating.discard(k)
        self.mothballed.add(k)
        n = self.nodes[k]
        return True, ("%s closed: you stop paying %s a year and stop earning %s"
                      % (k, "{:,.0f}".format(n["up"]), "{:,.0f}".format(n["rev"])))

    # Years a shop stands with its stock and its lease while you find somebody
    # to keep an eye on it. Past that it really has been given up.
    STAFF_CLOSURE_GRACE = 6

    def close_unstaffed_ventures(self, yr):
        """Shut what nobody is left to watch, dearest to supervise first.

        Not a policy and not an automation you can switch off: it is the same
        rule `open` already applies, applied on the years after the first. A
        shop whose keeper you dismissed is a shop that stops trading, and the
        alternative - which is what the game did - is a fortune of concerns
        running themselves for ever on an empty payroll.
        """
        # HYSTERESIS. Attrition is 3.5% a year and auto_hire tracks the
        # ceiling, so the supervision balance wobbles across the line
        # constantly - and an exact comparison meant a concern closed and was
        # reopened almost every single turn for four centuries. A play tester
        # called it "endless re-opening busywork" and they were right: nobody
        # shuts a shop because they are a fortieth of a man short this spring.
        # Close only when the shortfall is a real pair of hands.
        SLACK = 0.5
        closed = []
        while self.operating:
            sch_used, art_used = self.venture_staff_used()
            own = self.FOUNDER_IS_WORTH if self.founder_alive else 0.0
            if (sch_used <= self.effective_scholars() + SLACK
                    and art_used <= self.artisans + own + SLACK):
                break
            # THE LEAST WORTH KEEPING, not the largest. This picked whichever
            # concern needed the most hands, which is very nearly the same as
            # picking the most PROFITABLE one - a break tester watched it close
            # a 600-a-year hopper wagon twice and keep a concern earning
            # nothing with identical staffing. Shut the one that returns least
            # for the people it ties up.
            # sorted(): min() over a set returns whichever equal-keyed element
            # came first in iteration order, which is not fixed.
            # ONLY WHAT ACTUALLY HOLDS HANDS. The key divides by
            # max(0.01, hands), so a concern that ties up NOBODY scored minus
            # a hundred and seventy thousand and was chosen first every time -
            # and closing it freed not one pair of hands, so the loop came
            # round and closed the next, and the next, until nothing was open
            # at all. That is how a founder who opened a school, an academy
            # and an imperial patron on the same turn had all three shut by
            # the staffing rule on the next one. You cannot answer a shortage
            # of craftsmen by closing something no craftsman was watching.
            _holders = [k for k in sorted(self.operating)
                        if self.venture_hands(k)[1] > 0.005
                        or self.venture_hands(k)[0] > 0.005]
            if not _holders:
                break
            worst = min(_holders,
                        key=lambda k: ((self.nodes[k]["rev"] - self.nodes[k]["up"])
                                       / max(0.01, self.venture_hands(k)[1]),
                                       -self.venture_hands(k)[1]))
            self.operating.discard(worst)
            self.mothballed.add(worst)
            _sfs = getattr(self, "shut_for_staff", {})
            _sfs[worst] = yr
            self.shut_for_staff = _sfs
            closed.append(worst)
        if closed:
            self.log.append((yr, "nobody left to keep an eye on %d concern%s, so "
                                 "%s closed. You still know how; reopen with "
                                 "'open' once you have the people. The premises "
                                 "and the stock stand for a few years yet, so "
                                 "reopening soon costs a tenth of what opening did"
                             % (len(closed), "" if len(closed) == 1 else "s",
                                ", ".join(sorted(closed)[:4])
                                + (" and others" if len(closed) > 4 else ""))))
        return closed

    def reopen_restaffed_ventures(self, yr):
        """Bring back what the staffing rule shut, the moment you have the
        people to watch it again - not a policy, the other half of one.

        close_unstaffed_ventures is deliberately not a policy a player can
        switch off (see its own docstring): it is the world taking back a
        concern nobody is left to watch. Three playtesters found that the
        world never gave it back, even after they hired or taught their way
        past the shortfall - reopening was `auto_open`, a SEPARATE policy
        that defaults off for a player, and the whole of "most of the mid
        and late game was a repetitive hire-then-reopen treadmill rather
        than fresh decisions" is a player retyping `open` on the same
        handful of ids every few years, for no decision at all: they had
        already decided to run this concern once, and losing a craftsman to
        attrition is not a moment that asks them to decide it again.

        So this runs unconditionally, like the rule it undoes, and it is
        careful to undo only THAT rule: shut_for_staff is set nowhere except
        close_unstaffed_ventures, so a concern a player shut on purpose with
        `mothball` never reappears on its own - that is still their call.
        """
        _shut = getattr(self, "shut_for_staff", {})
        cands = [k for k in sorted(_shut)
                 if k in self.mothballed and k in self.done and k in self.nodes]
        if not cands:
            return []
        # BEST-EARNING FIRST, same idea as auto_open_ventures: when only some
        # of what closed can be restaffed with what you have free this year,
        # what comes back first should be what is worth the most, not
        # whichever id sorts first.
        cands.sort(key=lambda k: -((self.nodes[k]["rev"] - self.nodes[k]["up"])
                                   / max(0.01, sum(self.venture_hands(k)))))
        reopened = []
        for k in cands:
            need_sch, need_art = self.venture_hands(k)
            sch_free, art_free = self.venture_staff_free()
            if need_sch > sch_free + 0.01 or need_art > art_free + 0.01:
                continue
            ok, _msg = self.open_venture(k)
            if ok:
                reopened.append(k)
        if reopened:
            self.log.append((yr, "you have the people again: %s reopen%s on "
                                 "their own, now that somebody is free to "
                                 "watch %s"
                             % (", ".join(sorted(reopened)[:4])
                                + (" and others" if len(reopened) > 4 else ""),
                                "" if len(reopened) == 1 else "s",
                                "it" if len(reopened) == 1 else "them")))
        return reopened

    # ---- A WARNING BEFORE THE DOOR SHUTS, NOT AN AUTOMATION THAT OPENS IT --
    # close_unstaffed_ventures closes a concern the moment attrition pushes
    # the household's own staff below what keeping it open needs, and
    # reopen_restaffed_ventures now (see its own docstring) brings it back
    # the moment the shortfall is made good - between them the engine already
    # does the closing and the reopening on its own. Players were clear they
    # want neither automated further: what they asked for is to SEE a closure
    # coming while there is still a year or two to react - hire, teach,
    # stop something else on purpose - in their own words, "power grid
    # supervision is within 5 craftsmen of closure." This is that sentence,
    # not a third policy: it changes nothing about who gets hired, taught or
    # shut, only what the player is told before the staffing rule decides it
    # for them.
    #
    # THE SAME SLACK BAND close_unstaffed_ventures ITSELF USES, not a fresh
    # threshold invented for this: SLACK=0.5 there is the hysteresis that
    # stops a concern flapping open and shut across an exact tie, so "room
    # before closure" has to be measured against that same cushion or this
    # would warn about a closure that was never actually imminent (or stay
    # silent until after the real threshold had already passed).
    STAFFING_WARNING_BAND = 5.0

    # THE CLIFF ITSELF, not just the approach to it. Two players independently
    # reported the same shape of surprise: a single artisan dying took a
    # concern from comfortably staffed to closed the same year, with recurring
    # income swinging from strongly positive to nothing. STAFFING_WARNING_BAND
    # already puts every concern like that inside the warning list (5 people
    # of headroom catches 1), but the headline it got was the same generic
    # "within N craftsmen of closure" whether N was 4.8 or 0.3 - it never said
    # that N here is small enough that ONE ordinary attrition event, not a
    # policy failure or a run of bad luck, is what closes it, and it never
    # said what that closure would actually cost or how to buy the room back.
    # This band is where that sharper sentence kicks in: room this thin is not
    # early warning any more, it is the edge itself.
    STAFFING_NO_SLACK_BAND = 1.0

    def staffing_closure_warnings(self, limit=3):
        """Which running concern the staffing rule would shut NEXT if
        attrition keeps biting, and how many people of slack still stand
        between here and that - see the section comment above for why this
        exists instead of a third automation.

        Silent while the household is comfortably staffed (the common case):
        only reports when the SAME margin close_unstaffed_ventures itself
        would act on has shrunk to STAFFING_WARNING_BAND or less, in
        whichever of scholars or craftsmen actually binds for that concern -
        a concern that only ever drew on scholars is not put on notice by a
        shortage of craftsmen, and the other way round.
        """
        if not self.operating:
            return []
        sch_used, art_used = self.venture_staff_used()
        own = self.FOUNDER_IS_WORTH if self.founder_alive else 0.0
        SLACK = 0.5   # close_unstaffed_ventures' own hysteresis band
        sch_room = self.effective_scholars() + SLACK - sch_used
        art_room = self.artisans + own + SLACK - art_used
        if sch_room > self.STAFFING_WARNING_BAND and art_room > self.STAFFING_WARNING_BAND:
            return []
        _holders = [k for k in sorted(self.operating)
                    if self.venture_hands(k)[1] > 0.005
                    or self.venture_hands(k)[0] > 0.005]
        if not _holders:
            return []
        # SAME ORDER close_unstaffed_ventures would close in - dearest to
        # keep, for what it ties up, first - so the concerns named here are
        # exactly the ones actually at risk, not merely the largest.
        ranked = sorted(_holders,
                        key=lambda k: ((self.nodes[k]["rev"] - self.nodes[k]["up"])
                                       / max(0.01, self.venture_hands(k)[1]),
                                       -self.venture_hands(k)[1]))
        out = []
        for k in ranked:
            sch_need, art_need = self.venture_hands(k)
            candidates = []
            if sch_need > 0.005:
                candidates.append(("scholars", sch_room))
            if art_need > 0.005:
                candidates.append(("craftsmen", art_room))
            if not candidates:
                continue
            # WHICHEVER OF ITS OWN TRADES IS SCARCEST, not whichever this
            # concern happens to need most: a concern that ties up both a
            # scholar and three craftsmen is at risk the moment EITHER pool
            # runs out, so the tighter of the two is what actually decides
            # when it closes.
            word, room = min(candidates, key=lambda c: c[1])
            if room > self.STAFFING_WARNING_BAND:
                continue
            name = self.nodes[k]["name"]
            # WHAT IT COSTS TO LOSE, in the same recurring den/yr the player
            # already judges every concern by (rev - up, the same figure
            # `ventures` and the ranking above use) - not just that it would
            # close, but whether closing it is worth reacting to.
            net = max(0.0, self.nodes[k]["rev"] - self.nodes[k]["up"])
            cost = "{:,.0f}".format(net)
            # THE COMMAND THAT FIXES IT, named, not left for the player to
            # infer from "craftsmen"/"scholars" alone - hire is always
            # sayable (STAFF_SOURCES' own reasoning: the labour market is in
            # front of you whether or not any institution is), so this is the
            # one remedy safe to name inline rather than routing through the
            # fuller, sometimes-circular advice _staff_advice gives.
            _kind = "scholars" if word == "scholars" else "artisans"
            fix = next(why for node, why in self.STAFF_SOURCES[_kind]
                       if node == "HIRE")
            one_loss_closes = room <= self.STAFFING_NO_SLACK_BAND + 1e-9
            if room <= 0.05:
                headline = ("%s has no %s free this year and is next in "
                            "line to close - that would cost %s den/yr in "
                            "recurring income. %s"
                            % (name, word, cost, fix))
            elif one_loss_closes:
                # THE MISSING CASE: no slack at all. Room here is under one
                # whole person, so losing even ONE %s of this trade - one
                # death, one who leaves - closes this outright the same
                # year, not "eventually" and not "if things get worse".
                headline = ("%s has no spare %s: losing just one more "
                            "closes it outright, costing %s den/yr in "
                            "recurring income. %s"
                            % (name, word, cost, fix))
            else:
                # THE DIRECTION OF SAFETY, UNMISTAKABLE. "is within N
                # craftsmen of closure" read, on first sight, like a
                # countdown - an England player hired more staff, watched
                # this number climb 1.3 to 2.3, and took the rise for the
                # situation getting WORSE before working out that bigger
                # here means safer. "has N spare craftsmen before it
                # closes" cannot be misread the same way: spare is
                # obviously a good thing to have more of, and it is the
                # same word the no-slack branch just above already uses
                # ("has no spare %s: losing just one more closes it
                # outright") - the two headlines now share one vocabulary
                # for the same fact instead of two that could be read as
                # opposites of each other.
                headline = ("%s has %s spare %s before it closes"
                            % (name, ("%.1f" % room).rstrip("0").rstrip("."),
                               word))
            out.append({"id": k, "name": name, "within": round(max(0.0, room), 1),
                       "of": word, "headline": headline,
                       "recurring_income_at_risk": round(net, 1),
                       "one_loss_closes_it": one_loss_closes,
                       "fix": fix})
            if len(out) >= limit:
                break
        return out

    def auto_open_ventures(self):
        """Open what plainly pays for itself, best margin first, within the
        staff and the money available. Default ON for the optimizer and OFF
        for a player, like every other automation in this game."""
        opened = []
        # BEST MARGIN FOR THE MONEY IT TIES UP, not best margin outright. When
        # what you can raise is the binding constraint - which is exactly when
        # this matters - a 400-a-year shop that opens for 60 is worth more than
        # a 3,200-a-year works you cannot afford at all.
        # sorted() is stable, so ties keep the order of the input - and the
        # input was a generator over a set. sorted(self.done) first.
        cands = sorted((k for k in sorted(self.done)
                        if self.is_venture(k) and k not in self.operating
                        and self.nodes[k]["rev"] > self.nodes[k]["up"]),
                       key=lambda k: -((self.nodes[k]["rev"] - self.nodes[k]["up"])
                                       / max(1.0, self.venture_capex(k))))
        # DEEP IN ARREARS IS NOT "IN ARREARS". Removing the old `capital <= 0`
        # gate broke the catch-22 that trapped England - a household in the red
        # could never open the shop that would dig it out - but with no gate at
        # all the optimizer borrowed to the hilt opening concerns that each
        # return a third in their first year, and Rome logged "ABANDONED 1
        # works you could no longer maintain" two hundred and six times in five
        # hundred years. Half the credit line is the line: below it you can
        # still open your way out, above it you are digging - for an
        # INSTITUTION, which is a standing bleed against money you do not yet
        # have coming in (see the caps/scalable-growth guards right below,
        # unchanged by what follows).
        #
        # A completed, ordinary, net-positive concern (`cands`, below) is a
        # different thing, and measuring it as a household-debt question was
        # the wrong quantity. A traced Rome run built `exp_trade_route_extend`
        # - cost 4,800, net +1,700/year, capex to OPEN it a further 1,800 -
        # by year 117, and this blanket return refused to so much as look at
        # it for the next ~850 years because the household owed more than
        # half its credit line, even though opening it would have cost 1,800
        # against a line of several thousand and paid for itself within a
        # year. Sunk capex earning nothing, forever, is worse for the
        # household AND its creditors than letting it open. So: gate the
        # INSTITUTIONS below on the household's arrears, same as always, but
        # let an ordinary concern answer for itself - its own payback period,
        # not the size of the hole it would be dug from - in the `cands` loop
        # near the end of this function, which already refuses (via
        # `open_venture`) anything whose capex it cannot actually raise or
        # whose supervision it cannot actually staff.
        # "open", NOT "buy", AND THE DIFFERENCE IS LOAD-BEARING. This asks
        # what could be raised for a door fee on something that pays for
        # itself in weeks, IGNORING how deep the household already is.
        # "buy" counts the debt you carry,
        # because that is the honest answer for a wage or a commission that
        # buys you nothing back. Opening an already-built, already-earning
        # concern is the one case where it must not, and the reason is
        # recorded in the test named "a completed concern that pays for its
        # own door within months opens even while deep in arrears": gating
        # this on arrears made auto_open blanket-refuse everything once a
        # household owed half its line, and a traced Rome run left
        # exp_trade_route_extend - built, net +1,700 a year - shut for about
        # 850 years. Sunk capex earning nothing, for ever.
        #
        # A consolidation pass routed this through spending_power() on the
        # reasonable-looking grounds that it was the same arithmetic written
        # twice. It is not. It is the same arithmetic answering a different
        # question, and the regression suite caught it.
        _room = self.spending_power("open")
        _deep_arrears = self.capital < 0 and -self.capital > self.credit_limit() * 0.5
        # AND THE ONES WHOSE WORTH IS NOT AT THE DOOR. A school takes 2,500 a
        # year and hands back 800, so the margin test above shuts it out for
        # ever - and a school is where twelve of your scholars come from.
        # Everything a capability is gated on has to be able to open on the
        # strength of the capability, at a loss, provided the loss is one the
        # household can actually carry. Cheapest to keep first, so a poor
        # founder gets the workshop and the local patron before the academy.
        # STILL NOTHING WHILE DEEP IN ARREARS: an institution is a standing
        # bleed against revenue the household does not have, which is exactly
        # the case the ABANDONED-206 history above warns about, and nothing in
        # this paragraph is the bug this change is for.
        caps = [] if _deep_arrears else sorted(
                      (k for k in sorted(self.done)
                       if k in self.CAPABILITY_INSTITUTIONS
                       and k not in self.operating and self.is_venture(k)
                       and self.nodes[k]["rev"] <= self.nodes[k]["up"]),
                      key=lambda k: (self.nodes[k]["up"] - self.nodes[k]["rev"],
                                     self.venture_capex(k), k))
        # WHAT IS LEFT AFTER EVERYTHING YOU ARE ALREADY COMMITTED TO. Opening
        # an institution you cannot feed is how a household ends up abandoning
        # the works it already had.
        # AN INSTITUTION IS AN INVESTMENT, AND A LENDER KNOWS IT. Requiring a
        # CURRENT surplus is what killed the first rung of the ladder. A traced
        # Rome run built workshop_first by 150 AD and never opened it once in
        # the following four and a half centuries: the workshop bleeds 900 a
        # year, the gate wanted 1,800 a year of clear surplus, and the run's
        # surplus was negative precisely BECAUSE it had no workshop, no
        # household places and no staff. Scholars sat between 0.03 and 0.37
        # against the two that atomic_theory wants, for five hundred years, and
        # Rome fell from 38% of runs reaching the goal to none.
        #
        # `start` has always been allowed to borrow, and a half-dug foundation
        # is worse collateral than a working shop. So an institution may be
        # opened against what you could RAISE and not only out of what you are
        # clearing - with two guards, because the last time this gate was
        # loosened the optimizer borrowed to the hilt and logged "ABANDONED 1
        # works you could no longer maintain" two hundred and six times in five
        # hundred years: nothing opens while you are deep in arrears, and the
        # standing bleed you take on may not outgrow a tenth of your line.
        _surplus = (self.revenue() - self.upkeep() - self.living_cost())
        _line = self.credit_limit()
        _deep = self.capital < 0 and -self.capital > _line * 0.75
        _bleed_room = max(0.0, _surplus) * 0.5 + (0.0 if _deep else _line * 0.10)
        for k in caps:
            _bleed = self.institution_upkeep(k) - self.nodes[k]["rev"]
            if _bleed <= _bleed_room:
                ok, _w = self.open_venture(k)
                if ok:
                    opened.append(k)
                    _surplus -= _bleed
                    _bleed_room -= _bleed
                continue
            # TOO DEAR AT FULL SIZE - FOUND IT SMALLER. This is the actual
            # bridge running() needed and mines already had: workshop_first
            # bled 900 a year against a surplus that was negative BECAUSE
            # there was no workshop, so the full-size gate above refused it
            # for four and a half centuries straight. A place you can only
            # afford a fifth of is still a place; institution_units below
            # 1.0 is what open_venture calls a starter founding.
            if k not in self.SCALABLE_INSTITUTIONS or _bleed <= 0:
                continue
            starter = max(0.0, min(1.0, _bleed_room / _bleed))
            if starter < 0.2:
                continue
            ok, _w = self.open_venture(k, units=starter)
            if ok:
                opened.append(k)
                _spent = _bleed * starter
                _surplus -= _spent
                _bleed_room -= _spent
        # AND CLIMB THE LADDER ONCE IT IS OPEN - BUT ONLY ON REAL MONEY AND
        # REAL DEMAND, NOT ON THE STARTER FOUNDING'S CREDIT ALLOWANCE. A break
        # tester traced Rome under captured_han_386.json straight into the
        # thing this was supposed to cure: workshop_first opened, and this
        # loop then expanded it to 4.0 units purely because `_bleed_room`
        # (which includes a TENTH OF THE CREDIT LINE, the borrowing allowance
        # the starter founding above genuinely needs to break the original
        # deadlock) looked positive most years - without ever checking
        # whether the household could actually CARRY 3,600 a year of upkeep
        # against 1,300 of revenue. Every further unit is discretionary
        # growth, not survival, and discretionary growth has no business
        # spending a bootstrap allowance meant for the one step that has none.
        # So: real cash flow only (no credit line here), and only when the
        # place is actually full enough to want more room - a household with
        # 14 people is not short of a 12-place workshop, whatever it can
        # technically still borrow.
        if _surplus > 0.01 and not _deep_arrears:
            for k in sorted(self.SCALABLE_INSTITUTIONS):
                if k not in self.operating or _surplus <= 0.01:
                    continue
                have = self.institution_units(k)
                ceiling = self.institution_unit_ceiling(k)
                room = ceiling - have
                if room < 0.05:
                    continue
                places_now = self.institution_places(k) * have
                if self.headcount() < places_now * 0.85:
                    continue        # not full enough yet to be worth more
                per_unit = self.nodes[k]["up"] - self.nodes[k]["rev"]
                # AT MOST A QUARTER OF THIS YEAR'S REAL SURPLUS, and at most
                # one further unit a year - growth, not a second bootstrap.
                afford_room = _surplus * 0.25
                step = min(1.0, room) if per_unit <= 0 else \
                    max(0.0, min(1.0, room, afford_room / per_unit))
                if step < 0.1:
                    continue
                ok, _w = self.open_venture(k, units=step)
                if ok:
                    opened.append(k)
                    _spent = max(0.0, per_unit) * step
                    _surplus -= _spent
        # A CONCERN THAT PAYS FOR ITS OWN DOOR WITHIN A SEASON OR TWO IS NOT
        # WHAT THE ABANDONED-206 HISTORY IS ABOUT. That history is ventures
        # whose capex is large against their annual net - borrow to the hilt,
        # and the debt outruns what they pay back before they even finish
        # ramping up. A venture whose capex clears inside PAYBACK_LIMIT_YEARS
        # is the opposite case: refusing it while deep in arrears leaves its
        # capex sunk for nothing, which helps neither the household nor
        # whoever it owes. `open_venture` still refuses, on its own numbers,
        # anything whose capex cannot actually be raised or whose supervision
        # cannot actually be staffed - this only widens what is even offered
        # to it while the household is deep in arrears.
        PAYBACK_LIMIT_YEARS = 3.0
        blocked = None
        for k in cands:
            # NO SECOND, STRICTER GATE. This broke out the moment capital went
            # negative, so a household in arrears could never open anything -
            # and opening a concern is the only way to stop being in arrears.
            # An England run went into the red in its first year, logged
            # "tex_horizontal_loom would earn 400 a year against 30 of upkeep
            # and is still shut: you have no money to open it with" for a
            # century, and settled its debts twenty-eight times over seven
            # hundred years. open_venture already refuses what you cannot
            # raise, and a lender will advance against a shop with stock in it
            # as readily as against half-built work.
            if _deep_arrears:
                n = self.nodes[k]
                _payback = self.venture_capex(k) / max(0.01, n["rev"] - n["up"])
                if _payback > PAYBACK_LIMIT_YEARS:
                    if blocked is None:
                        blocked = (k, ("it would take %.1f years to pay for its "
                                       "own doors, and nothing slower than %.0f "
                                       "opens while you are this deep in arrears; "
                                       "clear enough debt to cross half your "
                                       "credit line, or wait for it to look "
                                       "quicker against what you can raise"
                                       % (_payback, PAYBACK_LIMIT_YEARS)))
                    continue
            ok, why = self.open_venture(k)
            if ok:
                opened.append(k)
            elif blocked is None:
                blocked = (k, why)
        # SAY WHY THE BEST ONE STAYED SHUT. A break tester watched a concern
        # earning 150 a year against 15 of upkeep sit closed for six years with
        # the policy switched on, because auto_open threw away every refusal
        # open_venture handed it. A policy that silently declines is
        # indistinguishable from a policy that is broken.
        if blocked and not opened:
            k, why = blocked
            said = getattr(self, "_said_autoopen", {})
            if self.year - said.get(k, -99) >= 10:
                said[k] = self.year
                self._said_autoopen = said
                self.log.append((self.year,
                                 "%s would earn %s a year against %s of upkeep and "
                                 "is still shut: %s"
                                 % (k, "{:,.0f}".format(self.nodes[k]["rev"]),
                                    "{:,.0f}".format(self.nodes[k]["up"]),
                                    why or "something is in the way")))
        return opened

    def mothball_work(self, k):
        """Shut a completed work down to stop paying its upkeep.

        Three testers hit the same wall and described it the same way: deep in
        debt, the only lever the game offered was to start MORE things, because
        `stop` cancels work in progress and there was nothing at all that shut
        down a finished institution. One wrote "once you've over-built, the
        recurring cost is permanent"; another "your agency basically
        disappears". This is the missing lever. It is not free: you lose what
        the work gave you, and restoring it costs a fraction of building it.
        """
        if k not in self.nodes:
            return False, "no such node"
        if k not in self.done:
            return False, "you have not built that"
        if k in self.granted:
            return False, ("that is something the society has, not something you "
                           "maintain; there is no upkeep of yours to stop")
        # MONEY IS NOT THE ONLY THING THIS TOOL CAN FREE. This used to refuse
        # outright whenever upkeep was zero, on the theory that nothing was
        # being saved - true of the money, and false of the staff: a concern
        # with no money upkeep at all can still tie up a fraction of a
        # scholar or craftsman in venture_hands (a going concern's "your
        # people already spoken for" table), and a Mexica playtester ran into
        # exactly that: a fully-built concern short 0.01 of a craftsman it
        # needed to open, with the only 0.01 to be had sitting inside a
        # zero-upkeep practice `mothball` would not touch, on the grounds
        # there was "nothing to save" - true of the money, false of the
        # craftsman-time the player was actually short of. Ask what THIS
        # tool actually releases (money upkeep, and, if it is running,
        # supervision time) rather than asking about money alone.
        sch_held, art_held = self.venture_hands(k) if k in self.operating else (0.0, 0.0)
        if self.nodes[k]["up"] <= 0 and sch_held <= 0.005 and art_held <= 0.005:
            return False, ("that has no money upkeep of yours to stop paying, and "
                           "nobody of yours is tied up supervising it either; "
                           "there is nothing to save")
        # A DELIBERATE SHUTDOWN IS NOT AN ABANDONMENT. never_abandon exists to
        # stop the ENGINE quietly deleting a step you need and then refusing to
        # fund rebuilding it. A player choosing to close something down is the
        # opposite: they chose it, restore brings it back, and refusing them was
        # the exact trap a tester hit - the upkeep bankrupting them was the one
        # thing they were not allowed to stop paying for, which is how a bad
        # year became "an unrecoverable softlock". Knowledge still cannot be
        # unlearned; a building can always be shut.
        if self.never_abandon(k) and self.nodes[k]["cat"] in self.NEVER_ABANDON:
            return False, ("that is knowledge, or it is who you are here. "
                           "You cannot un-know a thing to save its upkeep")
        # SHUTTING A SHOP DOWN IS NOT FORGETTING HOW IT WORKED. This used to
        # discard the node from `done`, so closing a loss-maker cost you your
        # place in the tree and the warning had to say "you will have to
        # restore or rebuild it before you can go on". That was a real trap and
        # it only existed because there was nowhere else to put "built but not
        # running". There is now: what you know is `done`, what you run is
        # `operating`, and this touches only the second.
        was_running = k in self.operating
        self.operating.discard(k)
        self.mothballed.add(k)
        if not was_running:
            return True, ("%s was not running, so there was nothing to stop "
                          "paying for. You still know how to do it." % k)
        # SAY WHAT WAS ACTUALLY FREED, not only the money. A concern held
        # together by staff time alone (up<=0, sch_held/art_held>0, the exact
        # case above) used to be unreachable by this method at all; now that
        # it can be shut, the confirmation has to say so, or freeing 0.75
        # craftsmen would read as a no-op that happened to succeed.
        _freed = []
        if self.nodes[k]["up"] > 0 or self.nodes[k]["rev"] > 0:
            _freed.append("you stop paying %s a year for it and stop earning "
                          "the %s a year it brought in"
                          % ("{:,.0f}".format(self.nodes[k]["up"]),
                             "{:,.0f}".format(self.nodes[k]["rev"])))
        if sch_held > 0.005 or art_held > 0.005:
            _freed.append("it frees %.2f scholars and %.2f craftsmen who were "
                          "tied up supervising it" % (sch_held, art_held))
        return True, ("%s shut down: %s. You still know how to do it, and "
                      "'restore %s' opens it again"
                      % (k, "; ".join(_freed), k))

    def restore_work(self, k):
        """Bring a mothballed work back, and open its doors again.

        It costs about twice what `open` costs on its own, because it does two
        things: it puts the plant back up - which rotted while it stood idle -
        and it starts the concern trading. `open` alone assumes the plant is
        still there.
        """
        if k not in getattr(self, "mothballed", set()):
            return False, "you have not shut that down"
        if k not in self.done:
            return False, ('you no longer know how to do that, so there is '
                           'nothing to reopen: build it again with '
                           '{"cmd":"start","id":"%s"}' % k)
        n = self.nodes[k]
        # A FLOOR FROM THE UPKEEP, not only a share of the build cost. Thirty
        # per cent of nothing is nothing, and a node that costs nothing to build
        # while costing 20 a year to keep could be shut down and brought back
        # around the annual tick for free, which made its upkeep optional. A
        # tester did exactly that and the reply read "back in service for 0
        # denarii". The engine already gets this right for mines - `quote mine`
        # says in as many words that mothballing is not free to reverse,
        # because the shaft floods and the crew disperses - so the asymmetry
        # was an oversight rather than a decision. Two years of the upkeep you
        # avoided is what it costs to find the people and the plant again.
        fee = max(self.project_cost(k) * 0.3, n["up"] * 2.0)
        # THE SAME GRACE `open` GIVES. A concern the staffing rule shut is a
        # shop whose keeper you lost, not a work you abandoned: open_venture
        # charges a tenth to reopen one within a few years and says so in the
        # closing message, and `restore` - the verb a player actually reaches
        # for - charged the full price, which is itself double open's. A break
        # tester paid twice what the event had promised.
        _shut = getattr(self, "shut_for_staff", {})
        _in_grace = k in _shut and self.year - _shut[k] <= self.STAFF_CLOSURE_GRACE
        # SAY WHICH CASE THIS IS, not just a number. The closing message
        # promises "reopening soon costs a tenth of what opening did"; a
        # player who comes back to `restore` years later, after the grace
        # window has lapsed, was billed the full price with nothing on this
        # line connecting it to that promise or saying the window was gone.
        # A third player read this as `restore` simply not honouring its own
        # stated discount, which is the same complaint in different words as
        # the earlier double-charge: a number with no account of itself reads
        # as broken whether it is wrong or merely unexplained.
        _grace_note = None
        if k in _shut:
            if _in_grace:
                fee *= 0.1
                _grace_note = ("the staffing window is still open (shut %d "
                               "years ago, of %d allowed), so this is the "
                               "discounted tenth, not the full price"
                               % (self.year - _shut[k], self.STAFF_CLOSURE_GRACE))
            else:
                _grace_note = ("the staffing discount only lasts %d years "
                               "after a closure, and it has been %d - too "
                               "long for the tenth, so this is the full "
                               "price, the same as rebuilding the plant "
                               "from nothing"
                               % (self.STAFF_CLOSURE_GRACE, self.year - _shut[k]))
        if fee > self.spending_power("buy"):
            return False, ("bringing it back costs %s denarii%s, and between "
                           "%s in cash and what anyone will advance against a "
                           "purchase you can raise %s"
                           % ("{:,.0f}".format(fee),
                              ("; " + _grace_note) if _grace_note else "",
                              "{:,.0f}".format(self.capital),
                              "{:,.0f}".format(self.spending_power("buy"))))
        if any(p not in self.done for p in n["pre"]):
            return False, ("you no longer have what it stands on: "
                           + ", ".join(p for p in n["pre"] if p not in self.done))
        self.capital -= fee
        self.done.add(k)
        self._done_changed()
        self.mothballed.discard(k)
        # Back in service means back in OPERATION: restore is what a player
        # types to reopen something they shut, so it must put it back on the
        # books rather than leaving it known-but-closed.
        if self.is_venture(k):
            self.operating.add(k)
        return True, ("%s back in service for %s denarii%s"
                      % (k, "{:,.0f}".format(fee),
                         (" (%s)" % _grace_note) if _grace_note else ""))

    def bribe(self, amount):
        """Pay your way out of trouble, deliberately, for a stated sum."""
        amount = float(amount)
        if amount <= 0:
            return False, "amount must be greater than zero. Nothing was changed."
        if amount > self.capital:
            return False, "you have %.0f denarii" % self.capital
        before = self.scandal
        prot_before = self.protection
        # DO NOT CHARGE FOR NOTHING. This took the money and then said, in the
        # same breath, "you had no scandal to answer and are already as
        # protected as money can make you, so this bought nothing" - a break
        # tester lost 5,000 to a single mistyped command that way, with no cap
        # and no confirmation. Work out whether it would move anything BEFORE
        # taking the money, and refuse if it would not.
        if before <= 0.0005:
            spent = 0.7 * self.bribes_ytd + amount
            income = max(1.0, self.revenue())
            would = min(0.30, (spent / (income * 0.6)) * self.w["bribability"])
            already = min(0.30, (self.bribes_ytd / (income * 0.6)) * self.w["bribability"])
            if would - already < 0.005:
                # SAY WHICH IT IS. A break tester was refused `bribe 1` at 0%
                # protection and told they were "already as protected as money
                # can make you", which is false and reads as a bug. One denarius
                # buys nothing measurable; a thousand would.
                _floor = 0.005 * (max(1.0, self.revenue()) * 0.6) / max(
                    1e-9, self.w["bribability"])
                if already < 0.29:
                    return False, ("you have no scandal to answer, and %s "
                                   "denarii is too little to buy any advocacy "
                                   "worth having. About %s would begin to move "
                                   "your protection. Nothing was changed."
                                   % ("{:,.0f}".format(amount),
                                      "{:,.0f}".format(max(1.0, _floor))))
                return False, ("you have no scandal to answer and you are already "
                               "as protected as money can make you here, so this "
                               "would buy nothing. Nothing was changed.")
        # NEVER TAKE MORE THAN IT CAN SPEND. Both things a bribe buys are
        # bounded: scandal stops at zero and the protection it buys saturates
        # at 0.30. A break tester typed `bribe 1000000`, got exactly the same
        # 0% -> 32% as `bribe 100`, and was left with nothing at all - one
        # command, no cap, no warning, and the run was over. What a man cannot
        # be paid to do more of, he cannot be paid more for.
        bribability = max(1e-9, self.w["bribability"])
        for_scandal = self.scandal * 300.0 / bribability
        income = max(1.0, self.revenue())
        # spent/(income*0.6) * bribability = 0.30, solved for the carried total
        for_protection = max(0.0, (0.30 * income * 0.6) / bribability
                             - 0.7 * self.bribes_ytd)
        useful = max(for_scandal, for_protection)
        refused = 0.0
        if amount > useful + 0.5:
            refused, amount = amount - useful, useful
        self.capital -= amount
        self.bribes_ytd = 0.7 * self.bribes_ytd + amount
        self.scandal = max(0.0, self.scandal - amount / 300.0 * bribability)
        self.update_protection()
        # BOTH THINGS IT BUYS. A break tester spent 500 denarii against a
        # scandal of zero, read "scandal 0.00 -> 0.00", and wrote it down as
        # money silently burned. It was not: bribes_ytd feeds protection, which
        # is what keeps an accusation from being made in the first place. A
        # reply that names only the half that did not move is what made a real
        # effect look like a bug.
        msg = "scandal %.2f -> %.2f for %.0f denarii" % (before, self.scandal, amount)
        if refused > 0.5:
            msg += ("; %s denarii of what you offered was not taken, because "
                    "this is as far as money goes here - you kept it"
                    % "{:,.0f}".format(refused))
        if self.protection > prot_before + 0.0005:
            msg += ("; advocacy and piety bought as well: protection %.2f -> %.2f"
                    % (prot_before, self.protection))
        elif before <= 0.0005:
            msg += ("; you had no scandal to answer and are already as protected "
                    "as money can make you, so this bought nothing")
        return True, msg

    def bounty_eligible(self, k):
        """Can this be bought as a prize instead of built with your own hands?

        A public prize ("ten thousand sesterces to the first glassworker who
        brings me a clear sphere of glass the size of a millet seed") converts
        DENARII into someone else's HOURS, which is the trade you most want to
        make. It only works where the craft already exists in the Empire and the
        artisan can recognise success without understanding the theory. You
        cannot post a bounty for zone refining; nobody would know what to aim at.
        """
        n = self.nodes[k]
        if n["tier"] > 2:
            return False
        # THE ALLOW-LIST IS ROME'S CRAFTS, and it was applied to everybody. A
        # Norse tester was refused a bounty on `sea_skeleton_first` -
        # shipbuilding - by a civilisation whose own profile marks ships as the
        # thing it is best at in the world, and told "a Roman artisan could not
        # recognise success at this". So the list is now a floor, not the whole
        # rule: anything this society is measurably GOOD at (its own cost
        # multipliers say so) can be recognised by its own craftsmen, whatever
        # Rome's craft categories happen to be.
        if n["cat"] in ("glass_optics", "metallurgy", "precision", "power",
                        "agriculture", "information", "instruments"):
            return all(p in self.done for p in n["pre"])
        if self.civ_cost_factor(k) < 0.95:
            return all(p in self.done for p in n["pre"])
        return False

    def post_bounty(self, k):
        """Pay well over the odds, save 65% of your own hours, gain visibility."""
        n = self.nodes[k]
        # 2.5x the cost THIS society would actually incur, not 2.5x an
        # abstract base. A playtester found `why` quoting 188 denarii to build a
        # node while `bounty` demanded 588 for the same thing, because the
        # bounty ignored the civilization and price factors the build applies.
        price = (n["_total_cost"] * 2.5 * self.civ_cost_factor(k)
                 * self.material_cost_factor(k) * self.cost_money_factor())
        if price > self.capital:
            return False
        self.capital -= price
        self.total_spend += price
        self.bounties_paid += 1
        self.active[k] = dict(ph_left=n["ph"] * 0.35, yrs=0.0, spent=price)
        self.bountied.add(k)
        # A public prize makes you conspicuous - and that is what `scandal`
        # and `eminence` now measure. This used to also add to a `suspicion`
        # scalar that nothing ever read; see core.py's note on scandal.
        self.log.append((self.year, "posted a public bounty for %s (%s den)"
                         % (n["name"], f"{price:,.0f}")))
        return True

    def substitution_quality(self, k):
        """Resolve `req_any` groups: for each, the best option you actually have.

        A steam engine does not REQUIRE coal and steel. It requires a fuel and a
        pressure vessel. Wood in a bronze boiler works. It is just bad, and the
        quality factor is how bad: it multiplies output and divides efficiency.
        """
        n = self.nodes[k]
        groups = n.get("req_any") or []
        if not groups:
            return 1.0, True
        q = 1.0
        for g in groups:
            best = 0.0
            for opt, qual in (g.get("options") or {}).items():
                if opt in self.done or opt in self.nodes.get(k, {}).get("mat", {}):
                    best = max(best, float(qual))
                elif opt not in self.nodes:
                    best = max(best, float(qual) * 0.9)   # a purchasable commodity
            if best <= 0:
                # WHICH GROUP, AND WHAT WOULD SATISFY IT. "no viable option in a
                # required substitution group (fuel, vessel, etc.)" was the one
                # blocked-reason a play tester never decoded in a whole run: it
                # names no candidate and no fix, and the parenthesis is a guess
                # at what the group might be about rather than what it is.
                # A GROUP KEY IS A SLUG, NOT PROSE. Surfacing it verbatim put
                # "unknown_source" in front of a player, which is data, not
                # English. Say it as words.
                _gname = (g.get("name") or g.get("group") or "").replace("_", " ")
                if _gname:
                    _gname = ("an " if _gname[0] in "aeiou" else "a ") + _gname
                self._last_subst_gap = (
                    _gname or "one of the things it can be made from",
                    sorted((g.get("options") or {}), key=lambda o:
                           -float((g.get("options") or {})[o]))[:4])
                return 0.0, False        # no option in this group is available
            q *= best
        self._last_subst_gap = None
        return q, True

    def start_reason(self, k, ignore_trade=False, _memo=None, _why=True):
        """Same legality test as `can_start`, but explains a refusal instead of
        just returning False. `can_start` is a thin wrapper around this now;
        the wrapper exists because the optimizer's inner loop calls it a huge
        number of times and does not want to build a string it will discard.
        The reason text is what a PLAYER needs (human or agent): not just "no",
        but "no, because you need a local patron first".

        ignore_trade skips only the "does the trade exist" check below, so
        auto_train can ask a narrower question than "what would help
        eventually": "is THIS the one thing standing between me and starting
        this, right now?" See its use in step(), 4a2.

        _memo is is_visible()'s shared per-descent cache, passed straight
        through to the is_visible() calls below for a missing node's own
        visibility. Not this function's concern otherwise; see is_visible's
        docstring for why it exists.

        _why=False: the caller only wants the boolean (can_start, and
        is_visible's own recursive descent through this same function) and
        will throw the second element away. Every `return False, <message>`
        below becomes `return False, None` in that case, which matters
        because several of those messages are themselves built by walking
        the tree - missing_prereq_message chief among them, which calls
        is_visible on every missing prerequisite, which calls back into
        start_reason on each. None of that recursion changes the boolean
        this function is about to return; it only decides which prerequisite
        NAMES a player refusal is allowed to mention. Skipping it here is
        purely an optimisation: every branch below still runs exactly the
        same tests it always did to arrive at True/False, and only the
        prose built FROM that answer is elided. See the callers of this
        flag (can_start, is_visible) for why they are the only two that may
        pass False - every other caller (why, available, stuck, path,
        bounty, the protocol layer) still wants the sentence and so keeps
        the default."""
        if k not in self.nodes:
            return False, ("no such node" if _why else None)
        n = self.nodes[k]
        if n.get("win_condition"):
            # A THRESHOLD GOAL, NOT A PROJECT. This is measured, not built:
            # nobody ever spends hours or money on it, so it is never
            # offered as something to start, whatever its (always zero)
            # cost fields say and however satisfied its `pre` looks. It
            # completes itself the moment the live measurement crosses the
            # target - see core.py's per-year win-condition check, the only
            # other place that reads this field. See
            # win_condition_describe() for the player-facing sentence.
            #
            # win_condition_describe() is pure formatting (data.py - no rng,
            # no mutation, no log) but there is no reason to call it at all
            # when nobody will read the string it returns.
            return False, (("this is not something you build; it happens on "
                           "its own once %s" % win_condition_describe(n))
                           if _why else None)
        if k in self.done:
            # A MOTHBALLED WORK IS NOT FRESH RESEARCH, and it is not "already
            # done" either: you know how, and the plant is gone. `restore` puts
            # it back at a fraction of the cost, and this branch used to sit
            # BELOW the flat "already done" that swallowed it - reachable only
            # in the one state where its advice was wrong.
            if k in getattr(self, "mothballed", set()):
                # project_cost() is pure (no rng, no log, no mutation - see
                # its own docstring and the factor functions it calls) but
                # it is real arithmetic over several factor tables, and
                # nobody reads the number when _why is False.
                return False, (("you built this once and let it go; you already "
                               'know how, so restoring it is cheaper than '
                               'starting over: {"cmd":"restore","id":"%s"} for '
                               "about %.0f denarii"
                               % (k, self.project_cost(k) * 0.3)) if _why else None)
            return False, ("already done" if _why else None)
        if k in self.active:
            return False, ("already active" if _why else None)
        # NOT DEAR HERE, IMPOSSIBLE HERE. See SocietyMixin.needs_first.
        # needs_first() itself is always called: `_nf` IS the answer, not
        # just words about it. Only the sentence built from the two strings
        # it hands back is skippable.
        _nf, _why_nf = self.needs_first(k)
        if _nf:
            return False, (("%s. Build %s first and this opens with it"
                           % (_why_nf, _nf)) if _why else None)
        # A MOTHBALL ENTRY WITHOUT THE KNOWLEDGE IS A STALE ENTRY, and it falls
        # through to the ordinary checks below. Refusing here and sending the
        # player to `restore` - which answers "you no longer know how" - was a
        # deadlock no verb could clear: a play tester lost
        # precision_three_plate to a sack and watched `available` read "0
        # startable now" for a hundred and eighty years, because that node
        # gates the whole precision branch.
        # Tier 9 once meant UNOBTAINABLE: rubber, quinine, New World crops. That
        # concept was abolished, because nothing is unobtainable, only elsewhere,
        # and the tree now routes those through exp_* expedition nodes instead.
        # The guard stays only to stop a stray tier 9 from a new branch file
        # silently making a technology permanently unbuildable; treetool now
        # retiers them on merge, so this should never fire.
        if n["tier"] == 9 or n["cat"] == "unobtainable":
            return False, ("retired category: unobtainable in this tree"
                           if _why else None)
        if self._is_foreign_only(k):
            return False, (("that is an institution of a different society. %s has "
                           "no such thing, and it is not something you can build "
                           "here" % self.civ.get("name", "this society"))
                           if _why else None)
        missing = [p for p in n["pre"] if p not in self.done]
        if missing:
            # NAME ONLY WHAT YOU HAVE HEARD OF. A tester wrote a twenty-line
            # crawler that did nothing but read this message, and mapped 163
            # nodes - the entire ancestor closure of the transistor - in eight
            # rounds, while `why` and `path` dutifully refused every one of them.
            # Fog that one error message undoes is not fog. The formatting
            # itself lives in missing_prereq_message (fog.py) now, shared with
            # `bounty`, so there is exactly one fog filter for this sentence
            # rather than one per caller.
            #
            # THIS is the call the profiler found: missing_prereq_message
            # calls is_visible() on every missing prerequisite, which
            # recurses back into start_reason on each - a full descent
            # through the tree purely to decide which of these ids a fogged
            # player is allowed to be told. `missing` (the boolean-relevant
            # part - there ARE missing prerequisites) is already known
            # above; only the message about which ones is skippable.
            return False, (self.missing_prereq_message(missing, _memo=_memo)
                           if _why else None)
        if not self.substitution_quality(k)[1]:
            # substitution_quality(k) ITSELF is always called, above - it is
            # not just words, it sets self._last_subst_gap as a side effect
            # (read a few lines down) and its second return value is the
            # actual test this branch is on. What is skippable is only the
            # _seen filter below, which calls is_visible() on every option in
            # the gap (another recursive descent), and the sentence built
            # from it.
            if not _why:
                return False, None
            _grp, _opts = getattr(self, "_last_subst_gap", None) or (None, [])
            _seen = [o for o in _opts
                     if o not in self.nodes or self.is_visible(o, _memo=_memo)]
            return False, ("this needs %s and you have none of the things that "
                           "would serve%s"
                           % (_grp or "a material or a vessel it can be built "
                                      "around",
                              (": any of " + ", ".join(_seen) + " would do")
                              if _seen else
                              ", and none of them is anything you have heard "
                              "of yet"))
        # A playtester hit a scholar wall that stopped ALL progress and reported
        # that nothing in the protocol told them how to get more scholars. The
        # refusal named the shortfall and not the remedy, which is the least
        # useful half. Staff is not a technical prerequisite so it never appears
        # in `path`, and the player had no way to discover the answer except by
        # reading prose they had no reason to think was relevant.
        # Arrears blocks NEW commitments, with two escape hatches, because
        # without them this is a trap rather than a setback. A playtester went
        # bankrupt, had a prerequisite abandoned out from under them, and then
        # could not rebuild it: they sat softlocked for 470 years until the
        # horizon. First hatch: creditors care about PERSISTENT insolvency, not
        # one bad year. Second: anything you can fund from this year's income
        # needs nobody's permission.
        # "Cheap enough to need nobody's permission" means payable out of what
        # is actually LEFT, not out of turnover. Measured against gross revenue
        # it let a bankrupt household with 11,637 of income and 6,020 of upkeep
        # start 11,000-denarius projects every year for two centuries, each one
        # halted by the creditors a year later: 18 technologies in 200 years and
        # a log that was nothing but CREDIT EXHAUSTED.
        # COMPUTED ONLY WHEN IT CAN MATTER. revenue() walks every technology you
        # have, and start_reason is called for every node in the tree, several
        # times over, by can_start and by is_visible under fog. A 45-year
        # fogged Mexica run made 335,276 calls to revenue() from here and spent
        # 38 of its 100 seconds inside them - to compute a surplus that is only
        # read when the household has been insolvent three years or more, which
        # in most runs is never.
        # A CREDIT FREEZE HAS TO APPLY TO THE PLAYER TOO. It was set when the
        # creditors halted your work and then only ever checked in the
        # optimizer's own start loop, so a person at a keyboard could default,
        # be frozen out on paper, and carry on borrowing and starting things
        # regardless. A weird-play tester found the consequence: creditors
        # seize CONCERNS, so a player who opens none can default over and over
        # for nothing but reputation, which regenerates - and building raises
        # reputation, which raises the credit limit. They financed 22
        # technologies with money that did not exist and kept all of it.
        if self.year < getattr(self, "credit_frozen_until", 0):
            # SAY IF IT WILL NEVER LIFT IN TIME. A break tester was told credit
            # would return in 609 in a game whose horizon is 600, which is not
            # a date, it is the end of the run wearing a date's clothes.
            _end = getattr(self, "end_year", None) or (
                self.cfg["start_year"] + self.cfg["horizon_years"])
            return False, (("nobody here will fund new work: your creditors were "
                           "left unpaid and the word is out. They will deal with "
                           "you again in %d%s, and until then you may finish what "
                           "is running, and pay for something out of money you "
                           "actually hold."
                           % (int(self.credit_frozen_until),
                              " - which is past the horizon at %d, so not within "
                              "this run" % int(_end)
                              if self.credit_frozen_until > _end else ""))
                           if _why else None)
        if getattr(self, "insolvent_years", 0) >= 3:
            surplus = (self.revenue() - self.upkeep() - self.living_cost()
                       - self.mine_operating_cost())
            cheap_enough = (self.project_cost(k) <= max(600.0, surplus * 2.0))
        else:
            cheap_enough = True
        if (getattr(self, "insolvent_years", 0) >= 3
                and not cheap_enough
                and self.capital < -max(4000.0, self.revenue() * 2.0)):
            return False, (("you have been in arrears %d years and are %.0f denarii down; "
                           "nobody will fund a new undertaking of this size. Something "
                           "you can pay for out of this year's income is still allowed, "
                           "so is finishing or stopping what is running."
                           % (getattr(self, "insolvent_years", 0), -self.capital))
                           if _why else None)
        if n["sch"] > self.effective_scholars():
            # _staff_advice is pure (labour.py: no rng, no log, no mutation -
            # it only reads is_venture/is_visible/nodes/artisans/scholars),
            # but it walks STAFF_SOURCES and can itself call is_visible, so
            # it is skipped along with the rest of the sentence.
            return False, (("needs %d trained scholars, you have %.1f (you are one of them). %s"
                           % (n["sch"], self.effective_scholars(), self._staff_advice("scholars")))
                           if _why else None)
        # CRAFTSMEN YOU HAVE UNDER CONTRACT COUNT TOO. This read self.artisans
        # alone, so work you had already paid an outside shop to do could not
        # satisfy the requirement - and the refusal's own advice was to go and
        # commission it. `commission` could not unblock the gate that
        # recommended commission.
        #
        # It is also what deadlocked an entire civilisation. A Norse run ended
        # at year 1500 with 31,068 denarii, 136 technologies and 1.6 craftsmen,
        # unable to build workshop_first because it needs 2 - while every
        # institution that would raise the staff ceiling (freedman_staff,
        # collegium_licensed, school_founded) needs workshop_first first. You
        # needed two craftsmen to build the place craftsmen work, and could
        # never get to two. The Norse reached the goal in 0% of runs.
        #
        # Buying a jobbing carpenter for a season to raise your workshop is
        # what a person in this position actually did.
        if n["art"] > self.craft_hands_available():
            # A SHARE OF A YEAR, NOT ONLY BODIES. craft_hands_available()
            # adds hours already bought under contract as that fraction of
            # one more craftsman's year (see its own docstring: "a year of
            # a carpenter's time IS a carpenter") - so the figure below can
            # be fractional even when every actual person on the payroll is
            # a whole one. Said inline, not left for the player to work out
            # from a number that otherwise looks like a body cut short.
            return False, (("needs %d trained craftsmen, and you have %.1f - "
                           "counting people on your staff plus any hours "
                           "already bought under contract as that share of "
                           "one more. %s"
                           % (n["art"], self.craft_hands_available(),
                              self._staff_advice("artisans")))
                           if _why else None)
        # THE TRADE HAS TO EXIST. A node wanting 450 hours of an engineer cannot
        # be built by smiths, and in 100 AD there is no such person as a private
        # engineer: the wage table says so itself. You make one by teaching one.
        absent = [] if ignore_trade else sorted(t for t in n["lab"]
                                                if not self.trade_available(t))
        if absent:
            return False, (("this needs %s and there are none in this society. "
                           'Teach one: {"cmd":"train","trade":"%s","n":2} '
                           "(about 450 of your own hours each, two years)"
                           % (", ".join(a + "s" for a in absent), absent[0]))
                           if _why else None)
        # AND SOMEBODY HAS TO BE LEFT. A trade you taught still counts as
        # existing after the last of them has died or been poached, so `why`
        # and `available` said CAN START NOW while the project, once begun,
        # counted down four years and was abandoned with the spend lost - the
        # trade check asked whether the trade existed and never whether anyone
        # could be had. A play tester lost six projects in one year to it and
        # could only find out by starting them.
        # People already being TAUGHT count: they will be ready, and starting
        # work that lands the year they qualify is the right thing to do.
        _none_left = [] if ignore_trade else sorted(
            t for t, want in (n["lab"] or {}).items()
            if want > 0 and self.market_supply(t) <= 0.0
            and self._trade_headcount_pending(t) <= 0.0)
        if _none_left:
            return False, (("this needs %s and there is not one left here to do "
                           "it: you taught the trade and nobody is currently "
                           'holding it. {"cmd":"train","trade":"%s","n":2} makes '
                           "more, or hire from your own if you have any"
                           % (", ".join(a + "s" for a in _none_left), _none_left[0]))
                           if _why else None)
        # SOCIAL APPROVAL GATE. Some things the State does not want built, and no
        # amount of money substitutes for someone powerful being willing to be
        # associated with it. See 03_SOCIAL_POLITICS.md section 4.
        # SOCIAL APPROVAL. Computed from this civilization's values and this
        # technology's traits, not from a number baked into the technology.
        # Never let the gate ask for a thing in order to get that same thing:
        # the patronage and institution nodes are how you BUY permission, so they
        # cannot themselves require permission.
        if n["cat"] in ("social", "institution", "foundation", "capability", "material"):
            return True, None
        si = self.state_interest(n)
        # state_interest() itself is always computed, above: it decides the
        # branch. _patron_advice, below, is not - it is pure (no rng, no
        # log, no mutation: see its own docstring) but it can call
        # is_visible() on a prerequisite chain, which is another recursive
        # descent nobody needs when only the boolean was asked for.
        if si < -0.4 and not self.running("patron_local"):
            # NAME THE NODE, by the word you would type. "Get at least a local
            # patron first" was the whole message, and a play tester who read
            # it several times never connected it to `patron_local`, which was
            # sitting startable in the list in front of them the entire time.
            #
            # BUT ONLY IF THEY HAVE HEARD OF IT. A Mexica play tester read this
            # exact line in `available`, typed the command it gave them, and
            # was told "you have never heard of any such thing" - by the same
            # engine, one command later. Naming an undiscovered id here is the
            # third instance of one filter living in one place: start_reason
            # had it, `bounty` skipped it, `why` leaked another node's id
            # through a kb path, and this line skipped it too. The advice is
            # worth nothing when the command it gives is refused, and under
            # fog it is worse than nothing, because it is a free reveal.
            return False, (("the state is wary of this (state interest %.1f); "
                           "%s"
                           % (si, self._patron_advice("patron_local",
                                                      "a local patron's name "
                                                      "behind you")))
                           if _why else None)
        if si < -1.2 and not (self.running("patron_senatorial") or self.protection > 0.45):
            return False, (("the state actively opposes this (state interest "
                           "%.1f); %s, or protection above 0.45 (you have "
                           "%.2f)"
                           % (si, self._patron_advice("patron_senatorial",
                                                      "patronage at the very "
                                                      "top"),
                              self.protection))
                           if _why else None)
        return True, None

    def _patron_advice(self, k, in_world):
        """What to tell a player who needs `k` before they may begin.

        The id and the command only when they have heard of it; the same
        advice in plain words when they have not, which under fog is most of
        the time this fires. `in_world` is that plain-words version.
        """
        if not self.is_visible(k):
            return "you will need %s before anyone here will let you begin" % in_world
        if k in self.done:
            return ("get %s: you have built it already, so 'open %s' to put "
                    "it behind you" % (in_world, k))
        # AND IT HAS TO BE STARTABLE, or this is still a refusal recommending
        # a refusal. patron_local itself needs identity_cover, so even with
        # the fog off, "get a local patron first: 'start patron_local'" sent
        # the player straight into "missing prerequisites: identity_cover".
        # Prerequisites read directly rather than through start_reason,
        # because this is called FROM start_reason and a second entry into it
        # is a recursion this line does not need: the missing-prereq case is
        # the one that actually bit, and the fog filter for naming them
        # already exists.
        missing = [p for p in self.nodes[k]["pre"] if p not in self.done]
        if missing:
            seen = [p for p in missing if self.is_visible(p)]
            return ("get %s first, which itself wants %s"
                    % (in_world,
                       ", ".join(seen) if seen
                       else "something you have not heard of yet"))
        return "get %s first: 'start %s'" % (in_world, k)

    def can_start(self, k, _memo=None):
        # _why=False: this discards the message anyway, and it is the
        # optimizer's own per-year loop that calls this for every node in
        # the tree - the single hottest path in the engine (see
        # start_reason's own docstring on _why for what this skips).
        return self.start_reason(k, _memo=_memo, _why=False)[0]

    def start_project(self, k):
        """PLAYER-CHOSEN start. This is the whole reason `--manual` and the
        `agent` JSON protocol exist: the old `play` command let you type a
        node id, but all that did was move it to the front of `order`, the
        list the OPTIMIZER in step() still walked on its own; the optimizer
        went on starting whatever ELSE it wanted that year regardless of what
        you typed. You never actually chose anything, you only nudged a
        priority queue you did not otherwise control. This method is the real
        thing: it applies the same legality check as the optimizer
        (`start_reason`), and if it passes, THIS is the only place besides the
        optimizer's own loop that ever adds to `self.active`. In `--manual`
        mode the optimizer's loop is switched off entirely (see step(), 4b),
        so this becomes the only way anything ever starts.
        """
        ok, why = self.start_reason(k)
        if not ok:
            return False, why
        # YOU MAY COMMIT PAST WHAT YOU HOLD, AND NOT PAST WHAT ANYONE WILL LEND.
        # `help economy` states exactly that contract, and nothing enforced the
        # second half. A break tester started all 104 available projects in a
        # fresh England game - 43,914 denarii of work in hand against 400 in
        # cash and a displayed credit limit of 1,503 - and was at -3,672 one
        # step later. Committing to something you cannot yet afford is
        # realistic project accounting and stays; committing to thirty times
        # what anyone will advance you is not a plan, it is an accounting
        # fiction, and the limit the player read a second earlier has to mean
        # something.
        price = self.project_cost(k)
        # WHAT IS LEFT TO PAY, not the whole bill. Money already sunk into this
        # node - by you stopping it, or by the creditors stopping it - comes
        # off, and testing against the gross would refuse a project that is
        # nearly paid for. See stop_project.
        _paid_now = min(price, max(0.0, (getattr(self, "paid_towards", None)
                                         or {}).get(k, 0.0)))
        price -= _paid_now
        # sorted(): summing floats over a dict whose keys came from a set.
        owed = sum(st.get("cost_left") or 0.0
                   for st in (self.active[x] for x in sorted(self.active)))
        ceiling = max(0.0, self.capital) + self.credit_limit()
        # `self.active and` used to guard this, which exempted the FIRST
        # project from the only affordability test there is. A break tester
        # took tx2_watch_case at 17,415 denarii on 400 in cash and 1,367 of
        # credit because it was their opening move, then found the identical
        # command refused - quoting the shortfall exactly - after they had
        # started a five-denarius project first. Two insolvencies, 1,306 in
        # interest and reputation from 5 to 0.2 later, nothing was built.
        if owed + price > ceiling:
            return False, ("you already owe %s denarii on work in hand; this "
                           "would take it to %s, and between cash and credit "
                           "you can raise %s. Finish or stop something first."
                           % ("{:,.0f}".format(owed), "{:,.0f}".format(owed + price),
                              "{:,.0f}".format(ceiling)))
        n = self.nodes[k]
        # CREDIT FOR WHAT YOU ALREADY PAID. See enforce_credit_limit: when the
        # creditors stop a project the money already sunk into it is kept
        # against the node, and this is where it comes back off the bill.
        _paid = getattr(self, "paid_towards", None) or {}
        _paid.pop(k, None)          # spent once; the figure is _paid_now above
        _already = _paid_now
        # A THING YOU ARE REBUILDING IS NOT A THING SITTING IDLE. If the
        # knowledge was destroyed and only the mothball entry survived, that
        # entry is stale the moment you begin again - and while it stands,
        # `available` hides the node and `restore` claims it can reopen it.
        self.mothballed.discard(k)
        # lab_left STARTS FULL, SET HERE - not lazily the first time
        # lab_year_draw runs. step() reduces ph_left for THIS year before it
        # ever reaches the labour section, so a lazy init reading ph_left at
        # that point sees a project already most of the way through its
        # founder-hours and (wrongly) concludes the hired-labour total must be
        # nearly done too. Setting the real total here, before any of that
        # runs, is what fixed it.
        self.active[k] = dict(ph_left=float(n["ph"]), yrs=0.0,
                              spent=_already, cost_left=price,
                              lab_left=dict(n["lab"]))
        if _already > 0.5:
            self.log.append((self.year, "%s begun again; the %s denarii already "
                                        "paid on it before comes off the bill"
                             % (k, "{:,.0f}".format(_already))))
        # Director hours in step() 5 are handed out by priority in `order`.
        # A thing you just chose to work on should get first call on your own
        # hours, exactly as the old (cosmetic) reprioritisation implied it did.
        if k in self.order:
            self.order.remove(k)
        self.order.insert(0, k)
        return True, None

    def stop_project(self, k):
        """Stop a project you started. Your HOURS are gone; the money stands.

        This used to burn both, "same as a real abandoned enterprise", and a
        break tester pointed out what that does to the decision: when the
        creditors are about to take everything, stopping something yourself
        costs exactly as much as letting them, so no branch saves you and
        `stop` is never the right move. The site does not un-dig itself either
        way. What you paid stands against the node - the same credit
        enforce_credit_limit keeps - and comes off the bill if you begin again.
        The hours really are gone: that is your year, and you spent it.
        """
        if k not in self.active:
            return False, "not active"
        st = self.active.pop(k)
        self.bountied.discard(k)
        _paid = getattr(self, "paid_towards", None)
        if _paid is None:
            _paid = self.paid_towards = {}
        kept = max(0.0, st.get("spent", 0.0))
        if kept > 0.5:
            _paid[k] = _paid.get(k, 0.0) + kept
        return True, ("stopped. The %s denarii already paid stands to your "
                      "credit and comes off the bill if you begin again; the "
                      "hours are gone" % "{:,.0f}".format(kept)
                      if kept > 0.5 else "stopped; nothing had been paid yet")

    # -- main loop ----------------------------------------------------------

    # A HIRED TRADE'S HOURS ARE A TOTAL, NOT A TOLL DUE EVERY YEAR. Before this,
    # a project wanting 1,200 smith-hours over a 4-year calendar floor demanded
    # exactly 300 a year, every year, whatever the trade could actually supply:
    # three smiths free or thirty, it drew the same 300 and wasted the rest. A
    # break tester asked the obvious question about it: "why do some researches
    # require a labor hours/year? Could you not spend half as much for twice as
    # long? I can see labour being a CAP - you can't do a billion hours in a
    # year - but a company being unable to spend twice as much for half as long
    # feels wrong." Both halves were right, and lab_year_draw is the honest
    # shape of the constraint: a TOTAL (n["lab"][t], drawn down in
    # st["lab_left"]), a per-year CEILING somewhat above the pace the node was
    # calibrated at (a site has only so many benches, so extra hands beyond a
    # multiple of that still go to waste), and a maximum calendar SPAN past
    # which the undertaking is abandoned rather than left to drift for
    # centuries - see lab_max_span just below for what that span is and why.
    #
    # A site can field more than its calibrated crew, but not without limit.
    LAB_CREW_RATE_MULT = 4.0

    def project_hour_pace(self, k):
        """How many of YOUR OWN hours active project `k` would draw this year
        if nothing else competed for the pool - step()'s own uncapped want,
        read here rather than re-derived, so anything reporting on it before
        the allocation runs (the 'work' warning below) cannot silently
        disagree with what step() actually offers.
        """
        st, n = self.active[k], self.nodes[k]
        # THE THROTTLE IS NOT APPLIED HERE, and must not be. step() spends
        # `min(remaining, this) * throttle`, and folding the throttle in
        # changes that to `min(remaining, this * throttle)`, which is a
        # different number whenever the founder's remaining hours are the
        # binding term: at remaining 100, a want of 500 and a throttle of
        # 0.5, the first gives the project 50 hours and the second gives it
        # 100. That is the material-shortage brake silently ceasing to apply
        # in exactly the case it matters most, a busy year with the founder
        # stretched thin, and no check in this suite caught it. What this
        # returns is the project's WANT; every caller applies the brake for
        # its own purpose.
        return max(st["ph_left"], n["ph"] / max(n["yrs"], 1.0))

    def active_hours_still_wanted(self):
        """{project id: hours} for every active project that would still like
        a real amount of your own time this year, at the pace project_hour_
        pace gives it - not what it will actually get (that depends on how
        many other projects are ahead of it in the pool this year), just what
        it is still asking for. Sorted iteration: this feeds a caller that
        may sum or rank it, and self.active's own order is not fixed.
        """
        out = {}
        for k in sorted(self.active):
            if k not in self.nodes:
                continue
            pace = self.project_hour_pace(k)
            if pace > 0.5:
                out[k] = pace
        return out

    def lab_max_span(self, k):
        """The most years a project may spend trying to find enough of a
        hired trade before it is given up on.

        Forty years is a working lifetime - the span between becoming
        competent at a trade and retiring from it - and no single human
        undertaking should be allowed to out-live the people who began it:
        past that, the people who understood the early stages are dead or
        have moved on, and continuing is not finishing the same project, it
        is starting a new one that happens to reuse the site. A
        node whose OWN calendar floor (n["yrs"]) is already longer than ten
        years is one this tree already marks as diffusion-limited rather than
        personal - see core.py's POP_TECH_RAMP_YEARS and the `floor` logic in
        step() - so it earns proportionately more room, to a ceiling of four
        times its own floor rather than an unbounded one.
        """
        n = self.nodes[k]
        return max(40.0, float(n["yrs"]) * 4.0)

    def _effective_lab_left(self, k, st):
        """What is left of each hired trade's total for active project `k`,
        read-only: never writes st["lab_left"], unlike lab_year_draw (the
        only place that is allowed to initialise it for real, because doing
        so is itself a decision - the guess below - that should happen once
        per project, not once per caller that wants to look).

        AN OLD SAVE NEVER TRACKED THIS FIELD. The best guess available is
        that the same share of each trade's total is left as is left of the
        founder-hours total - generous rather than punitive: a project nine
        tenths done on its own hours is assumed nine tenths done on its
        hired hours too, not reset to owing the lot.
        """
        lab_left = st.get("lab_left")
        if lab_left is not None:
            return lab_left
        n = self.nodes[k]
        _left_frac = min(1.0, st.get("ph_left", n["ph"]) / max(1.0, n["ph"]))
        return {t: want * _left_frac for t, want in n["lab"].items()}

    def trade_draw_plan(self, k, lab_left=None):
        """What project `k` would like to draw from each hired trade this
        year, if the trade could supply it without limit - the DEMAND side
        of lab_year_draw's per-trade loop, read-only and with no knowledge of
        what any OTHER project wants or what the trade can actually supply.

        `lab_left` is what is left of each trade's total: None means a
        project that has not started yet, so the full want is still owed.
        For an active project pass self._effective_lab_left(k, st) (or
        st["lab_left"] directly once lab_year_draw has initialised it).

        lab_year_draw calls this for nominal/ceiling/left and then clamps
        each trade to what it can actually supply this year (hours_you_can_
        call_on minus what earlier-ranked projects already took) - the
        SUPPLY side. Anything reporting the portfolio's aggregate demand
        before that allocation runs (trade_demand_vs_supply below, and the
        oversubscription check `start` runs before committing) calls this
        the same way, so a forecast and the real allocator can disagree
        about what a project GETS, never about what it WANTS.
        """
        n = self.nodes[k]
        out = {}
        for t, want in n["lab"].items():
            left = want if lab_left is None else lab_left.get(t, 0.0)
            if left <= 0 or want <= 0:
                continue
            nominal = want / max(1.0, n["yrs"])
            ceiling = nominal * self.LAB_CREW_RATE_MULT
            out[t] = {"nominal": nominal, "left": left, "ceiling": ceiling,
                      "desired": min(left, ceiling)}
        return out

    def trade_demand_vs_supply(self):
        """Aggregate, by hired trade: what this year's ACTIVE portfolio
        wants from it (summed trade_draw_plan 'desired', the same demand
        figure lab_year_draw is about to act on) against what the trade can
        actually supply (hours_you_can_call_on) - read-only, so calling this
        to look never changes what lab_year_draw later does.

        A player who had already won the game asked for exactly this, to
        see BEFORE committing to one more project: "the portfolio UI could
        make aggregate trade-hour demand vs supply easier to see" - their
        own run had one chemist left, 3,000 trade-hours a year, and a dozen
        projects each quietly assuming they would get all of it.
        """
        demand = collections.defaultdict(float)
        by_trade = collections.defaultdict(list)
        # sorted(): this feeds float sums, and self.active is a dict whose
        # key order depends on PYTHONHASHSEED.
        for k in sorted(self.active):
            st = self.active[k]
            for t, p in self.trade_draw_plan(
                    k, self._effective_lab_left(k, st)).items():
                demand[t] += p["desired"]
                by_trade[t].append(k)
        out = {}
        for t in sorted(demand):
            supply = self.hours_you_can_call_on(t)
            out[t] = {"demand_hours_this_year": round(demand[t], 1),
                      "supply_hours_this_year": round(supply, 1),
                      "oversubscribed": bool(demand[t] > supply + 1e-6),
                      "projects_drawing_on_it": sorted(by_trade[t])}
        return out

    def lab_year_draw(self, k, st, frac, hired_left):
        """This year's hired-labour draw for active project `k`.

        Returns (hh, worst, frac, abandon): `hh` is the total hired hours
        drawn this year (what step() checks against `hired_left`), `worst` is
        the worst-supplied trade's shortfall against ITS OWN historical pace
        (unchanged meaning from before: this still drives the founder-hours
        give-back in step(), because a trade that came up short really did
        waste some of the year's effort), `frac` is the money-pacing fraction,
        reduced exactly as before when a trade came up short of its own pace,
        and `abandon` is None or a reason the project should be dropped
        because it ran out of calendar (see lab_max_span above).

        Mutates st["lab_left"] and self.trade_hours_used as a side effect,
        exactly where the code this replaced did. The DEMAND side of the
        numbers below (nominal, ceiling, left) comes from trade_draw_plan,
        the same read-only formula anything reporting on the portfolio before
        this runs also calls - only the SUPPLY clamp (`have`) and the mutation
        are done here, which is the real allocation and happens exactly once
        a year, inside step().
        """
        n = self.nodes[k]
        if st.get("lab_left") is None:
            st["lab_left"] = self._effective_lab_left(k, st)
        lab_left = st["lab_left"]
        hh = 0.0
        worst = 1.0
        plan = self.trade_draw_plan(k, lab_left)
        for t, p in plan.items():
            left, nominal = p["left"], p["nominal"]
            have = max(0.0, self.hours_you_can_call_on(t)
                       - self.trade_hours_used.get(t, 0.0))
            # THE CEILING IS A CREW, NOT A CALENDAR, so take whatever of this
            # is both USEFUL (no more than is left to do) and AVAILABLE (no
            # more than the trade can actually supply this year), up to the
            # site's own headroom above its calibrated pace.
            drawn = min(left, p["ceiling"], have)
            lab_left[t] = max(0.0, left - drawn)
            self.trade_hours_used[t] = self.trade_hours_used.get(t, 0.0) + drawn
            hh += drawn
            # THE WARNING IS STILL DRAWN AT THE OLD PACE. Extra capacity above
            # the historical figure is a bonus with no penalty either way; a
            # SHORTFALL below the pace the node was actually calibrated
            # against is what give-back and "short of trade" have always
            # meant, and moving the goalposts to the new, larger ceiling would
            # warn about a shortage of hands nobody ever expected to exist.
            target = min(nominal, left)
            if target > 0:
                worst = min(worst, drawn / target)
        if worst < 1.0:
            frac *= worst
            st["short_of_trade"] = sorted(
                t for t, left in lab_left.items()
                if left > 0 and (self.hours_you_can_call_on(t)
                                  - self.trade_hours_used.get(t, 0.0))
                < min(left, n["lab"][t] / max(1.0, n["yrs"])))[:3]
        else:
            st.pop("short_of_trade", None)
        # THE DEADLINE. A trade that never clears its balance used to mean the
        # project crept forward for ever at whatever sliver of progress could
        # be found, which is how `logarithms` sat at 5.0 founder-hours for two
        # hundred and seventy-five years in a civilisation that could field
        # 8,750 scribe-hours against the 10,000 it wanted: technically still
        # moving, never actually finishing, and never SAID to have failed.
        # People die and what they knew goes with them; nothing here pretends
        # otherwise.
        if st["yrs"] >= self.lab_max_span(k) and any(v > 0.5 for v in lab_left.values()):
            unmet = sorted(t for t, v in lab_left.items() if v > 0.5)
            return hh, worst, frac, (
                "after %d years there was still not enough %s here to finish "
                "it. What was spent is lost; you still know what you learned "
                "along the way" % (int(self.lab_max_span(k)), " or ".join(unmet[:2])))
        return hh, worst, frac, None

    # ---- A FAILED ATTEMPT TEACHES YOU SOMETHING -----------------------------
    # A player who had already won the game objected to the mechanic just
    # below as it stood: a failure reset the calendar floor to zero and rolled
    # again at the SAME probability, which models a society trying the exact
    # same programme with the exact same odds as if the first attempt had
    # never happened. Their own words: "if I fail my first crystal-growing
    # programme, that failure itself teaches my engineers a huge amount. My
    # next attempt should not be probabilistically identical." They also
    # named the other half of it themselves - "the second attempt should
    # probably inherit some progress" - because a high-pressure steam system
    # or a zone-refining line is not only an engineering problem, it is a
    # SOCIAL one: workshops retooled, a workforce that has seen the process
    # once, suppliers who already adjusted, regulators or patrons who already
    # sat through the pitch. A technical failure at the end does not erase
    # that diffusion, which is most of what a long calendar floor represents
    # in the first place (see _calendar_floor_remaining's own comment on what
    # these floors are actually made of).
    #
    # So this does BOTH, because they answer two different questions the
    # player asked in the same breath: the risk term is the ENGINEERING
    # lesson (what failed, and why, is now known and will not recur in the
    # same way), the calendar term is the SOCIAL one (the groundwork already
    # laid does not have to be laid twice). Both are diminishing and both are
    # capped strictly short of removing the danger or the wait entirely -
    # "should never be free" was the explicit brief, and a mechanic that let
    # enough failures drive the risk to zero or the wait to nothing would
    # just be a slower way of removing the hazard altogether, which is not
    # what was asked for.
    #
    # RISK: multiplies the node's own base risk by a factor that starts at
    # 1.0 (attempt one is not "probabilistically identical" to anything - it
    # IS the first data point, nothing has been learned yet) and decays
    # toward RETRY_RISK_FLOOR as failures accumulate, geometrically, so the
    # first failure buys the most and every one after buys less. Floored well
    # above zero: an engineering team that has failed four times still faces
    # a real chance of failing a fifth, because "we now understand this
    # failure mode" does not mean "we have found every failure mode".
    RETRY_RISK_FLOOR = 0.40        # never cheaper than 40% of the naive risk
    RETRY_RISK_DECAY = 0.6         # each failure closes 40% of what is left

    def _retry_risk_multiplier(self, k):
        m = self.failed_attempts.get(k, 0)
        if m <= 0:
            return 1.0
        return (self.RETRY_RISK_FLOOR
                + (1.0 - self.RETRY_RISK_FLOOR) * self.RETRY_RISK_DECAY ** m)

    # CALENDAR: a fraction of the years already spent on THIS attempt is
    # banked toward the next one instead of being erased, on the same
    # diminishing, capped shape as the risk term above and for the same
    # reason - RETRY_CALENDAR_CAP is comfortably short of 1.0 so a retried
    # programme is never instantly ready, only readier than the last one.
    # Read off self.active[k]["yrs"] AT THE MOMENT OF FAILURE, not off a
    # recomputed floor: core.py's own completion gate (the reputation-
    # shrinking floor for diffusion-limited nodes) already decided how many
    # years this attempt actually took before calling here, and banking a
    # share of THAT figure keeps this consistent with whatever the floor
    # happened to be without this file needing a second copy of core.py's
    # formula that could drift out of step with it.
    RETRY_CALENDAR_CAP = 0.65      # at most 65% of the elapsed clock survives
    RETRY_CALENDAR_DECAY = 0.5     # each failure closes half of what is left

    def _retry_calendar_retain(self, k, m=None):
        # See _retry_risk_multiplier's comment on `m` - same reason, same
        # contract: the real failure count still drives every actual retry;
        # `m` only lets a projection ask about a hypothetical one.
        if m is None:
            m = self.failed_attempts.get(k, 0)
        if m <= 0:
            return 0.0
        return self.RETRY_CALENDAR_CAP * (1.0 - self.RETRY_CALENDAR_DECAY ** m)

    # CONTROL RELIEF: a player who holds a working process controller faces
    # a lower chance of failing any node whose OWN stated failure mode is
    # holding a continuous process at temperature, rate or composition - a
    # zone-refining run, a Czochralski pull, a fractional distillation, a
    # high-pressure boiler - rather than a one-shot mechanical build. This
    # answers the player who reached zone_refining with a mature economy
    # and complete prerequisites and found only dice waiting: the historical
    # mitigation for "a process you cannot hold at temperature or rate" is
    # closed-loop control (Minorsky 1922, the pneumatic three-term
    # controller, Ziegler-Nichols tuning - see ctl_pneumatic_process_
    # controller in the tree), not a bigger workshop or more capital.
    #
    # WHICH NODES QUALIFY IS DATA, NOT A LIST HERE. A node opts in by
    # carrying failure_kind: "process_control" in the tree itself - the
    # tag lives beside the other properties of the technology (risk, tier,
    # traits) in tech_tree.json / the branch files, the same place every
    # other fact about a node lives. Nine core nodes carry it today
    # (zone_refining, single_crystal, gecl4_purification, ge_reduction,
    # lead_chamber, crucible_steel, high_temp_furnace, steam_high_pressure,
    # electrolysis_industrial), chosen because each one's OWN note already
    # describes a continuous hold-at-setpoint failure character, not because
    # this function needed somewhere to point.
    #
    # BOUNDED, ON PURPOSE. CONTROL_RELIEF_FACTOR is a flat 35% cut, and nothing
    # about it depends on failed_attempts, so it neither stacks unboundedly
    # with retry-learning nor ever reaches zero by itself: a controlled
    # zone_refining run at 0.45 base risk drops to about 0.29 on a first
    # attempt, meaningfully more survivable, still a real coin's chance of
    # failing. RETRY_RISK_FLOOR is untouched (this multiplies alongside it,
    # not instead of it) so the worst case, many failures AND a controller,
    # is 0.45 * RETRY_RISK_FLOOR * CONTROL_RELIEF_FACTOR =~ 0.12, never a
    # formality. The brief was explicit that zone_refining's tension is the
    # game's best late tension and this must not remove it, only mitigate it.
    CONTROL_RELIEF_FACTOR = 0.65    # 35% off, earned, never stacks to zero
    CONTROL_RELIEF_CAPABILITY = "ctl_pneumatic_process_controller"

    def _control_relief_multiplier(self, k):
        if self.nodes[k].get("failure_kind") != "process_control":
            return 1.0
        if self.CONTROL_RELIEF_CAPABILITY not in self.done:
            return 1.0
        return self.CONTROL_RELIEF_FACTOR

    def effective_risk(self, k):
        """This node's actual chance of failing on its NEXT attempt, after
        whatever retry-learning its past failures have already bought (see
        _retry_risk_multiplier just above) AND whatever control-theory relief
        a completed process controller has earned it (see
        _control_relief_multiplier just above). Equal to the bare node risk
        the first time anything is tried, with no controller built. A screen
        quoting a node's risk once failed_attempts[k] is above zero, or once
        the controller is done, should read THIS, not the tree's bare
        n["risk"] - that number is no longer what the dice use.
        """
        return (self.nodes[k]["risk"] * self._retry_risk_multiplier(k)
                * self._control_relief_multiplier(k))

    # ---- WHAT A RISKY NODE ACTUALLY COSTS IN CALENDAR TIME -----------------
    # `effective_risk` and `calendar_floor` answer two separate questions -
    # "how likely is the next roll to fail" and "how many years before there
    # even IS a next roll" - and left a player to multiply them together by
    # hand. A player who had already won the game did exactly that by force
    # of repeated bad luck: point_contact_transistor, 45% risk and a 4-year
    # floor, failed six times running and cost "roughly two dozen years", and
    # they filed it as a node whose stated "4-year floor" was nothing like
    # its real calendar cost. A 45%-per-attempt, 4-year-floor node is not a
    # 4-year project; on the bare geometric series 1/(1-p) it is 1.82
    # attempts, and even that understates it for anything past the first
    # failure, because retry learning (RETRY_RISK_FLOOR, RETRY_CALENDAR_CAP
    # above) means neither the odds nor the clock a plain geometric series
    # assumes are the ones a second, third or fourth attempt actually faces.
    def calendar_floor(self, k):
        """Calendar years THIS attempt needs to elapse before a completion
        roll can fire at all - the SAME formula step() uses to gate
        `_complete` (see core.py, where a project's own `st["yrs"]` is
        compared against this), not a second copy of it. Diffusion-limited
        nodes (yrs >= 5) shrink as reputation grows: a civilisation that
        already does a hundred complicated things does not start the social
        diffusion of the hundred-and-first from zero credibility.
        """
        n = self.nodes[k]
        floor = n["yrs"]
        if n["yrs"] >= 5:   # diffusion-limited nodes, not physical curing
            floor = max(2.0, n["yrs"] / (1.0 + self.reputation / 90.0))
        return floor

    def expected_calendar_years(self, k, _max_extra_attempts=500):
        """Expected calendar years to SUCCEED at k, counting every retry the
        dice force - not the bare calendar_floor, and not a plain geometric
        series on the raw risk field either. A failure does not roll the
        exact same dice again: the per-attempt risk and the per-attempt wait
        both move on every subsequent attempt, so the true expectation is a
        sum over "the first i attempts all failed" with a shrinking risk and
        a shrinking wait at each step.

        THE RISK TERM IS READ FROM effective_risk(k), NEVER REIMPLEMENTED.
        effective_risk is the one place allowed to know everything that
        moves a node's odds - today that is only retry learning
        (_retry_risk_multiplier), but it is the designated home for any
        OTHER multiplier this society's own choices might someday apply
        (a capability that makes a whole family of processes more
        reliable, say), and this function has no business knowing what
        those are or duplicating how they combine. To ask "what would
        attempt i+1's odds be" for a hypothetical future i without actually
        recording a failure, this stands in for "i failures so far" by
        briefly setting failed_attempts[k] to i, reads effective_risk(k),
        and restores the real count immediately after - in a `finally`, so
        a real failure count is never left clobbered even if something
        above raises. The calendar term has no such second multiplier (see
        _retry_calendar_retain) and is asked the same way, via its own `m`.

        Three assumptions, stated because a wrong number here is worse than
        none:
        1. The calendar floor used is TODAY's (today's reputation). It can
           only shrink as reputation grows, never grow back, so if anything
           this slightly OVERSTATES the wait for a civilisation still
           climbing - never understates it.
        2. Hours and money are assumed never to bind once the floor does -
           the late-game case this was written for (a mature economy with
           nothing between it and the node but dice and the calendar). A
           project still starved of hours or cash will take longer than
           this says, for reasons this number is not trying to capture.
        3. Attempts keep retrying automatically without the project being
           manually `stop`ped in between - which is how the engine actually
           runs retries: a failure never removes a project from `active`,
           only shrinks its clock and its odds (see `_complete`).
           Stop-and-restart forfeits the banked calendar progress
           (start_project always zeroes `yrs`) while keeping the risk
           learning (failed_attempts is never reset) - a real, separate
           wrinkle, and the player's own choice, not the dice's.
        """
        floor = self.calendar_floor(k)
        i0 = self.failed_attempts.get(k, 0)
        _had_key = k in self.failed_attempts
        _active = self.active.get(k) if k in self.active else None
        total = 0.0
        survive = 1.0
        i = i0
        try:
            while True:
                if i == i0 and _active is not None:
                    # ALREADY MID-ATTEMPT: use the real elapsed clock, not a
                    # recomputed banked fraction - more honest about a
                    # project already part-way through its current attempt.
                    a = max(0.0, floor - _active.get("yrs", 0.0))
                elif i == i0:
                    # NOT ACTIVE: whether this is the very first attempt ever
                    # (i0 == 0) or a restart after a manual `stop` (i0 > 0),
                    # start_project always zeroes `yrs` - see assumption 3 -
                    # so the next attempt pays the full floor either way.
                    a = floor
                else:
                    a = floor * (1.0 - self._retry_calendar_retain(k, i))
                total += survive * a
                # STAND IN FOR "i FAILURES SO FAR", ask effective_risk, then
                # move on - the real count is restored in `finally` below,
                # not here, so an exception mid-loop can never leave it wrong.
                self.failed_attempts[k] = i
                survive *= self.effective_risk(k)
                i += 1
                if survive < 1e-12 or i - i0 > _max_extra_attempts:
                    break
        finally:
            if _had_key:
                self.failed_attempts[k] = i0
            else:
                self.failed_attempts.pop(k, None)
        return total

    def _complete(self, k):
        n = self.nodes[k]
        _risk_this_attempt = self.effective_risk(k)
        if self.rng.random() < _risk_this_attempt:
            _yrs_before = self.active[k]["yrs"]
            self.failed_attempts[k] += 1
            self.active[k]["ph_left"] = n["ph"] * 0.4
            # THE CALENDAR CLOCK IS NOT WIPED. It used to be set to 0.0
            # unconditionally, restarting the same multi-year diffusion
            # process from nothing every time - the exact complaint above.
            # Even ONE failed attempt already did real social groundwork
            # (workshops retooled, a workforce that has seen it once, a
            # regulator who already sat through the pitch), so the first
            # failure already banks a real share of the elapsed clock, not
            # zero - it is the risk term above, not this one, that has
            # nothing to show after only one failure. What this banks keeps
            # growing, with diminishing returns, as failed_attempts[k] grows,
            # and is capped well short of the whole clock (RETRY_CALENDAR_CAP)
            # so a retried programme is only ever readier, never instantly
            # ready.
            _retain = self._retry_calendar_retain(k)
            self.active[k]["yrs"] = _yrs_before * _retain
            _lost = n["_total_cost"] * 0.4 * self.cost_money_factor()
            self.capital -= _lost
            # SAY SO. The roll has always worked - 40 failures in 200 at a
            # stated 20% - and it has never once announced itself: it reset the
            # project and logged nothing, so a break tester watched about 113
            # builds, expected nine failures, found no occurrence of "fail",
            # "abandon" or "lost" anywhere in the output, and concluded the
            # whole mechanic was dead. A cost you cannot see is a cost the
            # player is not paying attention to, which is the same as not
            # charging it.
            # 40, NOT 60. ph_left is set to 0.4 of the FULL hours, so what is
            # to do again is forty per cent of the work; the line said sixty
            # and a break tester who measured the hours reported the stated
            # penalty as never charged. It was charged. The sentence was wrong.
            # AND NOW SAY WHAT WAS LEARNED, in the same breath as the loss -
            # a player who has just been told a program failed should also be
            # told, in the same sentence, that the next attempt is not a
            # repeat of this one: the engineering is better understood
            # (chance of failure quoted for next time) and some of the
            # groundwork survives (years already banked toward the next
            # attempt's own floor).
            _next_risk = self.effective_risk(k)
            _banked = self.active[k]["yrs"]
            self.log.append((self.year,
                             "FAILED at %s: it did not work. %d%% of the hours "
                             "are to do again (%s of your own) and %s is gone. "
                             "Attempt %d. What went wrong is now understood well "
                             "enough that the next attempt's chance of failing "
                             "this way is %d%%, down from the %d%% this attempt "
                             "just faced, and %.1f of the %.1f years already "
                             "spent count toward next time's wait."
                             % (n["name"], 40, "{:,.0f}".format(n["ph"] * 0.4),
                                "{:,.0f}".format(max(0.0, _lost)),
                                self.failed_attempts[k] + 1,
                                round(_next_risk * 100),
                                round(_risk_this_attempt * 100),
                                _banked, _yrs_before)))
            return
        del self.active[k]
        self.bountied.discard(k)
        # A FINISHED PROJECT CANNOT BE GIVEN MORE HOURS. Unlike stopping or
        # halting one - both of which carry what was already paid forward
        # if the player starts the same id again, see start_project's own
        # `_paid_now` - there is no "again" once it is done, so a standing
        # order aimed at this id would otherwise sit in `allocate`'s list
        # for ever, pointed at nothing.
        self.hour_allocations.pop(k, None)
        self.done.add(k)
        self._done_changed()
        self.done_year[k] = self.year
        # A technology changes the society that built it. Only for work YOU
        # completed: a society is not altered by owning something it always had.
        self.apply_tech_effects(k)
        self.reveal_from(k)
        # Visible, useful, State-approved work builds standing. Obscure laboratory
        # work does not, however important it is, which is a real and annoying fact
        # about how credibility actually accrues.
        gain = (0.6 + 0.5 * max(0.0, self.state_interest(n))
                + (1.2 if n["rev"] > 0 else 0.0) + 0.25 * n["tier"])
        self.reputation = min(100.0, self.reputation + gain)
        self.scandal += self.alarm_of(n)
        self.gov += self.state_interest(n)
        # _grant_staff, NOT a bare += on self.scholars/self.artisans. The old
        # direct assignment was overwritten out of existence the very next
        # time anything called _resync_pools() - which step() does
        # unconditionally, every year - because that function has always
        # treated self.scholars and self.artisans as computed purely from
        # self.employees. A player who founded the school under --manual (the
        # interactive protocol's only mode) read "+4 scholars" on completion
        # and a refusal naming an unchanged shortfall one step later, for the
        # single highest-leverage node in the game. See _grant_staff.
        #
        # ONLY WITHOUT auto_hire. With it on - the optimizer's default, off
        # for a player - staff_capacity() already counts this same
        # institution toward sc_cap/ar_cap and step()'s smoothing grows
        # self.scholars/self.artisans toward that ceiling on its own; the
        # long civilization runs are calibrated against that smoothing alone
        # (see core.py, "1. staff"). Granting it a second time here as well
        # double-counted every one of these three institutions and pushed a
        # 250-year optimizer run to 560 things startable where the tree is
        # calibrated to open up much more slowly - not a message that lied,
        # but the same bug's fix over-correcting into a different one.
        if not self.policy.get("auto_hire", not self.manual):
            if k == "freedman_staff":     self._grant_staff(artisans=8)
            if k == "school_founded":     self._grant_staff(scholars=4)
            if k == "academy_network":    self._grant_staff(scholars=10, artisans=10)
        if k == "mining_concession":  pass
        # SAY THAT IT IS NOT YET RUNNING. Completing something that could be a
        # going concern no longer starts it earning, and a player who is not
        # told will reasonably conclude the money is broken rather than that
        # they have not opened the doors.
        if self.is_venture(k) and not self.policy.get("auto_open", not self.manual):
            self.log.append((self.year, "completed: %s. You know how; nothing "
                                        "is earning yet - 'open %s' to run it"
                                        % (n["name"], k)))
        else:
            self.log.append((self.year, "completed: " + n["name"]))
        if k == self.goal and self.goal_year is None:
            self.goal_year = self.year

    # -- shocks -------------------------------------------------------------
    # WHAT YOU CAN DO ABOUT HISTORY.
    #
    # A tester's question, and it is the right one to ask of a game that tells
    # you on turn one exactly which disasters are coming: "some techs might
    # counter that, like what if you build a mine that can mine gold for Rome,
    # or guns for a rebellion, or medicine for disease?" Until now the answer
    # was almost no: four hardcoded checks, none of them findable, and the
    # hazards were weather. They are not weather. They are the thing the whole
    # programme is for.
    #
    # Each entry is (node id, how much of the harm it removes, what it is).
    # They compound, and none of them takes a hazard to zero on its own: no
    # amount of sanitation stops a plague, it decides how many of your people
    # are still alive at the end of it.
    HAZARD_COUNTERS = {
        "staff_loss": [
            ("sanitation_antisepsis", 0.30, "boiled water, handwashing, clean wounds"),
            ("med_quarantine_sanitation", 0.30, "quarantine, clean water, sewage"),
            ("germ_theory", 0.25, "knowing what is actually killing them"),
            ("md2_isolation_hospital", 0.20, "the sick kept apart from the well"),
            ("med_vaccination_progression", 0.45, "variolation and then vaccination"),
            ("md2_vaccine_smallpox", 0.40, "smallpox vaccine"),
            ("md2_vaccine_plague", 0.35, "plague vaccine"),
            ("md2_vaccine_typhoid", 0.20, "typhoid vaccine"),
            ("md2_sand_filtration", 0.15, "filtered water"),
            ("soap_hard", 0.10, "hard soap, in quantity"),
            ("med_nursing_profession", 0.12, "people trained to nurse the sick"),
            ("plague_preparedness", 0.35, "a plan made before the plague"),
            ("crop_rotation", 0.15, "fields that do not fail together"),
            ("ag2_silage_silo", 0.10, "fodder that keeps through a bad winter"),
            ("fud_canning_appert_method", 0.10, "food that keeps"),
        ],
        "sack_chance": [
            ("mil_trace_italienne", 0.45, "angled bastion walls no ram or ladder answers"),
            ("mil_bastion", 0.30, "a bastioned enclosure"),
            ("mil_concrete_fortification", 0.30, "concrete fortification"),
            ("mil_matchlock", 0.25, "firearms in the hands of your own people"),
            ("mil_flintlock", 0.35, "reliable firearms"),
            ("mil_artillery_piece", 0.30, "guns on the walls"),
            ("gunpowder", 0.15, "corned powder"),
            ("patron_imperial", 0.30, "a patron with soldiers"),
            ("academy_network", 0.40, "the work is in too many places to burn"),
            ("endowment_land", 0.15, "land nobody can carry away"),
        ],
        "output_factor": [
            ("endowment_land", 0.30, "land that yields whoever is emperor this year"),
            ("crop_rotation", 0.20, "you feed yourself"),
            ("water_power_scale", 0.20, "power that does not come by ship"),
            ("civ_road_paved", 0.10, "your own roads"),
            ("fin_marine_insurance", 0.15, "losses spread rather than borne"),
        ],
        "real_erosion": [
            ("_own_gold", 0.55, "your own gold, dug not minted"),
            ("_own_silver", 0.35, "your own silver"),
            ("endowment_land", 0.40, "wealth held as land, not as coin"),
            ("fin_bimetallism", 0.25, "a standard the coin can be held to"),
            ("fin_assay_office", 0.20, "you can prove what metal is in a coin"),
            ("met_fire_assay", 0.15, "you can assay ore and coin yourself"),
        ],
    }
