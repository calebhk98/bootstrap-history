"""How many trained, hired or supervised people this household may have -
and the founder's own hours, the one resource behind all of it.

Split out of labour.py (see that file's own docstring for why). These are
methods of Labour; they are a mixin only so that they can live in a file of
their own. Behaviour is unchanged and moved verbatim.

Three ceilings live here together because they answer the same question
from three different institutions: literacy bounds who a literate trade
(scholar, scribe, engineer, chemist, machinist, optician, electrician) can
ever draw from; STAFF_CAPACITY_SOURCES/staff_capacity is what schools,
patrons and heavy industry train and can afford to keep, once running;
SUPERVISION_ROOM/supervision_room is the founder's own headroom to direct
and house people beyond what any institution trained outright. hired_cap
and _staff_advice (how much an institution widens the LOCAL hiring pool,
and what to tell a player who has hit one of these walls) sit with them for
the same reason. household_room, headcount and director_hours_committed
are the small shared totals `hire`, `train` and `buy_slaves` (labour_
training.py, labour_bondage.py) all check against, so they live where the
ceilings they total up already live. director_pool and _stochastic_round
open the file because every one of these ceilings is ultimately a claim
about the founder's own scarce hours, or about rounding a continuous target
onto a whole person without biasing which way growth heads.
"""
import math

from sim.constants import declare
from . import legacy_trade_defaults, trade_data
from .wage_provider import reference_civilisation

_CRAFT_FAMILY = "craft"  # moves to legacy_trade_defaults


class _LiterateTrades:
    """The trades whose practice is reading: this world's own on an instance, the shipped set on the class."""

    def __get__(self, instance, owner=None):
        if instance is None:
            return frozenset(legacy_trade_defaults.LITERATE)
        return trade_data.literate_trades(instance._world.wages)


