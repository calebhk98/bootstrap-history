"""Revenue, the founder's job, workshops and the institutions that run them.

Every method here answers "what does the household actually take in this
year, and what does it cost to keep that running", as opposed to
economy_goods.py's question of what a unit of output sells for once
made. Covers: state_funding() (an imperial patron's direct funding) and
venture_ramp() (how a concern's takings ramp up after it opens);
revenue_capacity(), revenue() and
revenue_sources() (what a household earns, itemised);
workshop_output()/capability_factor() (what a staffed workshop makes,
and how accumulated method multiplies it); still_ramping(), held_trade(),
founder_wage_income() and the held-skill/candidate-set caches
(_practisable/_practice_set/_revenue_upkeep_candidates) revenue() and
upkeep() both share; and upkeep()/institution_upkeep()/
institution_places() (what it costs to keep a concern or institution
open this year).

ProductionMixin is composed into EconomyMixin (economy.py) alongside the
other economy sub-mixins; see that file for the composition and for the
grouping evidence, and for why this lives in a separate file.
"""
from .concern_earnings import ledger_row, output_market_factor, takings_at
from .data import trade_family
from sim.constants import declare
from . import category_traits, money_units, node_revenue_market, node_upkeep
from .readable import readable
from .revenue_ledger import assemble_ledger
from sim.world import plant_figures
from .industry_depth import RAMP_SHARE_AT_FULL_DEPTH


