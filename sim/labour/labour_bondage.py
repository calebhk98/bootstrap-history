"""Buying people and freeing them.

buy_slaves and manumit are the two sides of the model CLAUDE.md 3.1 asks for rather than hides: Roman labour is
cheap because much of it is coerced, and manumission is modelled as strictly better on the numbers as well as
on every other ground. slave_quote is the market depth and rising-price curve buy_slaves prices against."""
from sim.constants import declare
from sim.polity.api import GainReputation
from .buy_cap import over_room_refusal
from sim.ledger.api import PayEdge


class Bondage:
    def __init__(self, world, advice, capacity, pools, schedule):
        self._world = world
        self.advice = advice
        self.capacity = capacity
        self.pools = pools
        self.schedule = schedule

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

    SLAVE_BASE_PRICE_LABOUR_HOURS = declare(
        "SLAVE_BASE_PRICE_LABOUR_HOURS", 6050.0, kind="hardcoded_outcome",
        unit="labour hours, at price_index=1 and zero market pressure",
        source=None, confidence="D",
        why="Amount of labour, not of coin: it was a book-denarii figure and now follows what labour costs. "
            "The list price of one person before any congestion surcharge "
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

    @property
    def SLAVE_BASE_PRICE(self):
        """The base price in this civilisation's coin: the declared hours times what one unskilled hour is worth."""
        return self.SLAVE_BASE_PRICE_LABOUR_HOURS * self.schedule.money_per_labour_hour()

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
                    self.SLAVE_MARKET_DEPTH_SCALE * self._world.people.pop_scale ** self.SLAVE_MARKET_DEPTH_POP_EXPONENT)
        # Integrate the rising price ACROSS the purchase instead of applying
        # one end-price surcharge to the whole block, so grouping does not
        # change the per-head cost: the nth head costs what the nth head
        # costs however you group the purchase into calls.
        already = self._world.workforce.market_pressure
        people_count = float(n_people)
        exponent = self.SLAVE_PRICE_CONGESTION_EXPONENT
        integral = (((already + people_count) ** exponent) - (already ** exponent)) / (exponent * (depth ** (exponent - 1.0)))
        return self.SLAVE_BASE_PRICE * (people_count + integral) * self._world.finance.price_index

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
        room = self.capacity.household_room()
        refusal = over_room_refusal(n_people, room, lambda: self.advice.staff_advice("artisans"))
        if refusal:
            self._world.commands.note_buy_refusal(refusal)
            return 0
        # A town's slave market has a depth. Buying beyond it bids the price up.
        price = self.slave_quote(n_people)
        workforce = self._world.workforce
        if not self._world.finance.can_pay(price):
            self._world.commands.note_buy_refusal(self._world.finance.refusal_text("%d slaves" % n_people, price))
            return 0
        self._world.send(PayEdge(self._world.EDGE_SLAVE_TRADERS, price, "slaves bought"))
        workforce.slaves += n_people
        workforce.market_pressure = workforce.market_pressure + n_people
        # Untrained on arrival. They become productive through the workforce's training queue.
        workforce.training.append([n_people * self.pools.WORKER_EQUIVALENT_UNTRAINED, self._world.year + self.TRAINING_YEARS])
        return n_people

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
        workforce = self._world.workforce
        n_people = min(n_people, workforce.slaves)
        if not n_people:
            return 0
        workforce.slaves -= n_people
        workforce.freedmen += n_people
        workforce.manumitted_total += n_people
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
        in_training = sum(row[0] for row in workforce.training)
        untrained = min(n_people, int(in_training / self.pools.WORKER_EQUIVALENT_UNTRAINED + 0.5))
        trained_freed = max(0, n_people - untrained)
        workforce.artisans += trained_freed * self.MANUMISSION_ARTISAN_UPLIFT
        if untrained:
            share = untrained / max(1.0, in_training / self.pools.WORKER_EQUIVALENT_UNTRAINED)
            for row in workforce.training:
                row[0] *= 1.0 + self.MANUMISSION_ARTISAN_UPLIFT / self.pools.WORKER_EQUIVALENT_UNTRAINED * min(1.0, share)
        # Manumission is publicly admired, and admiration saturates: the
        # first freedmen you make are a statement, the four hundredth is a
        # payroll. The gain is capped so a high-volume series of small
        # manumissions cannot out-earn taking a patron.
        gain = (self.MANUMISSION_REPUTATION_GAIN_PER_PERSON * n_people
                / (1.0 + workforce.manumitted_total / self.MANUMISSION_REPUTATION_SATURATION_SCALE))
        self._world.send(GainReputation(min(gain, self.MANUMISSION_REPUTATION_GAIN_CAP)))
        return n_people