class CapacityMixin:
    """Literacy, institutional and supervisory ceilings on how many people
    this household may hire, teach, own or direct - see this module's own
    docstring for why these particular subjects sit together.
    """

    def _stochastic_round(self, x):
        """Round a continuous headcount target to a whole number of people
        without biasing where it is actually heading.

        PEOPLE ARE WHOLE; THE PATH TOWARD THEM DOES NOT HAVE TO BE. The
        automatic staff-growth in core.py's step() is a smoothing formula -
        this year's target minus what you have, times a rate - and that math
        is exactly what every balance comment near it was tuned against. Had
        it simply rounded the smoothed figure down every year, growth toward
        a ceiling of, say, 6 people from 0 would have sat at 5 forever
        (0.18 of the gap each year, floor()'d, converges just under the next
        whole number and never crosses it): hiring would have quietly gone
        dead a person short of every ceiling in the game. Rounding UP every
        year over-hires just as systematically the other way.
        A fractional remainder is instead spent as THIS YEAR's chance of the
        next whole person: 6.4 people is six for certain and a 40% chance of
        a seventh, drawn from self.rng so it is reproducible. Averaged over
        many years the realised headcount tracks the old fractional
        trajectory exactly, and no single year is ever asked to employ part
        of a person.
        """
        x = max(0.0, x)
        whole = math.floor(x)
        if self._world.rng.random() < x - whole:
            whole += 1
        return float(whole)

    BONDAGE_HOURS_SHARE = declare(
        "BONDAGE_HOURS_SHARE", 0.25, kind="temporary_heuristic",
        unit="fraction of founder_hours_per_year", source=None, confidence="D",
        why="What fraction of a bonded founder's day is still their own to "
            "spend, the rest being owed to whoever holds the bond. Not zero, "
            "because nobody works every waking hour and the evenings are "
            "where this model assumes the work gets done; not derived from "
            "any actual bondage contract terms, of which this engine has "
            "none, only picked so bondage costs something real without "
            "being a total stop.")

    def director_pool(self):
        total_hours = 0.0
        if self._world.state.founder.founder_alive:
            own = self._world.cfg["founder_hours_per_year"]
            # In bondage most of your hours are owed to somebody else. Not all
            # of them: nobody worked every waking hour, and the evenings are
            # where the work gets done. This is the cost, and it is temporary.
            if self._world.state.household.bondage_years_left > 0:
                own *= self.BONDAGE_HOURS_SHARE
            total_hours += own
        total_hours += self._world.state.household.directors_extra * self._world.cfg["director_hours_per_year"]
        return total_hours

    # ---- literacy bounds who you can hire ----------------------------------
    # FINDINGS_ROUND2 section Q: every civ file carries literacy_general and
    # literacy_elite, and apply_tech_effects (society.py) raises them when
    # paper, printing, schools and libraries are built. Nothing else reading
    # either number would let a scribe cost the same to hire in a society
    # where two people in a hundred could read as in one where nine could.
    #
    # `scholar` is drawn from the lettered, propertied class - literacy_elite
    # in the civ file, "fraction of the propertied class that can read". The
    # rest - `scribe`, and the trades taught into being from ordinary
    # craftsmen (`engineer`, `chemist`, `machinist`, `optician`) - draw on the
    # wider literacy_general pool of anyone who can read at all. `merchant` is
    # left out on purpose: an agent working on commission is not, in this
    # period, chiefly a reader.
    # electrician belongs in this set too: it is a taught trade that reads
    # drawings, exactly like the other four, so excluding it would let it
    # bypass the literacy ceiling that caps machinists, chemists,
    # engineers and opticians.
    LITERATE_TRADES = _LiterateTrades()

    def is_craft_trade(self, trade):
        return self._world.trade_family(trade) == _CRAFT_FAMILY
    # The literacy this file's trade shares and staff ceilings were already
    # tuned against, before literacy was read anywhere: the default
    # civilisation's own numbers, because every other constant in this economy -
    # price index, cost multipliers - is calibrated relative to it. Below
    # its own reference literacy stays 1.0 and NOTHING changes for it; a
    # civilization with less of either number gets a genuinely smaller pool,
    # in proportion, and a civilization with more (a higher elite literacy
    # than the reference) is not penalised for having read more.
    LITERACY_REFERENCE_GENERAL = declare(
        "LITERACY_REFERENCE_GENERAL", reference_civilisation()["literacy_general"], kind="initial_condition",
        unit="fraction of population able to read (general)",
        source="the default civilisation file's own literacy_general field.",
        confidence="B",
        why="The default civilisation's starting literacy_general, read here as the "
            "denominator every OTHER civilisation's literate-trade capacity "
            "is measured against, because every other constant in this "
            "economy (price index, cost multipliers) is calibrated "
            "relative to that civilisation. A real starting condition, "
            "read from its file, not an invented number.")
    LITERACY_REFERENCE_ELITE = declare(
        "LITERACY_REFERENCE_ELITE", reference_civilisation()["literacy_elite"], kind="initial_condition",
        unit="fraction of the propertied class able to read (elite)",
        source="the default civilisation file's own literacy_elite field.", confidence="B",
        why="As LITERACY_REFERENCE_GENERAL, for the lettered, propertied "
            "pool `scholar` is drawn from.")
    LITERACY_FACTOR_CAP = declare(
        "LITERACY_FACTOR_CAP", 4.0, kind="temporary_heuristic",
        unit="dimensionless multiple of the Rome-reference pool",
        source=None, confidence="D",
        why="How far a literacy_factor may rise above 1.0 for a society "
            "that has read PAST Rome's own reference literacy. Bounded so "
            "a civilisation is never treated as though it could staff an "
            "unbounded number of literate trades just because a handful of "
            "technologies nudged literacy above 0.9; the figure 4.0 is "
            "tuned headroom, not a measured ceiling on how literate a "
            "pre-modern society can get.")

    def literacy_factor(self, trade):
        """0..1: how much of this trade's usual pool this society's literacy
        can actually fill. 1.0 for anything that is not a literate trade."""
        if trade not in self.LITERATE_TRADES:
            return 1.0
        if trade == trade_data.scholar_trade():
            lit, ref = self._world.civ.get("literacy_elite", 0.0), self.LITERACY_REFERENCE_ELITE
        else:
            lit, ref = self._world.civ.get("literacy_general", 0.0), self.LITERACY_REFERENCE_GENERAL
        # NOT CLAMPED AT ONE: Rome starts AT the reference, so clamping here
        # would return exactly 1.0 for Rome for ever, no matter how much
        # printing, movable type, schools and academies raise
        # literacy_general above it - moving the specialist ceiling not at
        # all. It is the one thing the argument for printing rests on: a
        # society that reads more can staff more.
        #
        # Bounded at four, because a lettered pool cannot outgrow the town
        # without the town growing, and because the tech effects that feed it
        # are deliberately small.
        return max(0.0, min(self.LITERACY_FACTOR_CAP, float(lit) / ref))

    # "A CIVILIZATION OF 1.5 MILLION CANNOT FIELD WHAT ONE OF 65 MILLION CAN"
    # (hired_cap's own comment) - the same floor-plus-variable-share curve
    # reused everywhere in this file that a labour-market size has to shrink
    # with pop_scale (literate_capacity, hired_cap, market_supply,
    # home_town_population_estimate) rather than four independent numbers
    # that could drift apart.
    POP_SCALE_FLOOR_SHARE = declare(
        "POP_SCALE_FLOOR_SHARE", 0.25, kind="temporary_heuristic",
        unit="fraction of the reference labour market",
        source=None, confidence="D",
        why="Even the smallest civilisation this game starts (pop_scale "
            "near zero) is assumed to keep a quarter of Rome's own "
            "reference town's labour-market depth - a floor so a small "
            "society is diminished, not annihilated. Tuned, not measured: "
            "a real figure would come from how town size actually relates "
            "to specialist-trade depth, which this engine does not model.")
    POP_SCALE_VARIABLE_SHARE = declare(
        "POP_SCALE_VARIABLE_SHARE", 0.75, kind="temporary_heuristic",
        unit="fraction of the reference labour market, scaled by pop_scale",
        source=None, confidence="D",
        why="The remaining three quarters of market depth that DOES scale "
            "with pop_scale, so a full-size (pop_scale=1.0) civilisation "
            "sees the whole reference figure and a shrunken one sees "
            "proportionately less of it. Paired with POP_SCALE_FLOOR_SHARE, "
            "which the two are tuned to sum to 1.0 with.")
    SCHOLAR_MARKET_SHARE = declare(
        "SCHOLAR_MARKET_SHARE", 0.35, kind="temporary_heuristic",
        unit="fraction of hired_hours_cap_base", source=None, confidence="D",
        why="What share of the abstracted labour-market pool a scholar-"
            "family trade can draw on before literacy narrows it further - "
            "literate men are a small fraction of anywhere. Tuned to make "
            "the pre-literacy scholar ceiling feel like a real but tight "
            "wall; a real figure needs an occupational census this project "
            "does not have (see TRADE_DENSITY's own comment on the same "
            "gap for other trades).")
    LITERATE_CAPACITY_FLOOR = declare(
        "LITERATE_CAPACITY_FLOOR", 1.5, kind="temporary_heuristic",
        unit="people", source=None, confidence="D",
        why="A literate trade's hiring ceiling is ADDED to, not maxed "
            "with, this floor, so a society with almost no literate pool "
            "(Viking-age Scandinavia's rune-carvers and Latin-reading "
            "priests) still has SOMEONE findable rather than a ceiling "
            "that rounds to nobody. The rune-carver and the priest are "
            "always there; this is what makes that true numerically. "
            "Picked so the floor is real without swallowing the signal "
            "literacy_factor is supposed to carry (see this function's "
            "own docstring on why max() broke the mechanism for Norse).")

    def literate_capacity(self, trade):
        """The most people this society's literacy will EVER let you have in
        this trade, hired and taught combined - a headcount ceiling, not an
        hours one.

        `hire`'s own affordability and supervision checks say nothing about
        whether anyone who can read is available at any price; this is the
        actual wall. Read as people rather than hours, it is the same
        abstracted labour-market scale market_supply() already uses for the
        share a scholar-family trade gets (25,000 hours at full population
        scale, of which a lettered trade gets 35% before literacy narrows it
        further) - not a second population model that has to be kept in step
        with the first, but that one.

        FOR `scholar` ONLY, THIS IS NOT THE WHOLE WALL. A player who typed
        `hire scholar 12` was refused at 5.9, "ever, at any price" - and
        auto_hire, forty years later with the same civilisation, held 146.4
        scholars, because step() smoothed self.household.scholars toward
        staff_capacity()'s institutional ceiling directly and never once
        called hire() or read this function. Fixing the bypass (see step(),
        core.py) without fixing the number it now has to respect would have
        made the game worse, not better: the goal itself, and two nodes on
        the only road to it, want 25 trained scholars, and the market-share
        formula above tops out at 6.36 even after every literacy technology
        in the tree - printing, paper, a school, three academies - because
        Rome's literacy_elite starts at 0.900 and the field is capped at
        1.0. An eight per cent gain is what "a society that reads more can
        staff more" is worth if reading is the only lever, and it is not:
        the actual reason a household of one can eventually field two dozen
        literate men is that a school, an academy or an imperial patron
        hands them over ALREADY TRAINED, on the institution's own payroll -
        which is exactly what staff_capacity()'s `sc` already computes, and
        what auto_hire's own math already relies on. So the wall a person
        at a keyboard is held to is the same market-share pool PLUS
        the same institutional pool auto_hire is already trusted to grow
        toward: a city of a million cannot produce twenty-five idle
        scholars for one household to hire off the street, but it can
        certainly produce them once that household has built the school
        that trains them and the network that pays for a second and a
        third. Early game, with no such institution running, this adds
        nothing and the ceiling is exactly what it always was.
        """
        if trade not in self.LITERATE_TRADES:
            return float("inf")
        base = (self._world.cfg["hired_hours_cap_base"] * self.local_market_share()
                * (self.POP_SCALE_FLOOR_SHARE
                   + self.POP_SCALE_VARIABLE_SHARE * min(1.0, self._world.pop_scale)))
        people = base * self.SCHOLAR_MARKET_SHARE / self._world.HOURS_PER_PERSON_YEAR
        # A FLOOR OF TWO, because the unfloored number said something false.
        # Norse elite literacy is a sixth of Rome's, which took this ceiling to
        # 0.2 people: not "scarce" but "there is no such person in Scandinavia,
        # at any price, ever". That is wrong about the period. Viking-age
        # Scandinavia had runic literacy, rune-carvers who cut inscriptions for
        # hire, merchants who kept reckonings, and from the tenth century
        # priests who read Latin. What it did not have was a POOL - a body of
        # lettered men large enough to staff an institution.
        #
        # So literacy bounds the SCALE of what you can build and not whether a
        # single literate person can be found.
        #
        # ADDED, not a maximum. My first attempt floored this with max(), which
        # fixed the falsehood and broke the mechanism: the floor was larger than
        # anything Norse literacy could reach, so teaching the society to read
        # changed the ceiling not at all, for the one civilisation the mechanism
        # exists to matter for. A floor that swallows the signal is worse than
        # no floor. The rune-carver and the priest are always findable; the POOL
        # on top of them is what literacy buys, and it is what teaching moves.
        cap = self.LITERATE_CAPACITY_FLOOR + people * self.literacy_factor(trade)
        if trade == trade_data.scholar_trade():
            # THE SAME POOL auto_hire ALREADY TRUSTED. staff_capacity()'s `sc`
            # is schools, academies, patrons and the industrial cascade that
            # trains scholars outright and carries their keep on the
            # institution's own upkeep (see _grant_staff) - it is not a second,
            # looser estimate of the same thing, it is the number step() was
            # already smoothing self.household.scholars toward before this function's
            # cap ever got in the way. Zero with no such institution running,
            # which is why a fresh household still sees exactly the
            # market-share figure above and no more.
            cap += self.staff_capacity()[0]
        if trade not in self._world.trades_absent:
            cap = min(cap, self.people_who_exist(trade))
        return cap

    def _literate_wall_refusal(self, trade, cap, have):
        """The refusal hire() and train() give when literate_capacity() bites.

        SAY HOW MANY YOU CAN HAVE, NOT ONLY THAT YOU CANNOT HAVE SIX: a
        ceiling quoted as "will not supply more than 5.9 in total, ever, at
        any price" reads as being capped out entirely, even when the
        requester holds none and a smaller request would succeed. Say the
        number they should type.

        AND DO NOT BLAME LITERACY FOR A WALL IT DID NOT BUILD: "this
        society's literacy will not supply more than X" for every trade
        alike is a real description of the Norse scribe case and a false
        one of the Rome scholar case. Rome's literacy_elite starts at
        0.900 against a field capped at 1.0, so literacy itself can never
        move this ceiling by more than about eight per cent, while the
        actual quantity doing the work is hired_hours_cap_base - this
        household's own reach into the labour market - and, for scholar,
        the institutional pool literate_capacity() now folds in (see its
        docstring). Both matter; only one is literacy, and saying only
        "literacy" when the market-reach term is doing most of the work
        misleads a player into pulling the wrong lever.
        """
        _room = max(0.0, cap - have)
        _whole = int(_room + 1e-9)
        lever = (
            "Building the institutions that train scholars outright - a "
            "school, an academy, an imperial patron - is what actually "
            "moves this number; printing, paper and libraries raise "
            "literacy itself, which by itself is the smaller of the two."
            if trade == trade_data.scholar_trade() else
            "Printing, paper, schools and academies widen the pool - they "
            "raise how many people here can read, and this ceiling rises "
            "with it.")
        return ("this household's reach into the labour market for %ss "
                "will not stretch past %.1f in total, hired and taught "
                "together - not \"this society's literacy\" alone, which "
                "only narrows an already-limited reach further - and you "
                "have %.1f already (hired and still being taught). %s %s"
                % (trade, cap, have,
                   ("%d more is the most you can take right now." % _whole)
                   if _whole >= 1 else "There is no room for even one more.",
                   lever))

    def _trade_headcount_pending(self, trade):
        """People already on the books in this trade, plus people already
        being taught into it who are not ready yet - what a fresh hire or a
        fresh training run would be added ON TOP OF."""
        household = self._world.state.household
        pending = sum(row[3] for row in household.training
                      if len(row) > 2 and row[2] == trade)
        return household.employees.get(trade, 0.0) + pending

    # What each of these adds to the CEILING on people, taken from
    # staff_capacity below so the advice and the arithmetic cannot drift apart.
    # THESE ARE THE SAME NUMBERS AS STAFF_CAPACITY_SOURCES's own artisan (`ar`)
    # column below, for every node the two tables share, kept as INT here
    # (whole household places, for "%d" advice text) rather than the float
    # STAFF_CAPACITY_SOURCES needs for its own unit-scaled arithmetic - two
    # declared names per figure rather than one, so a rename or a cast can
    # never silently turn a place count into a fraction of one.
    # ROOM_SOURCES: [(node id, places)] from each node's `room_places` (MechanicsMixin).
    # fin_trial_balance, fin_company_town and fin_chain_store - the
    # organisation entries added alongside STAFF_CAPACITY_SOURCES above - are
    # deliberately NOT in ROOM_SOURCES, even though every one of them raises
    # the same ceiling every other entry here does. _room_advice's own
    # "nearest first" sort (below) ranks by CLOSURE SIZE, a proxy that holds
    # for the furnace-and-patronage tree above because a shallow node there
    # is also a cheap one. It does not hold for the finance branch: the whole
    # point of fin_chain_store's own note ("requires sophisticated management
    # and accounting") is that it is a late, expensive, 30,000-denarii
    # institution sitting only two prerequisites deep (fin_market ->
    # fin_department_store), so ranking it by closure size alone told a
    # founder with four hundred denarii in year 100 that the NEAREST way to
    # more room was a chain of department stores - a measured, not a
    # theoretical, failure of this heuristic once a second branch of the
    # tree with a different shape is let into it. The institutions
    # themselves are real (STAFF_CAPACITY_SOURCES, supervision_room); this
    # one piece of advice text is not worth teaching the sort to weigh cost
    # as well as depth for three nodes, so they are simply left unnamed here
    # - a player who builds them (for their own revenue, or for the
    # household room staff_capacity() already credits them with) still gets
    # the room; this function just never tells them to go build one.

    def _room_advice(self):
        """What raises the CEILING on people, which is not what buys people.

        The household-room refusal must not hand back _staff_advice, which
        names hiring, commissioning and buying - every one of which needs
        room you do not have. The room comes from institutions and heavy
        industry, and this has to point at those instead.
        """
        # A CLOSED ROOM SOURCE IS NOT A MISSING ONE: staff_capacity() already
        # drops a source's places the moment its venture is not running (see
        # STAFF_CAPACITY_SOURCES's must_be_running), so the advice below must
        # distinguish never-built (`k not in self.household.done`) from
        # built-but-not-running - a school built, then shut for want of a
        # supervisor, must still be named as the cheapest way back, not
        # just dropped from the count. Filtering only on `done` would tell
        # a player who hit the ceiling it had been holding up to build
        # endowment_land or court an imperial patron, instead of simply
        # reopening what they already own.
        projects = self._world.state.projects
        reopen = [(node_id, add) for node_id, add in self._world.ROOM_SOURCES
                  if node_id in projects.done and node_id in self._world.nodes and node_id not in projects.operating
                  and self._world.is_venture(node_id)]
        reopen.sort(key=lambda kv: -kv[1])
        want = [(node_id, add) for node_id, add in self._world.ROOM_SOURCES
                if node_id not in projects.done and node_id in self._world.nodes
                and self._world.is_visible(node_id)]
        # NEAREST FIRST, and nearest means how much of the tree stands between
        # you and it. Sorted on size alone this offered power_grid (+130) to a
        # founder with six places - the last node in the game, true and
        # useless - while workshop_first, one prerequisite away, went unnamed.
        def _distance(node_id):
            return len(self._world.closure(self._world.nodes, node_id) - projects.done)
        want.sort(key=lambda kv: (_distance(kv[0]), -kv[1]))
        _reopen_bit = (
            ("you already have %s, shut: reopening %s is cheaper than "
             "building anything else. "
             % (" and ".join("%s (+%d)" % (node_id, places) for node_id, places in reopen[:2]),
                "it" if len(reopen) == 1 else "them"))
            if reopen else "")
        _housing_bit = ("Housing is bought: 'buy housing N' adds N places at %s each. "
                        % "{:,.0f}".format(self._world.housing_price_per_place()))
        if not want:
            if reopen:
                return ("%sThe rest is built - or in this case, "
                        "reopened: %s'open %s'."
                        % (_housing_bit, _reopen_bit, reopen[0][0]))
            return ("%sBeyond that, room comes from institutions and heavy "
                    "industry, and you have every one of them this society "
                    "offers; what is left grows on its own as they run."
                    % _housing_bit)
        _now = [(node_id, places) for node_id, places in want if self._world.start_reason(node_id, _why=False)[0]]
        return ("%sMore room is built: %s%s. Each is somewhere for "
                "people to work and somebody to oversee them.%s"
                % (_housing_bit, _reopen_bit,
                   "; ".join("%s (+%d places)" % (node_id, places) for node_id, places in want[:3]),
                   "" if _now else " None is startable today; they are listed "
                                   "nearest first, so the first is what to work "
                                   "towards."))

    # WHO TRAINS PEOPLE, AND HOW MANY OF THEM.
    #
    # (node, scholars, artisans, directors, scales_with_units, must_be_running)
    #
    # The first nine are institutions the founder establishes: a school, a
    # licensed collegium, a patron, an endowment, a network of academies, and
    # the books that let people teach themselves. The rest are the late game's
    # own engine - each heavy industrial work trains the workforce that makes
    # the next one possible.
    #
    # scales_with_units: a second school trains a second school's worth of
    # scholars, so these are linear in institution_units (1.0 for a run that
    # never founds more than the original unit; the diminishing return lives
    # in what each further unit COSTS, see institution_unit_cost). The fixed
    # ones are singular by nature - there is one imperial patron.
    #
    # must_be_running: capacity that depends on a going concern disappears
    # when the concern does. bessemer_openhearth is the exception: a society
    # that has learned to make steel this way does not forget the men it
    # trained if one works closes.
    # Scholars/artisans/directors each institution trains outright, once
    # running - the raw figures behind STAFF_CAPACITY_SOURCES below, pulled
    # into named declarations so the table's own numbers carry provenance.
    # None of these is derived from anything physical (a real school's
    # actual graduation rate, a real patron's actual household); each is a
    # design-balance figure sized so the tree's own pacing (a school by
    # year N, an academy network by year M) feels achievable, which is
    # exactly the shape CLAUDE.md 3.4 calls a labelled heuristic rather
    # than a violation - nothing here stands in for a historical OUTCOME
    # (a wage, a price, an army size), only for an untouched mechanism
    # (how fast an institution actually trains people).

    # STAFF_CAPACITY_SOURCES: [(node, scholars, artisans, directors, scales_with_units, must_be_running)]
    # from each node's `staff_capacity` (MechanicsMixin).

    STAFF_CAPITAL_INCOME_RATE = declare(
        "STAFF_CAPITAL_INCOME_RATE", 0.06, kind="temporary_heuristic",
        unit="fraction of capital per year", source=None, confidence="D",
        why="Idle capital is treated as though it earns this much a year "
            "toward what a household can afford to pay staff, standing in "
            "for a real return on capital (lending it out, investing it) "
            "this engine does not model at the household level. Not "
            "derived from DEBT_BASE_RATE or any other rate elsewhere in "
            "the engine; picked as a plausible order of magnitude.")
    STAFF_BUDGET_SHARE_OF_SPARE = declare(
        "STAFF_BUDGET_SHARE_OF_SPARE", 0.40, kind="temporary_heuristic",
        unit="fraction of true surplus", source=None, confidence="D",
        why="Of the surplus actually left after upkeep and living costs, "
            "the share a household is willing to commit to new staff in a "
            "single year rather than holding back - a caution constant, "
            "not a measured savings rate.")
    def staff_wage_reference(self):
        """Blended annual wage of the trades that exist from the start, used
        to turn an affordability budget into a headcount."""
        wages = [self.base_annual_wage(trade) for trade in sorted(self._world.wages)
                 if trade not in self._world.trades_absent]
        return sum(wages) / len(wages) if wages else self.base_annual_wage(
            trade_data.fallback_trade(self.wage_schedule().training_years, self._world.trade_family))

    STAFF_EXTRA_HEADROOM_WEIGHT = declare(
        "STAFF_EXTRA_HEADROOM_WEIGHT", 1.35, kind="temporary_heuristic",
        unit="dimensionless", source=None, confidence="D",
        why="How much more expensive supervision_room()'s extra headroom "
            "is treated as, relative to an institutional scholar or "
            "artisan, when the same affordability budget has to cover "
            "both. Tuned so the headroom hiring does not silently crowd "
            "out institutional staffing or the other way round; not "
            "measured against any real relative cost of the two.")
    STAFF_POP_SCALE_FLOOR = declare(
        "STAFF_POP_SCALE_FLOOR", 0.45, kind="temporary_heuristic",
        unit="fraction of the institutional ceiling", source=None,
        confidence="D",
        why="Even the smallest civilisation this game starts keeps this "
            "much of the institutional staffing ceiling, so a small "
            "society is diminished rather than unable to staff anything "
            "at all - the softening this function's own comment describes "
            "after 'a first pass made every small civilization fail "
            "outright'. Tuned to that observed failure, not measured.")
    STAFF_POP_SCALE_VARIABLE = declare(
        "STAFF_POP_SCALE_VARIABLE", 0.55, kind="temporary_heuristic",
        unit="fraction of the institutional ceiling, scaled by pop_scale",
        source=None, confidence="D",
        why="The remaining share of the institutional ceiling that DOES "
            "grow with population, paired with STAFF_POP_SCALE_FLOOR (the "
            "two are tuned to sum to 1.0).")
    STAFF_POP_SCALE_EXPONENT = declare(
        "STAFF_POP_SCALE_EXPONENT", 0.35, kind="temporary_heuristic",
        unit="dimensionless exponent on pop_scale", source=None,
        confidence="D",
        why="How sub-linearly the population-scaled share of staffing "
            "capacity grows with pop_scale - a civilisation of 4.5 million "
            "can eventually staff what one of 65 million can, just more "
            "slowly, rather than never. The sub-linear SHAPE is the real "
            "claim (bigger societies are not proportionately easier to "
            "staff from); the exact exponent is tuned, not fitted.")
    DIRECTOR_SCALE_HEADROOM = declare(
        "DIRECTOR_SCALE_HEADROOM", 1.3, kind="temporary_heuristic",
        unit="dimensionless", source=None, confidence="D",
        why="Directors are allowed to reach a slightly higher fraction of "
            "their institutional ceiling than scholars/artisans do at the "
            "same affordability `scale`, on the theory that a household "
            "stretched thin still prioritises the deputies who let it run "
            "concerns at a distance. Tuned headroom, not a measured "
            "priority order.")

    def staff_capacity(self):
        """How many trained people the institution can support.

        Ceilings, not rates. You cannot teach faster than you can feed, house and
        supervise, and you cannot supervise more than your directors can reach.
        Funding matters: an institute whose income has collapsed sheds people.
        """
        # There is no floor here any more. Rome does have excellent craftsmen for
        # hire and they are reachable through market_supply() and `hire`, which
        # is a thing you do rather than a staff of four you are handed on
        # arrival and never asked for.
        base_sc, base_ar = 0.0, 0.0
        scholars = artisans = directors = 0.0
        # A SECOND SCHOOL TRAINS A SECOND SCHOOL'S WORTH OF SCHOLARS. Linear in
        # institution_units, which is 1.0 for a run that never founds more than
        # the original single unit - exactly the constants below, unchanged -
        # and the actual capacity a further unit buys otherwise. The COST of
        # each further unit is where the diminishing return lives (see
        # ProjectsMixin.institution_unit_cost); this is simply how big the
        # place you paid for actually is.
        # STAFF_CAPACITY_SOURCES is the whole list, in one place, because the
        # planner needs to read it too. A plan built from the tech tree alone
        # cannot see any of this: nothing in the goal's prerequisite closure
        # mentions a school, so a purely structural plan can walk into
        # quantum_solidstate_theory's demand for eight trained scholars
        # against a society that tops out at 5.9 of them and sit there
        # until the horizon runs out, unless the planner can read the same
        # table this function reads rather than an if-chain only this
        # function could see.
        for key, _sc, _ar, _di, scaled, must_run in self._world.STAFF_CAPACITY_SOURCES:
            if not (self._world.running(key) if must_run else self._world.has(key)):
                continue
            units = self._world.institution_units(key) if scaled else 1.0
            scholars += _sc * units
            artisans += _ar * units
            directors += _di * units
        # LITERACY BOUNDS THE SCHOLAR CEILING. A school, an academy or an
        # imperial patron can only produce as many scholars as this society
        # has literate, propertied people to draw them from (literacy_factor
        # reads literacy_elite for "scholar"; see FINDINGS_ROUND2 section Q).
        # Below Rome's own literacy_elite (0.9, the number every one of the
        # figures above was already tuned against) this narrows the pool;
        # printing, schools and libraries raise literacy_elite
        # (apply_tech_effects, society.py) and widen it again as a run goes
        # on, which is the entire point of building them.
        scholars *= self.literacy_factor(trade_data.scholar_trade())
        # you cannot keep staff you cannot pay
        # a famous school attracts students and patrons it did not have to pay for
        # WAGES ARE A REAL CHARGE (see wage_bill), so this ceiling must be
        # more than "what you could pay for": it must leave room WITHOUT
        # eating the surplus needed to build anything, or hiring to the
        # edge of affordability could let payroll consume the entire
        # surplus, leaving nothing to spend on the work itself. A
        # programme whose payroll is its whole income is not a programme.
        #
        # SPARE MUST SUBTRACT living_cost() TOO, not just revenue() minus
        # upkeep() (the upkeep of BUILT WORKS alone): living_cost also
        # covers rent, appearances, tax and (via wage_bill) the staff
        # already carried. Subtracting living_cost here is what "what you
        # can pay for" has to mean if it is to mean anything: money already
        # going to rent and to people already employed is not there to
        # hire more people with.
        spare = max(0.0, (self._world.revenue() - self._world.upkeep() - self._world.living_cost())
                    * self._world.rep_factor()
                    + max(0.0, self._world.state.household.capital) * self.STAFF_CAPITAL_INCOME_RATE)
        budget = spare * self.STAFF_BUDGET_SHARE_OF_SPARE
        afford = budget / self.labour_market.in_current_money(self.staff_wage_reference())
        # EXTRA is supervision_room(), the headroom auto_hire adds on top of
        # this institutional ceiling (see step(), section 1). It must be
        # folded into the SAME denominator this ceiling is scaled against,
        # not added with no affordability check of its own: sc/ar are BOTH
        # ZERO before a workshop or a school is built, so an unconditional
        # extra would let the headroom hiring go through at full strength
        # regardless of income. Folding it in is what makes "grow the staff
        # toward what you can house and pay" true of the headroom hiring
        # and not just the institutional kind.
        extra = self.supervision_room()
        # NO FLOOR: a household with no surplus at all must be able to hire
        # nobody. A floor such as max(0.10, ...) would still hire a tenth
        # of the headroom regardless of affordability, undoing the whole
        # calculation above - "grow the staff toward what you can house and
        # pay" has to be able to mean nobody.
        scale = min(1.0, afford / max(1.0, scholars + artisans
                                      + extra * self.STAFF_EXTRA_HEADROOM_WEIGHT))
        self._world.household._staff_scale = scale     # step() applies this to `extra` too
        # A civilization of 1.5 million simply cannot field the trained people a
        # civilization of 65 million can, however rich you are. This is the single
        # biggest structural difference between playing Rome and playing Norway.
        # A 4.5 million person society CAN eventually staff a semiconductor
        # programme, it just has to grow into it: making that impossible
        # would be a modelling error, not a finding.
        pop = (self.STAFF_POP_SCALE_FLOOR
               + self.STAFF_POP_SCALE_VARIABLE * min(1.0, self._world.pop_scale ** self.STAFF_POP_SCALE_EXPONENT))
        return (base_sc + scholars * scale * pop, base_ar + artisans * scale * pop,
                directors * min(1.0, scale * self.DIRECTOR_SCALE_HEADROOM) * pop)

    _SUPERVISION_ROOM_WHY = (
        "Household headroom (people a founder may oversee, distinct from "
        "the institutional staff_capacity ceiling) this source is worth, "
        "used identically by supervision_room() and by "
        "supervision_room_from()'s own breakdown of it - one declared name "
        "per source rather than the same literal written twice, so the "
        "breakdown cannot drift from the total it explains. Tuned game "
        "balance, not measured from anything: a real figure would come "
        "from how many workers a person of a given period could actually "
        "keep an eye on.")
    SUPERVISION_ROOM_SELF = declare(
        "SUPERVISION_ROOM_SELF", 6.0, kind="temporary_heuristic",
        unit="people", source=None, confidence="D",
        why=_SUPERVISION_ROOM_WHY)
    SUPERVISION_ROOM_PER_DIRECTOR_EXTRA = declare(
        "SUPERVISION_ROOM_PER_DIRECTOR_EXTRA", 14.0, kind="temporary_heuristic",
        unit="people per trained deputy", source=None, confidence="D",
        why=_SUPERVISION_ROOM_WHY)

    def supervision_room(self):
        """People you can direct and pay BEYOND what your institutions train.

        staff_capacity is a ceiling on what a school, a workshop and a
        patron produce and support. It must not also be treated as a
        ceiling on how many men you can hire off the street, which is
        limited by money and by the market instead: conflating the two
        would put a hard wall across a run needing more craftsmen than an
        institutional ceiling alone supplies, one no amount of wealth
        could ever cross. This is that honest headroom. You hire them,
        you pay them every year, and you can only supervise so many.
        """
        household = self._world.state.household
        room = (self.SUPERVISION_ROOM_SELF
                + self.SUPERVISION_ROOM_PER_DIRECTOR_EXTRA * household.directors_extra
                + max(0.0, household.worker_housing_places or 0.0))
        room = self._world.effect_sum("supervision_room", room)
        # A SECOND TOWN, NOT A SECOND SCHOOLROOM. workshop_first, school_founded
        # and academy_network above are each a single PLACE a founder can stand
        # in; fin_chain_store is the tree's own word for the thing that is not
        # - "operates identical stores in multiple cities... requires
        # sophisticated management and accounting" - so it belongs in the same
        # unconditional headroom as the other three places, not only in the
        # income-gated institutional ceiling (STAFF_CAPACITY_SOURCES) a branch
        # network also feeds. Smaller than that ceiling's own 30-per-unit
        # figure, the same way school_founded's 10 here is smaller than its
        # own 12 there: most of what a branch is worth is still bounded by
        # whether the household can pay its clerks, not by whether a director
        # could in principle watch them.
        return room

    def supervision_room_from(self):
        """Where supervision_room's total actually comes from, as rows.

        ONE RULE, NOT TWO: this re-walks the same sources supervision_room
        itself does and its total is asserted equal to it, because a
        breakdown that can disagree with the figure it explains is worse than
        no breakdown. The reason it exists is that a starting grant was
        invisible: Rome begins with fin_societas and so oversees ten people
        in year one where every other civilisation oversees six, and nothing
        anywhere told a Roman player why, or told a Norse player what they
        were missing. A civilisation's starting technologies are the whole
        point of having five civilisations, and an advantage nobody can see
        is an advantage the player cannot reason about.
        """
        rows = [{"source": "yourself", "people": self.SUPERVISION_ROOM_SELF,
                 "what_it_is": "what one person can keep an eye on"}]
        household = self._world.state.household
        if household.directors_extra > 0.005:
            rows.append({"source": "your deputies", "people":
                         round(self.SUPERVISION_ROOM_PER_DIRECTOR_EXTRA * household.directors_extra, 2),
                         "what_it_is": "people you have trained to direct work"})
        for key, spec in self._world.effect_terms("supervision_room"):
            if self._world.effect_holds(key, spec):
                rows.append({"source": key,
                             "people": (round(self._world.effect_value(key, spec), 2) if "per_unit" in spec
                                        else self._world.effect_value(key, spec)),
                             "what_it_is": spec["words"]})
        return rows

    # THE SAME COEFFICIENTS market_supply() USES for identical formulas below
    # - one declared name per figure rather than the literal written twice,
    # so hired_cap()'s ceiling and market_supply()'s ceiling for the same
    # institution can never silently drift apart.
    HIRING_MULTIPLIER_EXPONENT = declare(
        "HIRING_MULTIPLIER_EXPONENT", 0.5, kind="temporary_heuristic",
        unit="dimensionless exponent on institution_units", source=None,
        confidence="D",
        why="SQRT rather than linear scaling of an institution's hiring-"
            "pool multiplier with how many units of it are founded - "
            "diminishing returns on what a place trains, matching "
            "institution_unit_cost's own diminishing-cost curve. Chosen "
            "because unbounded compounding of several such multipliers "
            "together multiplied hired_cap by roughly two orders of "
            "magnitude in a traced Rome run (see this function's own "
            "comment); the exponent itself is tuned to tame that, not "
            "measured.")
    SCHOOL_FOUNDED_HIRING_COEFFICIENT = declare(
        "SCHOOL_FOUNDED_HIRING_COEFFICIENT", 1.0, kind="temporary_heuristic",
        unit="dimensionless", source=None, confidence="D",
        why="How much a school widens the local hiring pool, at one unit: "
            "cap *= 1 + this * units**HIRING_MULTIPLIER_EXPONENT. Tuned "
            "game balance.")

    def hired_cap(self):
        # a civilization of 1.5 million cannot staff what one of 65 million can
        cap = (self._world.cfg["hired_hours_cap_base"] * self.local_market_share()
               * (self.POP_SCALE_FLOOR_SHARE
                  + self.POP_SCALE_VARIABLE_SHARE * min(1.0, self._world.pop_scale)))
        # 1.0 + (mult - 1.0) * sqrt(units): exactly the old `cap *= mult` at
        # units 1.0 (a run that never expands sees the identical multiplier),
        # and SQRT rather than linear beyond that - because these multipliers
        # already compound with one another (a school, an academy and a
        # freedman staff open together and their factors multiply), and at a
        # linear rate a household that grows several such institutions to
        # many units apiece on the back of literacy growth alone would see
        # hired_cap multiplied to an absurd degree from these terms alone.
        # Diminishing returns belong on what a place trains, same as they
        # already do on what it costs to found (institution_unit_cost) - a
        # second school teaches nearly as many more people as the first
        # did; a ninth does not teach nine times as many as one did.
        cap = self._world.effect_factor("hiring_factor", cap, self.HIRING_MULTIPLIER_EXPONENT)
        return cap

    # ---- how a SOCIETY reacts to a TECHNOLOGY -------------------------------
    STATE_WEIGHT_INFRASTRUCTURE = declare(
        "STATE_WEIGHT_INFRASTRUCTURE", 0.5, kind="temporary_heuristic",
        unit="dimensionless state-interest weight", source=None,
        confidence="D",
        why="How favourably the state views a technology tagged "
            "'infrastructure', on the scale state_interest() combines "
            "these weights with. Roughly ordered by plausible period "
            "attitude (infrastructure and food welcomed, a status- or "
            "weapon-democratising technology resisted) but the specific "
            "magnitudes are tuned game balance, not derived from any "
            "state's actual recorded policy.")
    STATE_WEIGHT_FOOD = declare(
        "STATE_WEIGHT_FOOD", 0.7, kind="temporary_heuristic",
        unit="dimensionless state-interest weight", source=None,
        confidence="D", why="See STATE_WEIGHT_INFRASTRUCTURE.")
    STATE_WEIGHT_MEDICAL = declare(
        "STATE_WEIGHT_MEDICAL", 0.5, kind="temporary_heuristic",
        unit="dimensionless state-interest weight", source=None,
        confidence="D", why="See STATE_WEIGHT_INFRASTRUCTURE.")
    STATE_WEIGHT_LUXURY = declare(
        "STATE_WEIGHT_LUXURY", 0.1, kind="temporary_heuristic",
        unit="dimensionless state-interest weight", source=None,
        confidence="D", why="See STATE_WEIGHT_INFRASTRUCTURE.")
    STATE_WEIGHT_SPECTACLE = declare(
        "STATE_WEIGHT_SPECTACLE", 0.1, kind="temporary_heuristic",
        unit="dimensionless state-interest weight", source=None,
        confidence="D", why="See STATE_WEIGHT_INFRASTRUCTURE.")
    STATE_WEIGHT_INEXPLICABLE = declare(
        "STATE_WEIGHT_INEXPLICABLE", 0.0, kind="temporary_heuristic",
        unit="dimensionless state-interest weight", source=None,
        confidence="D",
        why="A technology the state has no framework to react to earns "
            "neither favour nor suspicion by default. See "
            "STATE_WEIGHT_INFRASTRUCTURE for the rest of this table.")
    STATE_WEIGHT_STATUS_THREATENING = declare(
        "STATE_WEIGHT_STATUS_THREATENING", -0.6, kind="temporary_heuristic",
        unit="dimensionless state-interest weight", source=None,
        confidence="D", why="See STATE_WEIGHT_INFRASTRUCTURE.")
    STATE_WEIGHT_WEAPON_DEMOCRATISING = declare(
        "STATE_WEIGHT_WEAPON_DEMOCRATISING", -0.5, kind="temporary_heuristic",
        unit="dimensionless state-interest weight", source=None,
        confidence="D", why="See STATE_WEIGHT_INFRASTRUCTURE.")
    STATE_WEIGHTS = {"infrastructure": STATE_WEIGHT_INFRASTRUCTURE,
                     "food": STATE_WEIGHT_FOOD, "medical": STATE_WEIGHT_MEDICAL,
                     "luxury": STATE_WEIGHT_LUXURY, "spectacle": STATE_WEIGHT_SPECTACLE,
                     "inexplicable": STATE_WEIGHT_INEXPLICABLE,
                     "status_threatening": STATE_WEIGHT_STATUS_THREATENING,
                     "weapon_democratising": STATE_WEIGHT_WEAPON_DEMOCRATISING}

    def _staff_advice(self, kind, deficit=None):
        """Name the remedy, not just the shortfall - and only remedies you could
        actually have heard of.

        Advice that says "build workshop_first" while `why workshop_first`
        replies "you have never heard of that" from the same program in the
        same second is a contradiction, not help. Hiring is always
        sayable, because the labour market is in front of you; a named
        institution is not, until it is.

        `deficit` is how many more people the caller is short; the hire
        advice is sized to it.
        """
        bits = []
        for node, why in self._world.STAFF_SOURCES.get(kind, []):
            if node == "HIRE" and deficit:
                bits.append(self._world.staff_hire_advice(kind, math.ceil(deficit - 1e-9)))
            elif node in ("BUY", "HIRE"):
                bits.append(why)
            # CLOSED IS NOT MISSING. market_supply() only applies a source's
            # multiplier via running(node), so a school built and then shut
            # for want of a supervisor stops widening the hiring pool exactly
            # as if it had never been built - and this advice, filtering on
            # `node not in self.household.done`, fell silent about it rather than
            # naming the actual remedy. Reopening costs a supervisor, not a
            # second institution; say that first.
            elif node in self._world.state.projects.done and node not in self._world.state.projects.operating and self._world.is_venture(node):
                bits.append("reopen %s ('open %s') - you already built this; "
                            "it is only shut" % (node, node))
            elif node not in self._world.state.projects.done and self._world.is_visible(node):
                # NOT A CIRCLE. `why workshop_first` says it is blocked for want
                # of artisans, and the advice on how to get artisans said "build
                # workshop_first (you need somewhere for them to work)" - a play
                # tester quoted the two lines against each other. If the remedy
                # is itself waiting on the very thing it is meant to supply,
                # naming it is worse than saying nothing: say what it is waiting
                # on instead, so the reader knows which end to start at.
                # Asked DIRECTLY of the node's own requirement, never through
                # start_reason - which calls this function, so the obvious
                # version of this test recurses until the stack gives out.
                _node = self._world.nodes[node]
                _short = (_node["art"] > self._world.state.household.artisans + 1e-9 if kind == "artisans"
                          else _node["sch"] > self.effective_scholars() + 1e-9)
                if _short:
                    bits.append("build %s eventually (%s) - but it is itself "
                                "waiting on %s, so hire or commission first"
                                % (node, why, kind))
                else:
                    bits.append("build %s (%s)" % (node, why))
        if not bits:
            return "wait: your existing institutions add %s each year." % kind
        return "To get more %s: %s." % (kind, "; ".join(bits[:3]))

    def headcount(self):
        household = self._world.state.household
        return sum(household.employees.values()) + household.slaves + household.freedmen

    def director_hours_committed(self):
        """Hours of your own year already spoken for before any project sees them.

        WAGE HOURS BELONG HERE: keeping a separate tally for `work` would let
        a founder sell an entire year of hours for wages and then still
        spend a full year's worth of hours on projects in the same year -
        a free second year inside every year. There is one year, and one
        pair of hands.
        """
        return (getattr(self._world.household, "teaching_hours_this_year", 0.0)
                + (getattr(self._world.household, "relocation_hours_this_year", 0.0) or 0.0)
                + self._world.household.wage_hours_this_year)

    def household_room(self):
        """How many more people this household can feed, house and oversee.

        One number, used by `hire` and by `buy` alike: using different
        ones - or, worse, none at all for one of the two - would let a
        player be told one capacity through one verb and exceed it
        through the other.
        """
        return (self.staff_capacity()[1] + self.supervision_room()
                - self.headcount())