class ProductionMixin:

    STATE_FUNDING_BASE_LABOUR_HOURS = declare(
        "STATE_FUNDING_BASE_LABOUR_HOURS", 50400.0, kind="temporary_heuristic",
        unit="labour hours/year at output_per_head=1, state_capacity=1, pop_scale=1",
        source=None, confidence="D",
        why="Amount of labour, not of coin: it was a book-denarii figure and now follows what labour costs. "
            "What an imperial patron is worth in direct funding at a "
            "reference civilisation size and state capacity. No fiscal "
            "record backs this figure; a real answer needs a state budget "
            "model - tax revenue, the fiscus's own spending priorities - "
            "that this engine does not have, per CLAUDE.md 3.1's ban on "
            "asserting a state revenue outright.")
    STATE_FUNDING_BASE = money_units.PricedInLabourHours("STATE_FUNDING_BASE_LABOUR_HOURS")
    STATE_FUNDING_POP_SCALE_EXPONENT = declare(
        "STATE_FUNDING_POP_SCALE_EXPONENT", 0.4, kind="temporary_heuristic",
        unit="dimensionless exponent on pop_scale", source=None,
        confidence="D",
        why="How much faster a larger population's state can fund you, on "
            "a sub-linear curve so state funding does not simply track "
            "population one-for-one. Shape is plausible (bigger states have "
            "more surplus but not proportionally more to spare on one "
            "founder); the exponent itself is tuned, not fitted to any "
            "fiscal data.")
    STATE_FUNDING_GOV_QUALITY_SCALE = declare(
        "STATE_FUNDING_GOV_QUALITY_SCALE", 25.0, kind="temporary_heuristic",
        unit="household.gov points per +100% funding", source=None,
        confidence="D",
        why="How much a better-governed household multiplies its own state "
            "funding. household.gov has no independent calibration of its "
            "own scale, so this denominator is picked to make the term feel "
            "proportionate rather than derived from anything.")

    def patron_funding_ask(self):
        """What a patron state would give the founder in a year if its treasury could spare it."""
        if not self.running_with_mechanic("state_funding"):
            return 0.0
        return (self.STATE_FUNDING_BASE * self.real_output_per_head() * self.state_capacity
                * self.pop_scale ** self.STATE_FUNDING_POP_SCALE_EXPONENT
                * (1.0 + max(0.0, self.state.governance.gov) / self.STATE_FUNDING_GOV_QUALITY_SCALE)
                * self.rep_factor())

    def state_funding(self):
        """What the treasury has paid the founder this year; the government decides it
        (Government.pay_patron) from its purse after its standing need."""
        state = self.state.actors
        record = None if state is None else state.records.get("government:" + str(self.civ.get("id")))
        return 0.0 if record is None else record.patron_grant

    def venture_ramp(self, node_id):
        """How much of its full takings a concern is making, 0..1.

        FROM THE YEAR YOU OPENED IT, not the year you worked out how: a
        concern built in one year and opened years later must still ramp
        up from its opening, not appear at full takings the instant its
        doors open, or delaying `open` would be strictly better than
        opening promptly. Custom takes time to find whoever owns the shop.
        """
        projects = self.state.projects
        scenario = self.state.scenario
        started = projects.business.opened_year_of(node_id, None)
        if started is None:
            started = projects.done_year.get(node_id, scenario.year)
        age = scenario.year - started
        # An established industry (anyone's worker-years running it) finds its custom sooner.
        return plant_figures.ramp(age, self.cfg["revenue_ramp_years"], self.industry_depth(node_id),
                                  RAMP_SHARE_AT_FULL_DEPTH)

    def revenue_capacity(self):
        """What you would earn in an ordinary year, with your own hands on your
        own work, none of this year's hours sold on request. Used where a swing in ONE year should not count - a lender
        does not cut your line because you took a job this year."""
        household = self.state.household
        _sold = household.wage_hours_this_year
        household.wage_hours_this_year = 0.0
        try:
            return self.revenue()
        finally:
            household.wage_hours_this_year = _sold

    @readable
    def revenue(self):
        """Total annual revenue across all active concerns, workshops, and state funding.

        Cached value: self.revenue()
        Dependencies:
          - self.year: changes annually in sim.step()
          - self.pop_scale: changes annually in sim.step()
          - economy.output_per_head: measured when the year's market closes
          - self.household._operating_ver: changes whenever self.household.operating is mutated
          - self.household._done_ver: changes whenever self.household.done or granted is mutated
          - self.household._workforce_ver: changes whenever self.household.employees is mutated
          - self.household.freedmen, self.household.slaves: workforce headcount
          - self.household.wage_hours_this_year: hours sold on request (e.g. temporary 0.0 in revenue_capacity)
          - director_hours_committed(): teaching, moving and supervising hours the standing job does not sell
          - labour.wage_signature(): recent hiring that moves the market wage the standing job is paid
          - self.household.directors_extra, bondage_years_left: the own hours the standing job sells
          - self.household.farm_hectares: household farmland staples affecting food price ratio
          - self.household.gov: governance quality affecting state funding
          - self.household._inst_units_ver: scalable institution units
          - self.output_factor: hazard/war output scaling
          - self.reputation: standing affecting state funding
          - self.founder_alive: a dead founder sells no hours
        Invalidated by: Any change to any element in the composite version key tuple.
        Nested mutation concerns: household.employees wrapped in _InvalidatingDict (flat dict); workforce counts tracked in key.
        Serialized: no
        """
        scenario = self.state.scenario
        economy = self.state.economy
        holdings = self.state.holdings
        projects = self.state.projects
        household = self.state.household
        governance = self.state.governance
        founder = self.state.founder
        key = (
            scenario.year,
            self.pop_scale,
            economy.output_per_head,
            self.household.operating_version,
            self.household.done_version,
            self.household.workforce_version,
            self.household.institution_units_version,
            household.wage_hours_this_year,
            self.labour.director_hours_committed(),
            self.labour.wage_signature(),
            household.directors_extra,
            household.bondage_years_left,
            getattr(holdings, "farm_hectares", 0.0) or 0.0,
            getattr(household, "freedmen", 0.0) or 0.0,
            getattr(household, "slaves", 0.0) or 0.0,
            getattr(governance, "gov", 0.0) or 0.0,
            economy.output_factor,
            household.reputation,
            founder.founder_alive,
            self.state_funding(),
            self.home_price_level(),
        )
        if getattr(self.household, "_revenue_cache_key", None) == key:
            return self.household._revenue_cache_val

        value = self._compute_revenue_uncached()
        self.household._revenue_cache_key = key
        self.household._revenue_cache_val = value
        return value

    def concern_revenue(self, node_id):
        """What one open concern earns in a year before the output factor: the figure the screens quote."""
        return self.venture_real_earnings(node_id, with_output_factor=False)

    def _compute_revenue_uncached(self):
        total_revenue = 0.0
        practice_set = self._practice_set()
        projects = self.state.projects
        granted = projects.granted
        operating = projects.operating
        # SCAN ONLY WHAT COULD POSSIBLY PAY. Every node this loop's own body
        # goes on to skip - not operating and not practised - was already
        # true of the whole rest of `done`, which only grows; see
        # _revenue_upkeep_candidates' own docstring for why this is safe.
        for node_id in self._revenue_upkeep_candidates():
            practice = node_id in practice_set
            if node_id in granted and not practice:
                continue          # the society's, not yours
            # KNOWING HOW IS NOT THE SAME AS RUNNING IT. A node pays when it is
            # open, and not for having been worked out. See is_venture and
            # open_venture in projects.py for why: the tree already described
            # these as concerns with a yearly running cost, and the only thing
            # missing was the decision to open the doors.
            if not practice and node_id not in operating:
                continue
            node = self.nodes[node_id]
            # a held skill earns through the founder's own hours (founder_wage_income), not through the node
            if node["rev"] and not practice:
                total_revenue += self.concern_revenue(node_id)
        # THERE IS ONLY SO MUCH MARKET. Uncapped, this compounds: every venture
        # pays back quickly, so its income buys the next one, and nothing
        # stops a run's capital from growing far past what a real market this
        # size could absorb - it cannot sell more inns than the town wants.
        # A saturating curve caps that without ever making a venture worthless.
        # WHAT YOUR OWN WORKSHOP SELLS: a payroll without credited output is
        # pure cost. Thirty craftsmen in a workshop do not sit there costing
        # money. They make things, and the things are sold.
        #
        # It is deliberately less than a 2x markup on wages and it needs somewhere
        # to work: a staff with no workshop is an expense, which is exactly why
        # workshop_first matters and why it is cheap.
        total_revenue += self.workshop_output()
        total_revenue += self.founder_wage_income()
        economy = self.state.economy
        gross = total_revenue
        ceiling = self.REVENUE_CEILING_PER_POP_SCALE * self.pop_scale \
            * self.real_output_per_head() * self.price_index
        gross = gross / (1.0 + gross / max(1.0, ceiling))
        return (gross + self.state_funding()) * economy.output_factor

    REVENUE_CEILING_LABOUR_HOURS_PER_POP_SCALE = declare(
        "REVENUE_CEILING_LABOUR_HOURS_PER_POP_SCALE", 18100000.0, kind="temporary_heuristic",
        unit="labour hours/year at pop_scale=1, output_per_head=1", source=None,
        confidence="D",
        why="Amount of labour, not of coin: it was a book-denarii figure and now follows what labour costs. "
            "The saturating ceiling on how much revenue a single founder's "
            "ventures can pull out of one civilisation's whole market - "
            "invented specifically to stop a run compounding into billions "
            "against an empire whose own annual product is not separately "
            "modelled (see this method's own comment on the tester who held "
            "three billion denarii). A real ceiling needs an actual GDP "
            "figure for the civilisation to compare against, which this "
            "engine does not compute.")
    REVENUE_CEILING_PER_POP_SCALE = money_units.PricedInLabourHours("REVENUE_CEILING_LABOUR_HOURS_PER_POP_SCALE")

    SLAVE_LABOUR_PRODUCTIVITY_SHARE = declare(
        "SLAVE_LABOUR_PRODUCTIVITY_SHARE", 0.7, kind="temporary_heuristic",
        unit="fraction of a free worker's output credited per enslaved worker",
        source=None, confidence="D",
        why="How much of a free craft worker's output one enslaved worker "
            "in the household is credited with producing, reused for both "
            "headcount and wage-bill purposes. A real figure needs actual "
            "evidence on relative productivity under coercion versus free "
            "labour for the specific tasks involved, which varied hugely "
            "by trade and is not modelled here; 0.7 is a plausible-feeling "
            "discount, not a measurement.")
    WORKSHOP_WAGE_MARKUP_BASE = declare(
        "WORKSHOP_WAGE_MARKUP_BASE", 1.55, kind="temporary_heuristic",
        unit="output denarii per denarius of craft wages", source=None,
        confidence="D",
        why="How much a workshop's output is worth relative to what it "
            "pays its craft staff - deliberately more than a bare 1x wage "
            "pass-through (a workshop has to sell its output for more than "
            "labour cost alone or it could never cover materials, rent or "
            "profit) and, per the comment above, deliberately less than a "
            "2x markup. Chosen to make the mechanism function at all, not "
            "measured against any real workshop's margins.")

    def workshop_output(self):
        """What your standing staff produces and sells, over and above projects."""
        if not self.running_with_mechanic("workshop_site"):
            return 0.0
        household = self.state.household
        craft = sum(count for trade, count in household.employees.items() if trade_family(trade) == "craft")
        craft += household.freedmen + household.slaves * self.SLAVE_LABOUR_PRODUCTIVITY_SHARE
        market = self.labour.market
        wage = 0.0
        for trade, count in household.employees.items():
            if trade_family(trade) == "craft":
                wage += count * market.quote_annual(trade)
        wage += ((household.freedmen + household.slaves * self.SLAVE_LABOUR_PRODUCTIVITY_SHARE)
                 * market.quote_annual("artisan"))
        mark = self.WORKSHOP_WAGE_MARKUP_BASE
        mark = self.effect_sum("workshop_markup", mark)
        # AND EVERYTHING YOU KNOW HOW TO DO, which is where the value of a
        # capability actually shows up.
        #
        # Making revenue follow what you RUN was right, and it left a hole:
        # 1,337 nodes carried revenue and most of them are not businesses at
        # all. A better furnace, a tighter tolerance, a purer reagent - nobody
        # opens those as a going concern, so under the new rule they paid
        # nothing whatever, and the economy came out far poorer than every
        # number in this file was calibrated against. A Rome run ended at year
        # 800 with 270 technologies, one open concern and no craftsmen at all.
        #
        # The honest place for that value is here. Knowing how to do a thing
        # earns you nothing on its own - which was the whole point - but it
        # makes the workshop you actually staff and pay for more productive,
        # which is how method has always paid. It needs a workshop and it needs
        # people; with neither, it is still worth nothing.
        return wage * mark * self.capability_factor()

    def capability_factor(self):
        """How much better your methods make the same pair of hands.

        Tier-weighted, over what you have built and are NOT separately running
        as a concern - a concern already pays you directly and must not be
        counted twice. Saturating, because the tenth improvement to a workshop
        is worth less than the first, and because an unbounded product of 1,300
        technologies is how you get a run holding more method than the empire.

        CACHED. A 300-year profile called this ~17,000 times, every one of
        them walking the full done list - self.household.done/self.household.operating change far
        less often than that (done_in_order() itself was fixed the same way,
        earlier, for the same reason). The cache holds the FINISHED RESULT of
        exactly this walk, recomputed from scratch - same order, same
        arithmetic, nothing added or removed piecemeal - whenever it is
        invalidated, so it is bit-identical to calling this uncached every
        time: see _done_changed() and _operating_changed(), the only two
        places that clear it. An incremental version that added and
        subtracted a node's weight as it entered or left self.household.done/
        self.household.operating was considered and rejected: float addition is not
        associative, and the order nodes enter or leave at runtime is not the
        order done_in_order() walks them in, so an incremental running total
        would drift from a full recompute in its last bits over a long run -
        a real behaviour change, not just a speed one. Recomputing the whole
        thing on invalidation has none of that risk and still turns ~17,000
        calls into however many times done/operating actually change in a
        run (a few hundred), not however many times this is asked.
        """
        cached = getattr(self.household, "_cap_factor", None)
        if cached is not None:
            return cached
        weight = 0.0
        projects = self.state.projects
        for node_id in self.done_in_order():
            if node_id in projects.granted or node_id in projects.operating:
                continue
            node = self.nodes[node_id]
            if node["rev"] <= 0:
                continue
            weight += node["rev_hours"]     # in hours, so the price level of money does not enter it
        result = 1.0 + self.CAPABILITY_FACTOR_CEILING_BONUS * (
            weight / (weight + self.CAPABILITY_FACTOR_HALF_SATURATION_REV_LABOUR_HOURS))
        self.household._cap_factor = result
        return result

    CAPABILITY_FACTOR_CEILING_BONUS = declare(
        "CAPABILITY_FACTOR_CEILING_BONUS", 2.0, kind="temporary_heuristic",
        unit="dimensionless multiple on workshop output (asymptote)",
        source=None, confidence="D",
        why="The most that accumulated, unused method can ever multiply a "
            "workshop's output by, as the weighted total saturates. A "
            "tripling-or-more from pure technique with no new workshop or "
            "worker would be implausible; 2x (a doubling) is a tuned "
            "ceiling, not derived from any output-per-technology "
            "measurement.")
    CAPABILITY_FACTOR_HALF_SATURATION_REV_LABOUR_HOURS = declare(
        "CAPABILITY_FACTOR_HALF_SATURATION_REV_LABOUR_HOURS", 806000.0,
        kind="temporary_heuristic", unit="labour hours of tier-weighted revenue at half of CAPABILITY_FACTOR_CEILING_BONUS", source=None,
        confidence="D",
        why="Amount of labour, not of coin: it was a book-denarii figure and now follows what labour costs. "
            "How much accumulated tier-weighted method it takes to reach "
            "half the maximum capability bonus - the saturating curve's "
            "own scale. Tuned against playtests (see the comment this "
            "replaces: '40,000 of tier-weighted method roughly doubles "
            "what a workshop makes'), not fitted to any measured "
            "productivity data.")
    CAPABILITY_FACTOR_HALF_SATURATION_REV = money_units.PricedInLabourHours("CAPABILITY_FACTOR_HALF_SATURATION_REV_LABOUR_HOURS")

    def concern_goods_have_market(self, node_id):
        """Whether the economy prices what the concern sells; a good nobody has sold yet has none, and its
        quote then values sales and purchases alike at long-run cost rather than mixing the two bases."""
        baskets = self.concern_baskets_now(node_id)
        paid = self.economy.agent_prices_at()
        if baskets is None or paid is None:
            return True
        return all(self._priced_key(material, paid) is not None for material in baskets.outputs)

    def node_output_market_factor(self, node):
        """This year's market over long-run prices for what an output-derived node sells and buys; one otherwise."""
        baskets = self.concern_baskets_now(node["id"])
        return output_market_factor(
            baskets is not None and self.concern_goods_have_market(node["id"]),
            lambda: node_revenue_market.basket_market_factor(
                baskets.outputs, baskets.purchases, self._material_prices(), self.goods_market.home_unit_price))

    def concern_takings(self, node_id, ramp, with_output_factor=True):
        """Yearly takings of one concern at a given ramp, before market saturation: its loaded figure
        carried to the techniques held now (concern_volume.py); callers apply the market's price.
        `with_output_factor` False leaves out the hazard and war factor `revenue` applies to its total."""
        economy = self.state.economy
        return takings_at(self.nodes[node_id]["rev"], ramp, economy.output_factor if with_output_factor else 1.0,
                          self.price_index, self.concern_value_ratio(node_id), self.concern_learning_ratio(node_id))

    def ledger_concern_rows(self):
        """Yearly takings of every opened concern that earns, by node id, as the ledger credits them. The
        founder's own practice is one row of `revenue_sources`, not one per skill."""
        rows = {}
        projects = self.state.projects
        for node_id in self.done_in_order():
            if node_id in projects.granted or node_id not in projects.operating:
                continue
            if not self.nodes[node_id]["rev"]:
                continue
            # The figure `ventures` and `why` print, and the factor revenue() applies, so the ledger's
            # parts add up to its total.
            row = ledger_row(self.venture_real_earnings(node_id))
            if row is not None:
                rows[node_id] = row
        return rows

    def held_trade(self):
        """The trade the founder sells hours in: scholar when a skill the founder holds asks for
        scholars, else artisan; None when the founder holds no skill."""
        held = self._practice_set()
        if not held:
            return None
        return "scholar" if any(self.nodes[node_id]["sch"] > 0 for node_id in held) else "artisan"

    def founder_wage_income(self):
        """Yearly pay of the founder's standing job: the hours not spoken for, sold in the held trade at
        that trade's market wage (labour_job.py). One person's hours sell once however many skills the
        founder holds, and a dead founder sells none."""
        return self.labour.standing_job_pay(self.held_trade())

    @readable
    def revenue_sources(self):
        """Where the money actually comes from, itemised.

        A player who never issues a single start can still get richer
        every year, from the wages of their own work - the founder is
        employed in a trade they hold - which is otherwise invisible
        anywhere else in the interface.
        """
        economy = self.state.economy
        funding = self.state_funding()
        return assemble_ledger(
            self.ledger_concern_rows(), self.workshop_output() * economy.output_factor,
            self.founder_wage_income() * economy.output_factor,
            funding * economy.output_factor if funding > 0.5 else None, self.revenue())

    # A granted node whose category is flagged practisable is a skill the founder holds and works with their own
    # hands; the held skills choose the trade the founder's hours are sold in (held_trade). A granted fleet of
    # merchant ships is owned by other people, so shipping is not one.
    def _practisable(self, node_id):
        """Is this granted node a skill the founder holds and works with their own hands?"""
        return category_traits.has_trait(self.nodes[node_id].get("cat"), "practisable")

    def still_ramping(self):
        """Earners that are not yet paying their full figure, and how far along.

        Every earner ramps over revenue_ramp_years, so on the day you open
        one it pays only a fraction of what the tree quotes for it. Nothing
        else explains that gap between the quoted figure and the ledger, so
        this surfaces it directly. Kept OUT of revenue_sources, whose every
        value is a number that has to sum to the revenue above it.
        """
        young = []
        projects = self.state.projects
        for node_id in sorted(projects.operating):
            node = self.nodes.get(node_id)
            if not node or not node["rev"] or node_id in projects.granted:
                continue
            ramp = self.venture_ramp(node_id)
            if ramp < 0.999:
                young.append((node_id, ramp))
        if not young:
            return None
        young.sort(key=lambda entry: entry[1])
        return ("%s%s at %d%% of full takings. A concern you open reaches its "
                "full figure over %g years, so what the ledger shows is not "
                "what it will be."
                % (", ".join(node_id for node_id, _ramp in young[:6]),
                   " and %d more" % (len(young) - 6) if len(young) > 6 else "",
                   young[0][1] * 100, self.cfg["revenue_ramp_years"]))

    def _practice_set(self):
        """The granted skills you actually practise, as a set, computed once.

        revenue() called _practisable once per done node per call, and
        start_reason calls revenue() - so a 45-year fogged Mexica run made
        SIXTY-ONE MILLION of those calls and spent 38 seconds inside revenue().
        The answer never changes unless the granted set does, which happens at
        setup and never again.
        """
        projects = self.state.projects
        cache = getattr(self.household, "_practice_cache", None)
        if cache is None or cache[0] != len(projects.granted):
            cache = (len(projects.granted),
                     frozenset(node_id for node_id in projects.granted if self._practisable(node_id)))
            self.household._practice_cache = cache
        return cache[1]

    def _revenue_upkeep_candidates(self):
        """Every node in `done` that revenue() or upkeep() could possibly
        charge or pay for - i.e. that is operating, or in your practice
        set - in done_in_order()'s own tree order. Neither function can do
        anything with a node that is neither: scanning the WHOLE of `done`
        (every technology ever finished, which is most of the tree by the
        late game) to throw almost all of it away again on that same test
        is wasted work whenever `operating` and the practice set together
        are a handful of concerns against a `done` list that only grows.
        This is the small subset that survives the test, computed once and
        handed to both.

        This closes the same O(active) vs O(done) gap done_in_order()
        itself was already added to close for a DIFFERENT quadratic blowup
        (see its own docstring): the candidate list is short, but scanning
        the whole of `done` to build it on every call is not.

        CACHED, on the same three signals _goods_category_state's own cache
        (above) already trusts for this reason:
          - the identity of done_in_order()'s own cached list - a NEW list
            object exactly when `done` changes, because _done_changed()
            (below) sets `_done_seq` to None and done_in_order() rebuilds it
            from scratch. A length check is not safe here for the same
            reason done_in_order's docstring already gives: a year that
            finishes one thing and abandons another leaves the length
            unchanged and the contents different.
          - `operating`'s version counter, `_operating_ver`, bumped once per
            mutation by _operating_changed() - see that method's own
            docstring for the exhaustive case-by-case proof, which applies
            unchanged here since this reads exactly the same `operating`.
          - the identity of _practice_set()'s own cached frozenset, which
            THAT method already rebuilds (a new object, new identity) the
            moment len(self.household.granted) changes - see its own docstring. Since
            self.household.granted is only ever grown (grep the engine: every mutation
            site is `.add`, never `.discard`/`.remove`/`&=`/`-=`), a length
            check is sound there in a way it would not be for `done`, and
            this cache inherits that same soundness by keying on the
            resulting object's identity rather than re-deriving it.
        Three signals already relied on elsewhere in this file, not a new
        one - and this cache's OWN staleness, if any one of them were wrong,
        would show up as a wrong revenue or upkeep total, which
        sim/tests/fingerprint.py's byte-for-byte, per-year state hash across nine
        reference runs (five civilisations, several seeds, fog on and off,
        events on and off) is built to catch.
        """
        seq = self.done_in_order()
        practice_set = self._practice_set()
        # STRONG REFERENCES AND `is`, NOT BARE id() INTEGERS, for the reason
        # _cached_demand_by_tag() below spells out at length: a freed
        # object's address is handed straight to the next same-sized
        # allocation, so two different objects compare equal by id() often
        # enough to matter, and the cache replays a stale answer under a fresh
        # one. That is what made this simulation non-deterministic, in the
        # sibling cache rather than this one.
        #
        # This is not a fix for an observed bug in THIS cache: probing it
        # for stale answers is unreliable, because the probe's own
        # allocations are exactly what decide whether an address gets
        # recycled, so a clean probe result proves nothing. It is the
        # removal of a hazard that cannot be cheaply observed, by the same
        # defence sim/ui/proto/nodes.py uses for the identical reason.
        # Holding seq and practice_set alive for as long as the entry may be
        # compared against them makes the collision structurally impossible
        # rather than merely unmeasured.
        projects = self.state.projects
        operating_version = self.household.operating_version
        cached = getattr(self.household, "_rev_up_candidates_cache", None)
        if (cached is not None and cached[0] is seq
                and cached[1] is practice_set and cached[2] == operating_version):
            return cached[3]
        operating = projects.operating
        cands = [node_id for node_id in seq if node_id in operating or node_id in practice_set]
        self.household._rev_up_candidates_cache = (seq, practice_set, operating_version, cands)
        return cands

    @readable
    def upkeep(self):
        # Symmetrically, you do not pay to maintain what you do not own, but you
        # do bear the small standing cost of the practice you actually run - and
        # you do not pay the running costs of a concern you have not opened.
        # Both halves of that follow `operating`, so closing something really
        # does stop the bleeding, and knowing how to do something costs nothing
        # to know.
        return sum(self.upkeep_by_concern().values())

    @readable
    def upkeep_by_concern(self):
        """{node id: yearly running cost} for each concern or practice that is paid for;
        `upkeep` is its sum."""
        practice_set = self._practice_set()
        operating = self.state.projects.operating
        return {node_id: self.venture_real_upkeep(node_id)
                for node_id in self._revenue_upkeep_candidates()
                if node_id in operating or node_id in practice_set}

    INSTITUTION_FLOOR = declare(
        "INSTITUTION_FLOOR", 0.20, kind="temporary_heuristic",
        unit="fraction of full upkeep charged with zero enrolment",
        source=None, confidence="D",
        why="What a school costs on the day you found it, as a share of "
            "what it costs once it is full: the building, the lease, and "
            "one teacher, before any scholars arrive. A real figure needs "
            "an itemised fixed-versus-variable cost breakdown for each "
            "capability institution (building/lease/core staff versus "
            "per-head cost), which this file does not have; 20% is a "
            "round, plausible fixed share, not derived from one.")

    def institution_upkeep(self, node_id, units=None, fully_staffed=False):
        """What this concern actually costs to keep open THIS year.

        `units` prices a stated size of a scalable institution instead of what is open;
        `fully_staffed` skips the occupancy scaling (every place filled).

        For almost everything, its upkeep. For an establishment whose purpose is
        to support PEOPLE - a school, an academy, a workshop, a licensed
        collegium, a freedman staff - it scales with how much of that support you
        are using, because a school with three scholars in it does not cost what
        a school with forty does. Endowed schools historically scaled with
        enrolment and so should this.

        Capability follows running(), so nothing is credited for a school
        or an imperial patron's line of credit that was never actually
        opened and paid for. That makes it essential this does not price
        every institution as though the place were full on the day you
        founded it: a flat full-upkeep charge on day one would kill the
        first rung of the ladder.
        """
        node = self.nodes[node_id]
        # A THIRD SCHOOL COSTS THREE SCHOOLS' UPKEEP, at three schools' worth
        # of places to fill it against - both sides of this scale together so
        # a run that never founds more than the original single unit sees
        # exactly the arithmetic it always did. See
        # ProjectsMixin.institution_units.
        #
        # NOT YET OPEN MEANS "WHAT WOULD A FIRST FOUNDING COST", not zero:
        # auto_open_ventures (projects.py) calls this on things it has not
        # opened yet to decide whether to. institution_units answers 0 for
        # anything not currently operating, so multiplying by that here
        # would turn every unopened institution's prospective upkeep into
        # zero - free, in effect - and let the affordability gate through
        # on nothing. _units must fall back to 1.0 for anything not yet
        # operating.
        _units = (self.institution_units(node_id) if node_id in self.state.projects.operating else 1.0) \
            if node_id in self.SCALABLE_INSTITUTIONS else 1.0
        if units is not None and node_id in self.SCALABLE_INSTITUTIONS:
            _units = float(units)
        # The crew's pay is in the payroll (`living_cost` through `wage_bill`), so only the non-crew part is charged here.
        upkeep_amount = node["up"] * node_upkeep.non_labour_share(node) * _units
        if (fully_staffed or node_id not in self.CAPABILITY_INSTITUTIONS or upkeep_amount <= 0
                or self.mechanic(node_id, "upkeep_full")):
            return upkeep_amount
        places = self.institution_places(node_id) * _units
        if places <= 0:
            return upkeep_amount
        used = min(1.0, self.labour.headcount() / max(1.0, places))
        return upkeep_amount * (self.INSTITUTION_FLOOR
                     + (1.0 - self.INSTITUTION_FLOOR) * used)

    # Read off STAFF_CAPACITY_SOURCES (labour.py) the same way
    # every other row here is: a unit's ar+di, so a chain store
    # with three people in it is not billed as though every
    # branch were already fully staffed.
    # People one unit supports: each institution's `institution_places` mechanic.
    INSTITUTION_PLACES_FALLBACK_UPKEEP_LABOUR_HOURS_PER_HEAD = declare(
        "INSTITUTION_PLACES_FALLBACK_UPKEEP_LABOUR_HOURS_PER_HEAD", 250.0,
        kind="temporary_heuristic", unit="labour hours of upkeep per head",
        source=None, confidence="D",
        why="For an institution not in INSTITUTION_PLACES, how many "
            "denarii of upkeep one person's worth of capacity is assumed "
            "to cost, so an arbitrary institution still scales with "
            "headcount instead of defaulting to zero places. 'About a "
            "wage a head' per the comment this replaces - the right ORDER "
            "of magnitude for a building whose cost is its people, not a "
            "specific attested wage.")
    INSTITUTION_PLACES_FALLBACK_UPKEEP_PER_HEAD = money_units.PricedInLabourHours("INSTITUTION_PLACES_FALLBACK_UPKEEP_LABOUR_HOURS_PER_HEAD")

    def institution_places(self, node_id):
        """Roughly how many people ONE UNIT of this establishment is built to
        support - see institution_upkeep, which multiplies this by
        institution_units(node_id) itself, so callers wanting the total should read
        that, not this, for anything in SCALABLE_INSTITUTIONS.

        Read off the same table staff_capacity() and supervision_room() use, so
        that the cost of a place and the existence of a place cannot drift
        apart. Anything absent is sized by its own upkeep at about a wage a
        head, the right order for a building whose cost is its people.
        """
        places = self.mechanic(node_id, "institution_places")
        if places is not None:
            return places["flat"]
        return max(1.0, self.nodes[node_id]["up"] / self.INSTITUTION_PLACES_FALLBACK_UPKEEP_PER_HEAD)
