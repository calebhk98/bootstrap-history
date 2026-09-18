"""Revenue, practices, workshops and the institutions that run them.

Split out of economy.py (see that file's own docstring for why): every
method here answers "what does the household actually take in this
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
grouping evidence.
"""
from .data import ANNUAL_WAGE, trade_family
from constants import declare


class ProductionMixin:

    STATE_FUNDING_BASE = declare(
        "STATE_FUNDING_BASE", 2500.0, kind="temporary_heuristic",
        unit="denarii/year at economy=1, state_capacity=1, pop_scale=1",
        source=None, confidence="D",
        why="What an imperial patron is worth in direct funding at a "
            "reference civilisation size and state capacity. No fiscal "
            "record backs this figure; a real answer needs a state budget "
            "model - tax revenue, the fiscus's own spending priorities - "
            "that this engine does not have, per CLAUDE.md 3.1's ban on "
            "asserting a state revenue outright.")
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

    def state_funding(self):
        if not self.running("patron_imperial"):
            return 0.0
        return (self.STATE_FUNDING_BASE * self.economy * self.state_capacity
                * self.pop_scale ** self.STATE_FUNDING_POP_SCALE_EXPONENT
                * (1.0 + max(0.0, self.household.gov) / self.STATE_FUNDING_GOV_QUALITY_SCALE)
                * self.rep_factor())

    def venture_ramp(self, k):
        """How much of its full takings a concern is making, 0..1.

        FROM THE YEAR YOU OPENED IT, not the year you worked out how. This read
        done_year, so a concern built in 100 and opened in 130 was at full
        takings the day its doors opened - which made delaying `open` strictly
        better than opening promptly, and made the ledger's own sentence ("a
        concern you open reaches its full figure over 3 years") false in the
        one case a break tester checked. Custom takes time to find whoever owns
        the shop.
        """
        started = (getattr(self.household, "opened_year", None) or {}).get(k)
        if started is None:
            started = self.household.done_year.get(k, self.year)
        age = self.year - started
        return min(1.0, (age + 1) / self.cfg["revenue_ramp_years"])

    def practice_attention(self):
        """How much of your practice you are actually there to run.

        The income from practising medicine is your own two hands: it is the
        cover identity the guide tells you to adopt, and a weird-play tester
        found you could sell every one of your 2,400 hours as a labourer and
        still collect the full fee from a surgery you were demonstrably not in.
        That is the same hours sold twice, which is an accounting error rather
        than a balance choice.

        Only hours sold for WAGES count against it. Hours that go into your own
        projects do not: a physician who spends his evenings grinding lenses is
        still a physician in the morning, and the whole model assumes you build
        while your practice runs. Whether THAT should compete too is a real
        question and a much larger one; this is the half that is simply wrong.
        """
        # A DEAD PHYSICIAN HAS NO PRACTICE. This is your own two hands, and a
        # break tester watched the surgery go on taking fees for eleven years
        # after the founder was buried. What you built outlives you; what you
        # personally did does not.
        if not self.founder_alive:
            return 0.0
        pool = self.director_pool()
        if pool <= 0:
            return 1.0
        sold = min(pool, getattr(self.household, "wage_hours_this_year", 0.0))
        return max(0.0, 1.0 - sold / pool)

    def revenue_capacity(self):
        """What you would earn in an ordinary year, with your own hands on your
        own work. Used where a swing in ONE year should not count - a lender
        does not cut your line because you took a job this year."""
        _sold = getattr(self.household, "wage_hours_this_year", 0.0)
        self.household.wage_hours_this_year = 0.0
        try:
            return self.revenue()
        finally:
            self.household.wage_hours_this_year = _sold

    def revenue(self):
        total_revenue = 0.0
        attention = self.practice_attention()
        practice_set = self._practice_set()
        granted = self.household.granted
        operating = self.household.operating
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
                # The tree's revenue figures are Rome 100 AD denarii and this
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
                          * self.goods_market_factor(node_id))
        # THERE IS ONLY SO MUCH MARKET. Uncapped, this compounds: every venture
        # pays back inside two years, so its income buys the next one, and a run
        # ended holding three billion denarii against an empire whose entire
        # annual product was perhaps five billion. Testers saw the near end of
        # it and said so plainly: "I have far more capital than I have good
        # places to put it". You cannot sell more inns than the town wants, and
        # a saturating curve says that without ever making a venture worthless.
        # WHAT YOUR OWN WORKSHOP SELLS. Charging wages explicitly without
        # crediting the work was half an accounting change: in the old model a
        # trained staff was free and its output was folded invisibly into node
        # revenue, so adding a payroll of 12,000 a year and no corresponding
        # output made every civilization except Rome unable to finish. Thirty
        # craftsmen in a workshop do not sit there costing money. They make
        # things, and the things are sold.
        #
        # It is deliberately less than a 2x markup on wages and it needs somewhere
        # to work: a staff with no workshop is an expense, which is exactly why
        # workshop_first matters and why it is cheap.
        total_revenue += self.workshop_output()
        gross = total_revenue * (self.economy ** self.ECONOMY_OUTPUT_SCALING_EXPONENT)
        ceiling = self.REVENUE_CEILING_PER_POP_SCALE * self.pop_scale \
            * (self.economy ** self.ECONOMY_OUTPUT_SCALING_EXPONENT) * self.price_index
        gross = gross / (1.0 + gross / max(1.0, ceiling))
        return (gross + self.state_funding()) * self.output_factor

    ECONOMY_OUTPUT_SCALING_EXPONENT = declare(
        "ECONOMY_OUTPUT_SCALING_EXPONENT", 0.75, kind="temporary_heuristic",
        unit="dimensionless exponent on self.economy", source=None,
        confidence="D",
        why="How sub-linearly overall output grows with the `economy` "
            "index (economy_index(), itself already a temporary_heuristic "
            "curve - see ECONOMY_INDEX_PER_DIFFUSED_NODE above), used "
            "everywhere gross revenue is scaled by it in this file. The "
            "sub-linear SHAPE reflects real diminishing returns to a single "
            "aggregate multiplier; the specific 0.75 exponent is tuned "
            "against playtests, not fitted to any output data.")
    REVENUE_CEILING_PER_POP_SCALE = declare(
        "REVENUE_CEILING_PER_POP_SCALE", 900000.0, kind="temporary_heuristic",
        unit="denarii/year at pop_scale=1, economy=1", source=None,
        confidence="D",
        why="The saturating ceiling on how much revenue a single founder's "
            "ventures can pull out of one civilisation's whole market - "
            "invented specifically to stop a run compounding into billions "
            "against an empire whose own annual product is not separately "
            "modelled (see this method's own comment on the tester who held "
            "three billion denarii). A real ceiling needs an actual GDP "
            "figure for the civilisation to compare against, which this "
            "engine does not compute.")

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
    DEFAULT_ARTISAN_WAGE_FALLBACK = declare(
        "DEFAULT_ARTISAN_WAGE_FALLBACK", 250.0, kind="temporary_heuristic",
        unit="denarii/year", source=None, confidence="D",
        why="As DEFAULT_ANNUAL_WAGE_FALLBACK, specifically for the generic "
            "'artisan' trade freedmen and slaves are costed against - lower "
            "than the craft fallback because 'artisan' is treated as the "
            "least skilled craft tier. Not sourced to any attested wage.")
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
    WORKSHOP_MARKUP_BONUS_INTERCHANGEABLE_PARTS = declare(
        "WORKSHOP_MARKUP_BONUS_INTERCHANGEABLE_PARTS", 0.35,
        kind="temporary_heuristic", unit="extra output denarii per denarius of wages",
        source=None, confidence="D",
        why="How much interchangeable parts (a real productivity-raising "
            "technology) raises the workshop markup. The DIRECTION is a "
            "real historical claim; the SIZE is tuned game feel, not "
            "derived from any attested productivity gain from "
            "interchangeability specifically.")
    WORKSHOP_MARKUP_BONUS_POWER_GRID = declare(
        "WORKSHOP_MARKUP_BONUS_POWER_GRID", 0.45, kind="temporary_heuristic",
        unit="extra output denarii per denarius of wages", source=None,
        confidence="D",
        why="As WORKSHOP_MARKUP_BONUS_INTERCHANGEABLE_PARTS, for electrical "
            "power - larger because electrification is judged the bigger "
            "productivity jump of the two, a judgement call rather than a "
            "measurement.")

    def workshop_output(self):
        """What your standing staff produces and sells, over and above projects."""
        if not (self.running("workshop_first") or self.running("school_founded")):
            return 0.0
        craft = sum(count for trade, count in self.household.employees.items() if trade_family(trade) == "craft")
        craft += self.household.freedmen + self.household.slaves * self.SLAVE_LABOUR_PRODUCTIVITY_SHARE
        wage = 0.0
        for trade, count in self.household.employees.items():
            if trade_family(trade) == "craft":
                wage += count * ANNUAL_WAGE.get(trade, self.DEFAULT_ANNUAL_WAGE_FALLBACK)
        wage += ((self.household.freedmen + self.household.slaves * self.SLAVE_LABOUR_PRODUCTIVITY_SHARE)
                 * ANNUAL_WAGE.get("artisan", self.DEFAULT_ARTISAN_WAGE_FALLBACK))
        mark = self.WORKSHOP_WAGE_MARKUP_BASE
        if self.running("interchangeable_parts"):  mark += self.WORKSHOP_MARKUP_BONUS_INTERCHANGEABLE_PARTS
        if self.running("power_grid"):             mark += self.WORKSHOP_MARKUP_BONUS_POWER_GRID
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
        return (wage * mark * self.capability_factor()
                * self.wage_index * self.price_index)

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
        for node_id in self.done_in_order():
            if node_id in self.household.granted or node_id in self.household.operating:
                continue
            node = self.nodes[node_id]
            if node["rev"] <= 0:
                continue
            weight += node["rev"]
        result = 1.0 + self.CAPABILITY_FACTOR_CEILING_BONUS * (
            weight / (weight + self.CAPABILITY_FACTOR_HALF_SATURATION_REV))
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
    CAPABILITY_FACTOR_HALF_SATURATION_REV = declare(
        "CAPABILITY_FACTOR_HALF_SATURATION_REV", 40000.0,
        kind="temporary_heuristic", unit="denarii of tier-weighted revenue "
        "at half of CAPABILITY_FACTOR_CEILING_BONUS", source=None,
        confidence="D",
        why="How much accumulated tier-weighted method it takes to reach "
            "half the maximum capability bonus - the saturating curve's "
            "own scale. Tuned against playtests (see the comment this "
            "replaces: '40,000 of tier-weighted method roughly doubles "
            "what a workshop makes'), not fitted to any measured "
            "productivity data.")

    def revenue_sources(self):
        """Where the money actually comes from, itemised.

        Testers asked this three separate times and could not answer it: "there
        is no visible in-fiction source for it", "a player who never issues a
        single start still gets richer every year". Both were looking at the
        income from practising medicine, which is the cover identity the game
        tells you to adopt, and neither had any way to find that out.
        """
        rows = {}
        for node_id in self.done_in_order():
            practice = node_id in self.household.granted and self._practisable(node_id)
            if node_id in self.household.granted and not practice:
                continue
            if not practice and node_id not in self.household.operating:
                continue
            node = self.nodes[node_id]
            if not node["rev"]:
                continue
            if practice:
                ramp = self.PRACTICE_SHARE
            else:
                ramp = self.venture_ramp(node_id)
            amt = (node["rev"] * ramp * (self.economy ** self.ECONOMY_OUTPUT_SCALING_EXPONENT) * self.output_factor
                   * self.price_index)
            if practice:
                amt *= self.practice_attention()
            else:
                # SAME FACTOR revenue() APPLIES, so this row and the total it
                # is supposed to add up to do not silently disagree - see the
                # "the ledger's parts add up to the revenue it states" check.
                amt *= self.goods_market_factor(node_id)
            if amt > 0.5:
                rows[node_id] = round(amt, 1)
        # ALL OF IT, OR SAY WHAT IS MISSING. This returned the fifteen largest
        # rows and nothing else, so a break tester summed what the ledger
        # listed, got 7,101.9 against a stated revenue of 6,738, and correctly
        # reported that the accounts do not add up - two running earners were
        # simply not shown, and the workshop's own output and the saturation
        # that caps the whole figure were never rows at all.
        ranked = sorted(rows.items(), key=lambda kv: -kv[1])
        out = dict(ranked[:15])
        rest = sum(value for _node_id, value in ranked[15:])
        if rest > 0.5:
            out["_and_%d_smaller_concerns" % len(ranked[15:])] = round(rest, 1)
        workshop_total = self.workshop_output() * (self.economy ** self.ECONOMY_OUTPUT_SCALING_EXPONENT) * self.output_factor
        if workshop_total > 0.5:
            out["_what_your_own_workshop_sells"] = round(workshop_total, 1)
        if self.state_funding() > 0.5:
            out["_state_funding"] = round(self.state_funding() * self.output_factor, 1)
        # And the difference between the parts and the whole, which is the
        # market saturating: you cannot sell more inns than the town wants.
        gap = round(self.revenue() - sum(out.values()), 1)
        if abs(gap) > 1.0:
            out["_what_the_market_will_not_absorb"] = gap
        else:
            # ROUNDING IS NOT A ROW. Every entry is rounded to a tenth so it
            # can be read, and a ledger that says "these add up to the revenue
            # above" has to survive being added up: a break tester summed two
            # rows, got 166.7 + 66.7 = 233.4 under a stated 233.5, and filed
            # the claim as false in one line. Push the residue into the largest
            # row, which is the one place a tenth cannot be noticed.
            # AT ONE DECIMAL, like every other row. Pushing the raw residue in
            # wrote 166.8394 onto a line the player reads; the rows and the
            # total both live at a tenth, so the correction has to as well.
            resid = round(round(self.revenue(), 1) - sum(out.values()), 1)
            if out and abs(resid) > 0.049:
                # sorted(): a tie in max() over a dict falls back to insertion
                # order, which came from a set.
                big = max(sorted(out), key=lambda k: abs(out[k]))
                out[big] = round(out[big] + resid, 1)
        return out

    # Of the auto-granted nodes that carry revenue, seven are medicine and two
    # are shipping, and the difference decides who gets paid. Cataract couching
    # is a skill a single trained person practises with their own hands, and
    # practising it is exactly the cover the guide tells you to adopt. A fleet
    # of large merchant ships is owned by other people and you are not entitled
    # to its freight. Removing the revenue from BOTH, which is what I did first,
    # was too blunt: it left every civilization with no way to earn a living at
    # all, and the Norse, who are poorer and pay a 1.4 price index, could then
    # never accumulate the 1,580 denarii for identity_cover. They failed 100% of
    # runs, blocked on the first node in the game.
    PRACTISABLE_CATS = {"surgery", "obstetrics", "pharmacology", "medicine",
                        "diagnosis", "dentistry"}

    def _practisable(self, k):
        """Is this granted node a skill YOU can practise for a fee?"""
        return self.nodes[k].get("cat") in self.PRACTISABLE_CATS

    def still_ramping(self):
        """Earners that are not yet paying their full figure, and how far along.

        Every earner ramps over revenue_ramp_years, so on the day you open one
        it pays a third of what the tree quotes for it. A break tester read
        `why` at 500 a year, opened it, saw 166.7 in the ledger, and had
        nothing anywhere to tell them whether the ledger was wrong, the quote
        was wrong, or they were being charged for something. It is none of
        those: it is year one of three. Kept OUT of revenue_sources, whose
        every value is a number that has to sum to the revenue above it.
        """
        young = []
        for node_id in sorted(self.household.operating):
            node = self.nodes.get(node_id)
            if not node or not node["rev"] or node_id in self.household.granted:
                continue
            ramp = self.venture_ramp(node_id)
            if ramp < 0.999:
                young.append((node_id, ramp))
        if not young:
            return None
        young.sort(key=lambda kv: kv[1])
        return ("%s%s at %d%% of full takings. A concern you open reaches its "
                "full figure over %g years, so what the ledger shows is not "
                "what it will be."
                % (", ".join(node_id for node_id, _ramp in young[:6]),
                   " and %d more" % (len(young) - 6) if len(young) > 6 else "",
                   young[0][1] * 100, self.cfg["revenue_ramp_years"]))

    def practice_note(self):
        """Why the practice pays less than the tree quotes, said once, plainly."""
        # ONLY WHAT THE LEDGER ACTUALLY SHOWS. Naming rows that were dropped
        # for being under half a denarius invites the reader to look for them.
        scale = (self.PRACTICE_SHARE * self.practice_attention()
                 * (self.economy ** self.ECONOMY_OUTPUT_SCALING_EXPONENT) * self.output_factor)
        prac = sorted(node_id for node_id in self._practice_set()
                      if self.nodes[node_id]["rev"] * scale > 0.5)
        if not prac:
            return None
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
        cache = getattr(self.household, "_practice_cache", None)
        if cache is None or cache[0] != len(self.household.granted):
            cache = (len(self.household.granted),
                     frozenset(node_id for node_id in self.household.granted if self._practisable(node_id)))
            self.household._practice_cache = cache
        return cache[1]

    def _revenue_upkeep_candidates(self):
        """Every node in `done` that revenue() or upkeep() could possibly
        charge or pay for - i.e. that is operating, or in your practice
        set - in done_in_order()'s own tree order. Neither function can do
        anything with a node that is neither, so both used to scan the
        WHOLE of `done` (every technology ever finished, which is most of
        the tree by the late game) just to throw almost all of it away
        again on that same test; this is the small subset that survives it,
        computed once and handed to both.

        A 150-year rome_100ad profile of 150 optimizer steps found revenue()
        alone at 9,037 calls and 1.428s cumulative, and upkeep() at 4,293
        calls (upkeep's own summing genexpr showing up separately at
        120,922 calls) - both walking done_in_order() start to finish on
        every one of those, when `operating` and the practice set together
        are typically a handful of concerns against a `done` list that only
        grows. This is exactly the O(active) vs O(done) gap done_in_order()
        itself was already added to close for a DIFFERENT quadratic blowup
        (see its own docstring); the list is short but the SCAN was still
        long.

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
        # _cached_demand_by_tag() below now spells out at length: a freed
        # object's address is handed straight to the next same-sized
        # allocation, so two different objects compare equal by id() often
        # enough to matter, and the cache replays a stale answer under a fresh
        # one. That is what made this simulation non-deterministic, in the
        # sibling cache rather than this one.
        #
        # This one had not been shown to be firing. It had been PROBED and
        # come back clean - 0 stale answers in 64,157 calls - and that probe
        # was worthless, because it allocated a comparison list on every call
        # and allocation is precisely what decides whether an address gets
        # recycled. It suppressed the effect it was measuring. The same false
        # negative cleared the cache that turned out to be guilty.
        #
        # So this is not a fix for an observed bug. It is the removal of a
        # hazard that cannot be cheaply observed, in the one shape known to
        # have already cost this project a day, by the defence
        # sim/engine/proto/nodes.py chose for the identical reason. Holding
        # seq and practice_set alive for as long as the entry may be compared
        # against them makes the collision structurally impossible rather than
        # merely unmeasured.
        operating_version = getattr(self.household, "_operating_ver", 0)
        cached = getattr(self.household, "_rev_up_candidates_cache", None)
        if (cached is not None and cached[0] is seq
                and cached[1] is practice_set and cached[2] == operating_version):
            return cached[3]
        operating = self.household.operating
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
        practice_set = self._practice_set()
        return sum(self.institution_upkeep(node_id)
                   for node_id in self._revenue_upkeep_candidates()
                   if node_id in self.household.operating or node_id in practice_set)

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

    def institution_upkeep(self, k):
        """What this concern actually costs to keep open THIS year.

        For almost everything, its upkeep. For an establishment whose purpose is
        to support PEOPLE - a school, an academy, a workshop, a licensed
        collegium, a freedman staff - it scales with how much of that support you
        are using, because a school with three scholars in it does not cost what
        a school with forty does. Endowed schools historically scaled with
        enrolment and so should this.

        This is the bridge the capability change needed. Making capability follow
        running() was right: a founder used to collect a school's twelve
        scholars and an imperial patron's sixty thousand of credit without ever
        opening either, and without paying a denarius toward them. But it priced
        every institution as though the place were full on the day you founded
        it, and that killed the first rung of the ladder.
        """
        node = self.nodes[k]
        # A THIRD SCHOOL COSTS THREE SCHOOLS' UPKEEP, at three schools' worth
        # of places to fill it against - both sides of this scale together so
        # a run that never founds more than the original single unit sees
        # exactly the arithmetic it always did. See
        # ProjectsMixin.institution_units.
        #
        # NOT YET OPEN MEANS "WHAT WOULD A FIRST FOUNDING COST", not zero.
        # auto_open_ventures (projects.py) calls this on things it has not
        # opened yet to decide whether to; institution_units answers 0 for
        # anything not currently operating, and multiplying by that turned
        # every unopened institution's prospective upkeep into a small
        # negative number (upkeep 0 against real revenue), which read as free
        # and let the affordability gate through on nothing.
        _units = (self.institution_units(k) if k in self.household.operating else 1.0) \
            if k in self.SCALABLE_INSTITUTIONS else 1.0
        upkeep_amount = node["up"] * _units
        if k not in self.CAPABILITY_INSTITUTIONS or upkeep_amount <= 0:
            return upkeep_amount
        places = self.institution_places(k) * _units
        if places <= 0:
            return upkeep_amount
        used = min(1.0, self.headcount() / max(1.0, places))
        return upkeep_amount * (self.INSTITUTION_FLOOR
                     + (1.0 - self.INSTITUTION_FLOOR) * used)

    _INSTITUTION_PLACES_WHY = (
        "Roughly how many people one unit of this institution is built "
        "to support, for institution_upkeep()'s enrolment-scaled "
        "billing. Read off labour.py's STAFF_CAPACITY_SOURCES table "
        "(outside this file's scope) by hand, mostly as that row's "
        "'sc'+'ar' staffing columns - not a strict, checked formula, so "
        "the two tables can drift apart if one changes without the "
        "other; a real fix would derive institution_places() FROM "
        "STAFF_CAPACITY_SOURCES directly instead of copying a number "
        "read off it.")
    INSTITUTION_PLACES_WORKSHOP_FIRST = declare(
        "INSTITUTION_PLACES_WORKSHOP_FIRST", 12.0,
        kind="temporary_heuristic", unit="people per unit",
        source=None, confidence="D", why=_INSTITUTION_PLACES_WHY)
    INSTITUTION_PLACES_SCHOOL_FOUNDED = declare(
        "INSTITUTION_PLACES_SCHOOL_FOUNDED", 34.0,
        kind="temporary_heuristic", unit="people per unit",
        source=None, confidence="D", why=_INSTITUTION_PLACES_WHY)
    INSTITUTION_PLACES_ACADEMY_NETWORK = declare(
        "INSTITUTION_PLACES_ACADEMY_NETWORK", 120.0,
        kind="temporary_heuristic", unit="people per unit",
        source=None, confidence="D", why=_INSTITUTION_PLACES_WHY)
    INSTITUTION_PLACES_FREEDMAN_STAFF = declare(
        "INSTITUTION_PLACES_FREEDMAN_STAFF", 10.0,
        kind="temporary_heuristic", unit="people per unit",
        source=None, confidence="D", why=_INSTITUTION_PLACES_WHY)
    INSTITUTION_PLACES_COLLEGIUM_LICENSED = declare(
        "INSTITUTION_PLACES_COLLEGIUM_LICENSED", 3.0,
        kind="temporary_heuristic", unit="people per unit",
        source=None, confidence="D", why=_INSTITUTION_PLACES_WHY)
    INSTITUTION_PLACES_PATRON_SENATORIAL = declare(
        "INSTITUTION_PLACES_PATRON_SENATORIAL", 10.0,
        kind="temporary_heuristic", unit="people per unit",
        source=None, confidence="D", why=_INSTITUTION_PLACES_WHY)
    INSTITUTION_PLACES_PATRON_IMPERIAL = declare(
        "INSTITUTION_PLACES_PATRON_IMPERIAL", 64.0,
        kind="temporary_heuristic", unit="people per unit",
        source=None, confidence="D", why=_INSTITUTION_PLACES_WHY)
    INSTITUTION_PLACES_ENDOWMENT_LAND = declare(
        "INSTITUTION_PLACES_ENDOWMENT_LAND", 14.0,
        kind="temporary_heuristic", unit="people per unit",
        source=None, confidence="D", why=_INSTITUTION_PLACES_WHY)
    INSTITUTION_PLACES_CORPUS_DISPERSED = declare(
        "INSTITUTION_PLACES_CORPUS_DISPERSED", 8.0,
        kind="temporary_heuristic", unit="people per unit",
        source=None, confidence="D", why=_INSTITUTION_PLACES_WHY)
    INSTITUTION_PLACES_INTERCHANGEABLE_PARTS = declare(
        "INSTITUTION_PLACES_INTERCHANGEABLE_PARTS", 44.0,
        kind="temporary_heuristic", unit="people per unit",
        source=None, confidence="D", why=_INSTITUTION_PLACES_WHY)
    # Read off STAFF_CAPACITY_SOURCES (labour.py) the same way
    # every other row here is: a unit's ar+di, so a chain store
    # with three people in it is not billed as though every
    # branch were already fully staffed.
    INSTITUTION_PLACES_FIN_COMPANY_TOWN = declare(
        "INSTITUTION_PLACES_FIN_COMPANY_TOWN", 20.0,
        kind="temporary_heuristic", unit="people per unit",
        source="labour.py STAFF_CAPACITY_SOURCES row for "
               "fin_company_town: ar=20.0, di=0.0.",
        confidence="D", why=_INSTITUTION_PLACES_WHY)
    INSTITUTION_PLACES_FIN_CHAIN_STORE = declare(
        "INSTITUTION_PLACES_FIN_CHAIN_STORE", 34.0,
        kind="temporary_heuristic", unit="people per unit",
        source="labour.py STAFF_CAPACITY_SOURCES row for "
               "fin_chain_store: ar=30.0, di=4.0.",
        confidence="D", why=_INSTITUTION_PLACES_WHY)
    INSTITUTION_PLACES = {
        'workshop_first': INSTITUTION_PLACES_WORKSHOP_FIRST,
        'school_founded': INSTITUTION_PLACES_SCHOOL_FOUNDED,
        'academy_network': INSTITUTION_PLACES_ACADEMY_NETWORK,
        'freedman_staff': INSTITUTION_PLACES_FREEDMAN_STAFF,
        'collegium_licensed': INSTITUTION_PLACES_COLLEGIUM_LICENSED,
        'patron_senatorial': INSTITUTION_PLACES_PATRON_SENATORIAL,
        'patron_imperial': INSTITUTION_PLACES_PATRON_IMPERIAL,
        'endowment_land': INSTITUTION_PLACES_ENDOWMENT_LAND,
        'corpus_dispersed': INSTITUTION_PLACES_CORPUS_DISPERSED,
        'interchangeable_parts': INSTITUTION_PLACES_INTERCHANGEABLE_PARTS,
        'fin_company_town': INSTITUTION_PLACES_FIN_COMPANY_TOWN,
        'fin_chain_store': INSTITUTION_PLACES_FIN_CHAIN_STORE,
    }
    INSTITUTION_PLACES_FALLBACK_UPKEEP_PER_HEAD = declare(
        "INSTITUTION_PLACES_FALLBACK_UPKEEP_PER_HEAD", 250.0,
        kind="temporary_heuristic", unit="denarii of upkeep per head",
        source=None, confidence="D",
        why="For an institution not in INSTITUTION_PLACES, how many "
            "denarii of upkeep one person's worth of capacity is assumed "
            "to cost, so an arbitrary institution still scales with "
            "headcount instead of defaulting to zero places. 'About a "
            "wage a head' per the comment this replaces - the right ORDER "
            "of magnitude for a building whose cost is its people, not a "
            "specific attested wage.")

    def institution_places(self, k):
        """Roughly how many people ONE UNIT of this establishment is built to
        support - see institution_upkeep, which multiplies this by
        institution_units(k) itself, so callers wanting the total should read
        that, not this, for anything in SCALABLE_INSTITUTIONS.

        Read off the same table staff_capacity() and supervision_room() use, so
        that the cost of a place and the existence of a place cannot drift
        apart. Anything absent is sized by its own upkeep at about a wage a
        head, the right order for a building whose cost is its people.
        """
        if k in self.INSTITUTION_PLACES:
            return self.INSTITUTION_PLACES[k]
        return max(1.0, self.nodes[k]["up"] / self.INSTITUTION_PLACES_FALLBACK_UPKEEP_PER_HEAD)
