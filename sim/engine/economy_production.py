"""Revenue, practices, workshops and the institutions that run them.

Every method here answers "what does the household actually take in this
year, and what does it cost to keep that running", as opposed to
economy_goods.py's question of what a unit of output sells for once
made. Covers: state_funding() (an imperial patron's direct funding) and
venture_ramp() (how a concern's takings ramp up after it opens);
practice_attention(), revenue_capacity(), revenue() and
revenue_sources() (what a household earns, itemised);
workshop_output()/capability_factor() (what a staffed workshop makes,
and how accumulated method multiplies it); still_ramping(),
practice_note() and the practice/candidate-set caches
(_practisable/_practice_set/_revenue_upkeep_candidates) revenue() and
upkeep() both share; and upkeep()/institution_upkeep()/
institution_places() (what it costs to keep a concern or institution
open this year).

ProductionMixin is composed into EconomyMixin (economy.py) alongside the
other economy sub-mixins; see that file for the composition and for the
grouping evidence, and for why this lives in a separate file.
"""
from .data import trade_family
from sim.constants import declare
from . import money_units, node_revenue_market


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
        started = (getattr(projects, "opened_year", None) or {}).get(node_id)
        if started is None:
            started = projects.done_year.get(node_id, scenario.year)
        age = scenario.year - started
        return min(1.0, (age + 1) / self.cfg["revenue_ramp_years"])

    def practice_attention(self):
        """How much of your practice you are actually there to run.

        The income from practising medicine is your own two hands: it is the
        cover identity the guide tells you to adopt, and selling those same
        hours as a labourer while still collecting the full fee from a
        surgery you are not attending would count the same hours twice.
        That is an accounting error, not a balance choice.

        Only hours sold for WAGES count against it. Hours that go into your own
        projects do not: a physician who spends his evenings grinding lenses is
        still a physician in the morning, and the whole model assumes you build
        while your practice runs. Whether THAT should compete too is a real
        question and a much larger one; this is the half that is simply wrong.
        """
        # A DEAD PHYSICIAN HAS NO PRACTICE: this is your own two hands, so it
        # must go to zero the moment the founder is gone. What you built
        # outlives you; what you personally did does not.
        if not self.state.founder.founder_alive:
            return 0.0
        pool = self.director_pool()
        if pool <= 0:
            return 1.0
        sold = min(pool, self.state.household.wage_hours_this_year)
        return max(0.0, 1.0 - sold / pool)

    def revenue_capacity(self):
        """What you would earn in an ordinary year, with your own hands on your
        own work. Used where a swing in ONE year should not count - a lender
        does not cut your line because you took a job this year."""
        household = self.state.household
        _sold = household.wage_hours_this_year
        household.wage_hours_this_year = 0.0
        try:
            return self.revenue()
        finally:
            household.wage_hours_this_year = _sold

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
          - self.household.wage_hours_this_year: practice attention (e.g. temporary 0.0 in revenue_capacity)
          - self.household.farm_hectares: household farmland staples affecting food price ratio
          - self.household.gov: governance quality affecting state funding
          - self.household._inst_units_ver: scalable institution units
          - self.output_factor: hazard/war output scaling
          - self.reputation: standing affecting state funding
          - self.founder_alive: boolean for physician practice attention
        Invalidated by: Any change to any element in the composite version key tuple.
        Nested mutation concerns: household.employees wrapped in _InvalidatingDict (flat dict); workforce counts tracked in key.
        Serialized: no
        """
        scenario = self.state.scenario
        economy = self.state.economy
        projects = self.state.projects
        household = self.state.household
        governance = self.state.governance
        founder = self.state.founder
        key = (
            scenario.year,
            self.pop_scale,
            economy.output_per_head,
            getattr(projects, "_operating_ver", 0),
            getattr(projects, "_done_ver", 0),
            getattr(household, "_workforce_ver", 0),
            getattr(governance, "_inst_units_ver", 0),
            household.wage_hours_this_year,
            getattr(economy, "farm_hectares", 0.0) or 0.0,
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

    def _compute_revenue_uncached(self):
        total_revenue = 0.0
        attention = self.practice_attention()
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
            if node["rev"]:
                # AT THIS SOCIETY'S PRICES, like everything else it charges you.
                # The tree's revenue figures are labour hours and this
                # was the one flow that never converted them, so a physician's
                # practice paid exactly 233.5 in Tenochtitlan, in Luoyang and
                # in Scandinavia while the cost of building anything differed
                # by up to 1.4x. See living_cost for the other half.
                if practice:
                    total_revenue += node["rev"] * self.PRACTICE_SHARE * attention * self.price_index
                else:
                    # A SCHOOL YOU FOUNDED THREE OF EARNS THREE SCHOOLS' WORTH.
                    # institution_units is 1.0 for everything that was never
                    # expanded - the whole rest of the tree, and a single
                    # ordinary founding of the five that CAN be - so this
                    # changes nothing for a run that never asks `open` for a
                    # second one. See ProjectsMixin.institution_units.
                    _units = (self.institution_units(node_id)
                              if node_id in self.SCALABLE_INSTITUTIONS else 1.0)
                    # goods_market_factor() is 1.0 for anything outside
                    # GOODS_CATEGORIES, so this changes nothing for the
                    # services, institutions and patronage the brief asked to
                    # leave alone - see that method's own comment for why.
                    total_revenue += (node["rev"] * _units * self.venture_ramp(node_id) * self.price_index
                          * self.goods_market_factor(node_id) * self.node_output_market_factor(node))
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
        market = self.labour_market
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

    def node_output_market_factor(self, node):
        """This year's market over long-run prices for what an output-derived node sells and buys; one otherwise."""
        baskets = self.concern_baskets_now(node["id"])
        if baskets is None:
            return 1.0
        return node_revenue_market.market_factor(
            {"_output_per_year": baskets.outputs, "_purchases_per_year": baskets.purchases},
            self._material_prices(), self.market_price_ratio)

    def concern_takings(self, node_id, ramp):
        """Yearly takings of one concern at a given ramp, before market saturation: its loaded figure
        carried to the techniques held now (concern_volume.py); callers apply the market's price."""
        economy = self.state.economy
        return (self.nodes[node_id]["rev"] * ramp * economy.output_factor * self.price_index
                * self.concern_value_ratio(node_id))

    def ledger_concern_rows(self):
        """Yearly takings of every concern and practice that earns, by node
        id, as the ledger credits them."""
        rows = {}
        projects = self.state.projects
        economy = self.state.economy
        for node_id in self.done_in_order():
            practice = node_id in projects.granted and self._practisable(node_id)
            if node_id in projects.granted and not practice:
                continue
            if not practice and node_id not in projects.operating:
                continue
            node = self.nodes[node_id]
            if not node["rev"]:
                continue
            if practice:
                ramp = self.PRACTICE_SHARE
            else:
                ramp = self.venture_ramp(node_id)
            if practice:
                amt = self.concern_takings(node_id, ramp) * self.practice_attention()
            else:
                # The figure `ventures` and `why` print, and the factor
                # revenue() applies, so the ledger's parts add up to its total.
                amt = self.venture_real_earnings(node_id)
            if amt > 0.5:
                rows[node_id] = round(amt, 1)
        return rows

    def revenue_sources(self):
        """Where the money actually comes from, itemised.

        A player who never issues a single start can still get richer
        every year, from practising medicine - the cover identity the game
        tells you to adopt - which is otherwise invisible anywhere else in
        the interface.
        """
        economy = self.state.economy
        rows = self.ledger_concern_rows()
        # ALL OF IT, OR SAY WHAT IS MISSING: a ledger that shows only the
        # fifteen largest rows and nothing else does not add up to the
        # revenue it states. Every running earner has to be represented -
        # the rest as one summed row, the workshop's own output, state
        # funding, and whatever the market saturation absorbs - or the
        # accounts are visibly wrong.
        ranked = sorted(rows.items(), key=lambda entry: -entry[1])
        out = dict(ranked[:15])
        rest = sum(value for _node_id, value in ranked[15:])
        if rest > 0.5:
            out["_and_%d_smaller_concerns" % len(ranked[15:])] = round(rest, 1)
        workshop_total = self.workshop_output() * economy.output_factor
        if workshop_total > 0.5:
            out["_what_your_own_workshop_sells"] = round(workshop_total, 1)
        if self.state_funding() > 0.5:
            out["_state_funding"] = round(self.state_funding() * economy.output_factor, 1)
        # And the difference between the parts and the whole, which is the
        # market saturating: you cannot sell more inns than the town wants.
        gap = round(self.revenue() - sum(out.values()), 1)
        if abs(gap) > 1.0:
            out["_what_the_market_will_not_absorb"] = gap
        else:
            # ROUNDING IS NOT A ROW: every entry is rounded to a tenth so it
            # can be read, and a ledger that says "these add up to the
            # revenue above" has to actually survive being added up by hand
            # at that precision. Push the residue into the largest row,
            # which is the one place a tenth cannot be noticed.
            # AT ONE DECIMAL, like every other row: the residue itself has
            # to be rounded to a tenth before being added in, or it
            # reintroduces the exact mismatch this is fixing.
            resid = round(round(self.revenue(), 1) - sum(out.values()), 1)
            if out and abs(resid) > 0.049:
                # sorted(): a tie in max() over a dict falls back to insertion
                # order, which came from a set.
                big = max(sorted(out), key=lambda key: abs(out[key]))
                out[big] = round(out[big] + resid, 1)
        return out

    # Of the auto-granted nodes that carry revenue, seven are medicine and
    # two are shipping, and the difference decides who gets paid. Cataract
    # couching is a skill a single trained person practises with their own
    # hands, and practising it is exactly the cover the guide tells you to
    # adopt: PRACTISABLE_CATS credits it. A fleet of large merchant ships is
    # owned by other people and you are not entitled to its freight, so
    # shipping stays excluded. Removing the revenue from both is too blunt:
    # without practice income, a poorer civilisation paying a higher price
    # index has no way to accumulate enough for identity_cover, the first
    # node in the game.
    PRACTISABLE_CATS = {"surgery", "obstetrics", "pharmacology", "medicine",
                        "diagnosis", "dentistry"}

    def _practisable(self, node_id):
        """Is this granted node a skill YOU can practise for a fee?"""
        return self.nodes[node_id].get("cat") in self.PRACTISABLE_CATS

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

    def practice_note(self, brief=False):
        """Why the practice pays less than the tree quotes, said once, plainly.
        `brief` is the one-line form for screens that already explained it."""
        # ONLY WHAT THE LEDGER ACTUALLY SHOWS. Naming rows that were dropped
        # for being under half a denarius invites the reader to look for them.
        economy = self.state.economy
        scale = self.PRACTICE_SHARE * self.practice_attention() * economy.output_factor
        prac = sorted(node_id for node_id in self._practice_set()
                      if self.nodes[node_id]["rev"] * scale > 0.5)
        if not prac:
            return None
        if brief:
            return ("%s %s your own practice, paid at about a third of what "
                    "the tree quotes ('money full' says why)."
                    % (", ".join(prac[:4]), "is" if len(prac) == 1 else "are"))
        return ("%s %s your own practice, and %s about a third of what the tree "
                "quotes for the trade: the difference between one person in a "
                "rented room and an organised concern. That gap does not close "
                "with time. Selling your hours for wages takes another bite out "
                "of it, because you cannot be in two places."
                % (", ".join(prac[:4]),
                   "is" if len(prac) == 1 else "are",
                   "it pays" if len(prac) == 1 else "they pay"))

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
        perf_fingerprint.py's byte-for-byte, per-year state hash across nine
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
        # defence sim/engine/proto/nodes.py uses for the identical reason.
        # Holding seq and practice_set alive for as long as the entry may be
        # compared against them makes the collision structurally impossible
        # rather than merely unmeasured.
        projects = self.state.projects
        operating_version = getattr(projects, "_operating_ver", 0)
        cached = getattr(self.household, "_rev_up_candidates_cache", None)
        if (cached is not None and cached[0] is seq
                and cached[1] is practice_set and cached[2] == operating_version):
            return cached[3]
        operating = projects.operating
        cands = [node_id for node_id in seq if node_id in operating or node_id in practice_set]
        self.household._rev_up_candidates_cache = (seq, practice_set, operating_version, cands)
        return cands

    def upkeep(self):
        # Symmetrically, you do not pay to maintain what you do not own, but you
        # do bear the small standing cost of the practice you actually run - and
        # you do not pay the running costs of a concern you have not opened.
        # Both halves of that follow `operating`, so closing something really
        # does stop the bleeding, and knowing how to do something costs nothing
        # to know.
        return sum(self.upkeep_by_concern().values())

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

    def institution_upkeep(self, node_id):
        """What this concern actually costs to keep open THIS year.

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
        upkeep_amount = node["up"] * _units
        if (node_id not in self.CAPABILITY_INSTITUTIONS or upkeep_amount <= 0
                or self.mechanic(node_id, "upkeep_full")):
            return upkeep_amount
        places = self.institution_places(node_id) * _units
        if places <= 0:
            return upkeep_amount
        used = min(1.0, self.headcount() / max(1.0, places))
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
