"""Buying people, freeing them, and keeping the two staff pools honest.

These are methods of Sim; they are a mixin only so that they can live in a
file of their own (see labour.py's own docstring for the split).

buy_slaves and manumit are the two sides of the model CLAUDE.md 3.1 asks
for rather than hides: Roman labour is cheap because much of it is
coerced, and manumission is modelled as strictly better on the numbers as
well as on every other ground. slave_quote is the market depth and rising-
price curve buy_slaves prices against, the same saturating idea labour_
population.py applies to ordinary hiring. _grant_staff and _resync_pools
are the bookkeeping underneath both verbs and underneath every institution
that hands a household trained people outright (a school's own
professors, a patron's freedmen): _grant_staff records what an institution
granted so _resync_pools - which runs unconditionally every step() and
rebuilds self.household.scholars/artisans from the trades actually on the
books - does not overwrite the grant out of existence.
"""
from .data import trade_family
from sim.constants import declare


class BondageMixin:
    """Buying and freeing people, and the pool bookkeeping that keeps
    trained/granted staff from being overwritten or double-counted - see
    this module's own docstring for why these sit together.
    """


    def _grant_staff(self, scholars=0.0, artisans=0.0):
        """An institution hands you people outright, on completion - the
        school's own professors, the freedmen a patron staffs your workshop
        with. They are not on the payroll you can fire (their keep is already
        inside the institution's own upkeep), so they do not belong in
        `self.household.employees`; they have to survive `_resync_pools()` some other
        way, which is what this records.

        `_resync_pools()` runs unconditionally every single step() and
        rebuilds self.household.scholars / self.household.artisans from
        `self.household.employees` alone, so anything `_complete()` grants
        outright has to be recorded here rather than added straight to
        those two fields: an addition that bypasses this record is silently
        overwritten and discarded the next time `_resync_pools()` runs.
        """
        granted = getattr(self.household, "granted_staff", None)
        if granted is None:
            granted = self.household.granted_staff = {"scholars": 0.0, "artisans": 0.0}
        granted["scholars"] = granted.get("scholars", 0.0) + scholars
        granted["artisans"] = granted.get("artisans", 0.0) + artisans
        self.household.scholars += scholars
        self.household.artisans += artisans

    FREEDMAN_ARTISAN_PRODUCTIVITY = declare(
        "FREEDMAN_ARTISAN_PRODUCTIVITY", 1.0, kind="temporary_heuristic",
        unit="fraction of a full worker's artisan capacity", source=None,
        confidence="D",
        why="A trained, freed person counts as a full worker. Paired with "
            "TRAINED_SLAVE_ARTISAN_PRODUCTIVITY below: the gap between the "
            "two is this model's stand-in for the real productivity cost "
            "of coercion, which nothing here derives from an actual "
            "measured difference in enslaved versus free labour output.")
    TRAINED_SLAVE_ARTISAN_PRODUCTIVITY = declare(
        "TRAINED_SLAVE_ARTISAN_PRODUCTIVITY", 0.7, kind="temporary_heuristic",
        unit="fraction of a full worker's artisan capacity", source=None,
        confidence="D",
        why="A trained person still held as a slave is worth less than a "
            "freedman doing the same work - coerced labour is real but "
            "worse, which is also the whole argument for manumission "
            "being strictly better on these numbers (see buy_slaves' own "
            "docstring). The specific 0.7 is tuned game balance, not a "
            "measured efficiency gap.")

    def _resync_pools(self):
        """Recompute the two aggregate pools the tech tree asks for from the
        actual people on the books. `art` and `sch` in the tree mean "trained
        people who understand your methods", so they are the sum of the trades,
        not a number that floats free of them.

        ONLY `scholar` COUNTS AS A TRAINED SCHOLAR. TRADE_FAMILY groups
        scholar, chemist, engineer, scribe and merchant together as
        "scholar" - and that grouping is real and stays exactly as it is for
        market_supply(), where it means "draws on the same small, literate-
        or-propertied slice of the population", which is equally true of all
        five. It is not the same claim as "is a trained natural philosopher":
        a node gated on "2 trained scholars" must be started on the strength
        of people actually trained as scholars, not on scribes, chemists,
        engineers or merchants who have never been asked to do a
        philosopher's work. STAFF_SOURCES - the advice this same household
        is given on how to get scholars - names only `hire scholar` and
        never the other four, for the same reason: the five-way grouping is
        sized for the labour MARKET, not the staff ROSTER. train()'s own
        docstring already makes the non-interchangeability of the taught
        trades explicit ("the machinists you made are no use at all when
        you need a chemist");
        nothing about a chemist makes them a scholar either.

        PLUS WHAT AN INSTITUTION GRANTED OUTRIGHT. See _grant_staff: those
        people are real and already paid for out of the institution's own
        upkeep, and this is the one place that ever told self.household.scholars and
        self.household.artisans what they are, so it is the one place that has to add
        the grant back rather than let it be overwritten out of existence.
        """
        craft = sum(count for trade, count in self.household.employees.items() if trade_family(trade) == "craft")
        schol = self.household.employees.get("scholar", 0.0)
        granted = getattr(self.household, "granted_staff", None) or {}
        # PEOPLE STILL LEARNING ARE NOT YET CRAFTSMEN. This function
        # recomputes self.household.artisans from scratch on every call, so
        # anyone still in the training queue must be excluded from the count
        # here: counting them early makes the training lag that buy_slaves'
        # own docstring promises do nothing. Once a training row matures and
        # step() adds its capacity to self.household.artisans directly, this
        # function must not count that person via `learning` again - by
        # then they are simply part of `owned` below.
        # buy_slaves stores WORKER_EQUIVALENT_UNTRAINED of a worker per person
        # bought, so that is the divisor that recovers the headcount still
        # learning.
        learning = sum(row[0] for row in getattr(self.household, "training", ())
                       if len(row) <= 2) / self.WORKER_EQUIVALENT_UNTRAINED
        owned = max(0.0, self.household.freedmen + self.household.slaves - learning)
        # Split what is left in the same proportion as what is held.
        held = self.household.freedmen + self.household.slaves
        if held > 0:
            free_share = self.household.freedmen / held
        else:
            free_share = 0.0
        self.household.artisans = (craft + owned * free_share * self.FREEDMAN_ARTISAN_PRODUCTIVITY
                         + owned * (1.0 - free_share) * self.TRAINED_SLAVE_ARTISAN_PRODUCTIVITY
                         + granted.get("artisans", 0.0))
        self.household.scholars = schol + granted.get("scholars", 0.0)

    TRAINING_YEARS = declare(
        "TRAINING_YEARS", 3.0, kind="temporary_heuristic",
        unit="years", source=None, confidence="D",
        why="How long a newly-bought or newly-trained person takes to "
            "mature into a useful worker - nobody is a useful artisan the "
            "week you buy them. Tuned to make the training lag real "
            "without being punitive; not measured from any real "
            "apprenticeship length (met_trip_hammer and similar nodes' "
            "own multi-year floors are a separate, better-sourced figure "
            "for a different thing).")

    SLAVE_MARKET_DEPTH_FLOOR = declare(
        "SLAVE_MARKET_DEPTH_FLOOR", 8.0, kind="temporary_heuristic",
        unit="people", source=None, confidence="D",
        why="The smallest a local slave market's depth is ever assumed to "
            "be, even at pop_scale near zero, so a tiny civilisation still "
            "has SOME market rather than an infinitely steep price curve. "
            "Tuned floor, not measured.")
    SLAVE_MARKET_DEPTH_SCALE = declare(
        "SLAVE_MARKET_DEPTH_SCALE", 40.0, kind="temporary_heuristic",
        unit="people, at pop_scale=1.0", source=None, confidence="D",
        why="How deep a full-size civilisation's local slave market is "
            "assumed to be before price pressure really bites - a market-"
            "size assumption, not an attested number of people traded "
            "anywhere in this game's period.")
    SLAVE_MARKET_DEPTH_POP_EXPONENT = declare(
        "SLAVE_MARKET_DEPTH_POP_EXPONENT", 0.5, kind="temporary_heuristic",
        unit="dimensionless exponent on pop_scale", source=None,
        confidence="D",
        why="Sub-linear (square-root) growth of slave-market depth with "
            "population, the same diminishing-returns shape this file "
            "uses elsewhere for a market that does not scale one-for-one "
            "with population size. Tuned shape, not fitted.")
    SLAVE_PRICE_CONGESTION_EXPONENT = declare(
        "SLAVE_PRICE_CONGESTION_EXPONENT", 1.85, kind="temporary_heuristic",
        unit="dimensionless (1 + congestion power)", source=None,
        confidence="D",
        why="The exponent of the rising-price curve integrated across a "
            "purchase (nth head costs more than the first): 1.0 (linear "
            "count) plus 0.85 of super-linear congestion as you buy "
            "deeper into the local market. The congestion power is tuned "
            "to make buying in bulk or in quick slices cost the same "
            "(see this function's own docstring on the exploit this "
            "closed), not derived from an observed price-quantity curve "
            "for any real slave market.")
    SLAVE_BASE_PRICE_DENARII = declare(
        "SLAVE_BASE_PRICE_DENARII", 300.0, kind="hardcoded_outcome",
        unit="denarii, at price_index=1 and zero market pressure",
        source=None, confidence="D",
        why="The list price of one person before any congestion surcharge "
            "- a flat number this file asserts rather than derives from "
            "food, security, transport and recruitment costs the way "
            "CLAUDE.md 3.1 asks a price to be derived. §3.1 CANDIDATE: "
            "this is exactly the shape the Roman-soldier example in "
            "CLAUDE.md warns about (a person's price stated outright "
            "rather than computed from the underlying scarcity), and "
            "RECLASSIFIED as hardcoded_outcome on that basis. The agent that "
            "declared it argued the opposite - that unlike DEBT_BASE_RATE "
            "this is not an attested historical figure, just a "
            "plausible-looking round number - which is true and is the "
            "wrong axis: an INVENTED price is worse than a copied one, "
            "because at least the copied one is right about the world. "
            "What the kind tests is whether the quantity is an OUTPUT "
            "this simulation should compute, not where the number came "
            "from. A real mechanism would price a person the way "
            "labour.py now prices free labour: from local supply, risk "
            "and what the buyer can actually enforce.")

    def slave_quote(self, n_people):
        """What buying this many people actually costs, here, today.

        A town's slave market has a depth; buying beyond it bids the price
        up, so no purchase clears at flat list price regardless of size.
        """
        if n_people <= 0:
            return 0.0
        # The surcharge has to remember across calls: a market that resets
        # between two purchases made in the same instant is not a market.
        # market_pressure accumulates with every purchase and decays each
        # year as sellers restock, so buying in slices is priced as one
        # large purchase unless you actually wait between them.
        depth = max(self.SLAVE_MARKET_DEPTH_FLOOR,
                    self.SLAVE_MARKET_DEPTH_SCALE * self.pop_scale ** self.SLAVE_MARKET_DEPTH_POP_EXPONENT)
        # Integrate the rising price ACROSS the purchase instead of applying
        # one end-price surcharge to the whole block, so grouping does not
        # change the per-head cost: the nth head costs what the nth head
        # costs however you group the purchase into calls.
        already = getattr(self.household, "market_pressure", 0.0)
        people_count = float(n_people)
        exponent = self.SLAVE_PRICE_CONGESTION_EXPONENT
        integral = (((already + people_count) ** exponent) - (already ** exponent)) / (exponent * (depth ** (exponent - 1.0)))
        return self.SLAVE_BASE_PRICE_DENARII * (people_count + integral) * self.price_index

    def buy_slaves(self, n_people):
        """The option the model refuses to hide, and refuses to make costless.

        Roman labour is cheap because much of it is coerced, and any honest model
        of a Roman enterprise has to let you do this. It is available, it works,
        it is counted separately, and manumission is modelled as strictly better
        on the numbers as well as on every other ground: a freedman is paid, is
        literate, stays, and transmits what he knows.

        Three invariants this function and manumit() must keep together:

        A person's capability rises exactly once. buy_slaves adds 0.55
        artisans per person; manumission does not clone anybody, it makes
        the same person work properly, a rise from 0.55 to 1.0 - so
        manumit() adds 0.45, not another 0.55.

        Price rises with the size of the purchase against the local
        market's depth (see slave_quote), so no purchase clears at flat
        list price however many people it is for.

        People arrive untrained and become useful only over a training
        lag, so buying and freeing someone is never faster or cheaper than
        honestly training them free through freedman_staff (900 founder
        hours, two years) would be.
        """
        if n_people <= 0:
            return 0
        # THE SAME ROOM `hire` ENFORCES: a person you own needs feeding,
        # housing and oversight exactly as much as a person you pay, more
        # so, so buy_slaves must respect the same household capacity cap as
        # hire rather than bypassing it under a different verb.
        room = self.household_room()
        if n_people > room:
            self.household._last_buy_refusal = (
                "you can supervise, house and teach %.2f more people, not %g - "
                "and a person you own needs feeding and housing exactly as much "
                "as one you pay. %s"
                % (max(0.0, room), n_people, self._staff_advice("artisans")))
            return 0
        # A town's slave market has a depth. Buying beyond it bids the price up.
        price = self.slave_quote(n_people)
        if price > self.household.capital:
            return 0
        self.household.capital -= price
        self.household.slaves += n_people
        self.household.market_pressure = getattr(self.household, "market_pressure", 0.0) + n_people
        # Untrained on arrival. They become productive through self.household.training.
        self.household.training.append([n_people * self.WORKER_EQUIVALENT_UNTRAINED, self.year + self.TRAINING_YEARS])
        return n_people

    WORKER_EQUIVALENT_UNTRAINED = declare(
        "WORKER_EQUIVALENT_UNTRAINED", 0.55, kind="temporary_heuristic",
        unit="fraction of a full worker's artisan capacity", source=None,
        confidence="D",
        why="What fraction of a full worker a person newly bought is "
            "assumed to represent, entered into the training queue and "
            "matured over TRAINING_YEARS. Not a measured productivity "
            "ratio; picked so the training lag is real (see buy_slaves' "
            "own docstring on the exploit this closed) without being all "
            "or nothing.")
    MANUMISSION_ARTISAN_UPLIFT = declare(
        "MANUMISSION_ARTISAN_UPLIFT", 0.45, kind="temporary_heuristic",
        unit="fraction of a full worker's artisan capacity", source=None,
        confidence="D",
        why="What manumission adds to an already-TRAINED person's artisan "
            "value: the same person working properly rather than under "
            "coercion, a rise from WORKER_EQUIVALENT_UNTRAINED (0.55) to a "
            "full worker (1.0), so it adds the difference, 0.45 - not "
            "another whole worker. See buy_slaves' own docstring for the "
            "double-counting bug this figure fixed.")
    MANUMISSION_REPUTATION_GAIN_PER_PERSON = declare(
        "MANUMISSION_REPUTATION_GAIN_PER_PERSON", 0.4, kind="temporary_heuristic",
        unit="reputation points per person freed, before saturation",
        source=None, confidence="D",
        why="How much standing freeing one person is worth before the "
            "saturation term below discounts it. Tuned game balance, not "
            "a measured social reward for manumission in any specific "
            "period.")
    MANUMISSION_REPUTATION_SATURATION_SCALE = declare(
        "MANUMISSION_REPUTATION_SATURATION_SCALE", 25.0, kind="temporary_heuristic",
        unit="people manumitted, for the saturation denominator",
        source=None, confidence="D",
        why="How fast repeated manumission stops being newsworthy: 'the "
            "first freedmen you make are a statement; the four hundredth "
            "is a payroll'. The saturating SHAPE is a real claim about "
            "admiration; the scale of it is tuned, not measured.")
    MANUMISSION_REPUTATION_GAIN_CAP = declare(
        "MANUMISSION_REPUTATION_GAIN_CAP", 6.0, kind="temporary_heuristic",
        unit="reputation points, per manumit() call", source=None,
        confidence="D",
        why="The most a single manumission act can raise reputation by, "
            "however many people it frees at once - uncapped, this was a "
            "reputation pump that beat taking a patron. Tuned ceiling, not "
            "measured.")

    def manumit(self, n_people):
        n_people = min(n_people, self.household.slaves)
        if not n_people:
            return 0
        self.household.slaves -= n_people
        self.household.freedmen += n_people
        self.household.manumitted_total += n_people
        # The SAME person, working properly: 0.55 to 1.0, not another whole
        # worker.
        #
        # But only for people who are actually TRAINED: freeing an untrained
        # person upgrades what they will be worth WHEN they mature, it does
        # not skip the maturing, so the uplift below must not be paid on a
        # share of n_people that is still sitting in the training queue.
        # The training queue also carries taught-trade rows (which have a
        # trade name in them and no artisan capacity), so read column 0 by
        # index rather than unpacking a row whose width is not fixed.
        in_training = sum(row[0] for row in self.household.training)
        untrained = min(n_people, int(in_training / self.WORKER_EQUIVALENT_UNTRAINED + 0.5))
        trained_freed = max(0, n_people - untrained)
        self.household.artisans += trained_freed * self.MANUMISSION_ARTISAN_UPLIFT
        if untrained:
            share = untrained / max(1.0, in_training / self.WORKER_EQUIVALENT_UNTRAINED)
            for row in self.household.training:
                row[0] *= 1.0 + self.MANUMISSION_ARTISAN_UPLIFT / self.WORKER_EQUIVALENT_UNTRAINED * min(1.0, share)
        # Manumission is publicly admired, and admiration saturates: the
        # first freedmen you make are a statement, the four hundredth is a
        # payroll. The gain is capped so a high-volume series of small
        # manumissions cannot out-earn taking a patron.
        gain = (self.MANUMISSION_REPUTATION_GAIN_PER_PERSON * n_people
                / (1.0 + self.household.manumitted_total / self.MANUMISSION_REPUTATION_SATURATION_SCALE))
        self.household.reputation += min(gain, self.MANUMISSION_REPUTATION_GAIN_CAP)
        return n_people