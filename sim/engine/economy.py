"""Money, materials, and the works that consume both.

These are methods of Sim; they are a mixin only so that they can live in a
file of their own.
"""
import math
from constants import declare

from .economy_goods import GoodsMixin
from .economy_materials import MaterialSupplyMixin
from .economy_electricity import ElectricityMixin
from .economy_freight import FreightMixin
from .economy_mining import MiningMixin
from .economy_credit import CreditMixin
from .economy_production import ProductionMixin


class _InvalidatingSet(set):
    """A set that calls `on_change` after every mutation, with no exceptions.

    Backs `Sim.operating` (see the `operating` property on `EconomyMixin`
    below) so that a cache keyed off operating's exact membership -
    `capability_factor()`'s - cannot go stale, no matter which of the nine
    call sites across core.py/projects.py/economy.py/society.py adds to or
    discards from it, and without asking any of them to remember a second
    line. The `done`/`_done_changed()` convention this project already has
    relies on every one of ITS mutation sites remembering to call
    `_done_changed()` by hand; that is a real convention and it has held,
    but a second one just like it - one more rule written down at every call
    site instead of enforced at one - is exactly the shape that has already
    produced three drifted-apart bugs elsewhere in this codebase today. This
    set makes the equivalent mistake impossible for `operating` specifically:
    there is only one `.add`, only one `.discard`, and they are these. It is
    the same reasoning that made `revealed` (engine/fog.py) a property rather
    than a plain attribute, extended to a set instead of a ratchet.

    Every mutating method a plain `set` exposes is overridden so that
    swapping this in for `set()` changes nothing observable except that
    `on_change` now fires. Non-mutating methods (`copy`, `union`, membership
    tests, iteration, `len`) are inherited unchanged.
    """

    def __init__(self, iterable=(), on_change=None):
        set.__init__(self, iterable)
        self._on_change = on_change

    def _fire(self):
        if self._on_change is not None:
            self._on_change()

    def add(self, item):
        if item not in self:
            set.add(self, item)
            self._fire()

    def discard(self, item):
        if item in self:
            set.discard(self, item)
            self._fire()

    def remove(self, item):
        set.remove(self, item)      # raises KeyError, same as a plain set
        self._fire()

    def pop(self):
        item = set.pop(self)
        self._fire()
        return item

    def clear(self):
        if self:
            set.clear(self)
            self._fire()

    def update(self, *others):
        before = len(self)
        set.update(self, *others)
        if len(self) != before:
            self._fire()

    def difference_update(self, *others):
        before = len(self)
        set.difference_update(self, *others)
        if len(self) != before:
            self._fire()

    def intersection_update(self, *others):
        before = len(self)
        set.intersection_update(self, *others)
        if len(self) != before:
            self._fire()

    def symmetric_difference_update(self, other):
        before = frozenset(self)
        set.symmetric_difference_update(self, other)
        if frozenset(self) != before:
            self._fire()

    def __ior__(self, other):
        before = len(self)
        result = set.__ior__(self, other)
        if len(self) != before:
            self._fire()
        return result

    def __iand__(self, other):
        before = len(self)
        result = set.__iand__(self, other)
        if len(self) != before:
            self._fire()
        return result

    def __isub__(self, other):
        before = len(self)
        result = set.__isub__(self, other)
        if len(self) != before:
            self._fire()
        return result

    def __ixor__(self, other):
        before = frozenset(self)
        result = set.__ixor__(self, other)
        if frozenset(self) != before:
            self._fire()
        return result


class _InvalidatingDict(dict):
    """A dictionary that calls `on_change` after every mutation.

    Follows the exact pattern of _InvalidatingSet above. Used for
    `self.household.active` and `self.household.employees` so that
    derived-state caches keyed on active project membership or workforce
    changes are reliably invalidated whenever keys or values mutate,
    without requiring scattered callers across the engine to remember
    manual cache resets.
    """

    def __init__(self, *args, on_change=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._on_change = on_change

    def _fire(self):
        if self._on_change is not None:
            self._on_change()

    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        self._fire()

    def __delitem__(self, key):
        super().__delitem__(key)
        self._fire()

    def pop(self, *args, **kwargs):
        result = super().pop(*args, **kwargs)
        self._fire()
        return result

    def popitem(self):
        result = super().popitem()
        self._fire()
        return result

    def clear(self):
        if self:
            super().clear()
            self._fire()

    def update(self, *args, **kwargs):
        super().update(*args, **kwargs)
        self._fire()

    def setdefault(self, key, default=None):
        if key not in self:
            result = super().setdefault(key, default)
            self._fire()
            return result
        return super().setdefault(key, default)



# ---- REPUTATION/STANDING: a scoreboard, not yet a social mechanism --------
#
# None of the numbers below are measured facts about anything; they are a
# hand-tuned scoring function for "how well known and well regarded are you",
# invented because no lower-level model of patronage, gossip or audience
# reach exists yet. A real mechanism would derive standing from who actually
# knows what you have done and how far that spreads through a real social
# network (patrons, students, guild membership, literacy and travel time all
# bound how far reputation can propagate) - no such mechanism exists
# anywhere in this project yet, including ENDOGENOUS_COSTS_AND_DOMAINS.md,
# whose Part 2 covers production-cost pricing, not social propagation.
# Until a real one exists, every constant here is temporary_heuristic.
STANDING_BASE_FLOOR = declare(
    "STANDING_BASE_FLOOR", 0.5, kind="temporary_heuristic",
    unit="reputation points (dimensionless)", source=None, confidence="D",
    why="The reputation floor of someone who has founded and finished "
        "nothing yet - not zero, because arriving with a plan and a "
        "household is itself a small, visible fact. A real mechanism would "
        "derive this from how a stranger is actually perceived on arrival "
        "in a given society, not assign a flat starting score.")
STANDING_PER_SQRT_EARNED = declare(
    "STANDING_PER_SQRT_EARNED", 0.55, kind="temporary_heuristic",
    unit="reputation points per sqrt(finished works)", source=None,
    confidence="D",
    why="How much each additional finished, ungranted work adds to standing, "
        "on a sqrt curve so the first few matter far more than the "
        "hundredth. The sqrt SHAPE is a real claim (reputation saturates, it "
        "does not accumulate linearly); the 0.55 coefficient is simply "
        "tuned until the early game felt right. A real mechanism needs a "
        "model of who hears about a given work and how impressed they are.")
STANDING_CORPUS_WRITTEN = declare(
    "STANDING_CORPUS_WRITTEN", 3.0, kind="temporary_heuristic",
    unit="reputation points", source=None, confidence="D",
    why="Flat bonus for having written a corpus of your own knowledge down "
        "at all, before it has spread anywhere. Invented game balance; a "
        "real figure would follow from how rare and how legible written "
        "work is in this society.")
STANDING_CORPUS_DISPERSED = declare(
    "STANDING_CORPUS_DISPERSED", 6.0, kind="temporary_heuristic",
    unit="reputation points", source=None, confidence="D",
    why="Further bonus once that corpus is actually copied into other "
        "libraries - twice the written-only bonus because now other people, "
        "not just you, hold the proof of what you know. Tuned, not derived.")
STANDING_SCHOOL_FOUNDED_PER_SQRT_UNIT = declare(
    "STANDING_SCHOOL_FOUNDED_PER_SQRT_UNIT", 4.0, kind="temporary_heuristic",
    unit="reputation points per sqrt(school units)", source=None,
    confidence="D",
    why="Founding a school buys standing mostly by having founded one at "
        "all, not by its size - sqrt so a third schoolhouse does not make "
        "you three times as well known as the first. The curve shape is "
        "reasoned; the coefficient is tuned until playtests felt right.")
STANDING_ACADEMY_NETWORK_PER_SQRT_UNIT = declare(
    "STANDING_ACADEMY_NETWORK_PER_SQRT_UNIT", 10.0,
    kind="temporary_heuristic", unit="reputation points per sqrt(network units)",
    source=None, confidence="D",
    why="Same sqrt-saturating shape as the school bonus, larger because an "
        "academy network is a bigger, later institution. No independent "
        "source; picked to feel roughly proportionate to the school figure.")
STANDING_PATRON_SENATORIAL = declare(
    "STANDING_PATRON_SENATORIAL", 3.0, kind="temporary_heuristic",
    unit="reputation points", source=None, confidence="D",
    why="Flat standing from having a senatorial-tier patron's name attached "
        "to you. A real figure would follow from how visible that patron's "
        "own standing is in this specific society, not a flat constant "
        "reused across every civilisation in the game.")
STANDING_PATRON_IMPERIAL = declare(
    "STANDING_PATRON_IMPERIAL", 8.0, kind="temporary_heuristic",
    unit="reputation points", source=None, confidence="D",
    why="As STANDING_PATRON_SENATORIAL, for the imperial tier - larger "
        "because that patron is more visible, tuned rather than derived.")
STANDING_IDENTITY_COVER = declare(
    "STANDING_IDENTITY_COVER", 1.0, kind="temporary_heuristic",
    unit="reputation points", source=None, confidence="D",
    why="Small standing bonus for having a respectable cover identity at "
        "all. Invented game balance, smallest of this group because a cover "
        "identity is a starting requirement, not an achievement.")
STANDING_SCANDAL_PENALTY_PER_POINT = declare(
    "STANDING_SCANDAL_PENALTY_PER_POINT", 0.5, kind="temporary_heuristic",
    unit="reputation points lost per point of household.scandal",
    source=None, confidence="D",
    why="How much a point of scandal erodes standing, one-for-one at half "
        "weight. Scandal itself has no source model (who spreads it, how "
        "fast, whether it fades) so this coefficient is a placeholder for "
        "that whole missing mechanism, not a measured rate of anything.")
REPUTATION_EASE_SCALE = declare(
    "REPUTATION_EASE_SCALE", 120.0, kind="temporary_heuristic",
    unit="reputation points per unit of ease (dimensionless denominator)",
    source=None, confidence="D",
    why="How much reputation it takes to make everything else roughly "
        "twice as easy (rep_factor = 1 + reputation/120). No independent "
        "source; a real figure needs a model of what reputation actually "
        "buys (lower prices, faster favours, less friction) instead of one "
        "shared multiplier standing in for all of them at once.")
ECONOMY_INDEX_PER_DIFFUSED_NODE = declare(
    "ECONOMY_INDEX_PER_DIFFUSED_NODE", 0.055,
    kind="temporary_heuristic", unit="fraction of output per diffused technology",
    source=None, confidence="D",
    why="How much each technology that has spread beyond your own workshop "
        "(corpus_dispersed) raises output economy-wide, standing in for the "
        "real mechanism - diffusion of a specific technology through a "
        "specific population over time - that nothing in this project "
        "computes yet; ENDOGENOUS_COSTS_AND_DOMAINS.md Part 2 gets closer "
        "to a real production-cost price than this flat index does, but "
        "does not model diffusion speed either.")
ECONOMY_INDEX_PER_LOCKED_NODE = declare(
    "ECONOMY_INDEX_PER_LOCKED_NODE", 0.030,
    kind="temporary_heuristic", unit="fraction of output per undispersed technology",
    source=None, confidence="D",
    why="Same mechanism as ECONOMY_INDEX_PER_DIFFUSED_NODE, at roughly "
        "half strength, for a technology that exists only in your own "
        "workshop and has not been copied out - knowledge locked in one "
        "place should spread its economic benefit more slowly, not not at "
        "all. Both figures are tuned, not measured.")


class EconomyMixin(GoodsMixin, MaterialSupplyMixin, ElectricityMixin, FreightMixin,
                    MiningMixin, CreditMixin, ProductionMixin):
    """Composition point for the economy sub-mixins, plus what is left over.

    EconomyMixin's methods are grouped by subject across sibling modules
    (ore and land in economy_mining.py, debt and affordability in
    economy_credit.py, revenue and workshops in economy_production.py,
    goods-producing concerns in economy_goods.py, raw material supply in
    economy_materials.py, electricity as a physical quantity in
    economy_electricity.py, freight in economy_freight.py - see each
    module's own docstring for the detailed grouping and evidence) as
    their own mixin classes, which EconomyMixin composes back into one
    name so core.py's `class Sim(EconomyMixin, ...)` does not have to
    know about any of them individually.

    Methods are grouped by what actually calls them, not by where they
    happen to sit textually: _cached_material_demand() and
    _cached_demand_by_tag() live in economy_freight.py, not
    economy_electricity.py, because every real caller of either is in
    economy_freight.py - see that file's own docstring for the fuller
    account.

    CLASS-LEVEL CACHES, NAMED DELIBERATELY. Three methods in
    economy_materials.py and one in economy_freight.py cache their
    answer on their own bare class object rather than on self, because
    what they cache (a CommodityLedger, a material-to-commodity-id map,
    prices.json's own figures, and the ox-cart-and-dirt-track physical
    inputs freight pricing reuses) does not differ between one Sim
    instance and the next in the same process. TRAP: that class-object
    reference at each cache site MUST match whatever class actually
    holds the method - a stale identifier fails silently, invisible to
    import and to `validate`, surfacing only when a command that reads a
    material price first runs. See each file's own CLASS-LEVEL CACHE
    note for which methods, which cache names, and why each one points
    at the class actually holding it.

    What is defined directly on EconomyMixin, below, is what did not
    fit cleanly into any one of those subjects: standing/reputation
    (standing_floor/rep_factor/economy_index), the generic cost of a
    project (cost_money_factor/opposition_factor/project_cost), the
    `done`/`operating` set-identity and ordering plumbing every
    sub-mixin reads through self
    (done_in_order/_done_changed/_operating_changed/_reset_operating,
    alongside _InvalidatingSet above, which the last two use), and a
    handful of constants (PRACTICE_SHARE, DEFAULT_ANNUAL_WAGE_FALLBACK,
    MINE_CAPEX_PER_T_YR and its per-material entries, FOREST_COST_PER_HA)
    that are genuinely read from more than one sub-mixin, so moving any
    one of them into a single sub-mixin would leave the others reaching
    across module boundaries for a constant that isn't theirs - they
    stay here, on the composition point all of them inherit from,
    instead.
    """

    def standing_floor(self):
        """The reputation you keep for what you have built, whatever else happens.

        Novelty fades. A corpus in three libraries, a school with students and a
        senator who will receive you do not.
        """
        earned = len(self.household.done) - len(self.household.granted)
        standing = STANDING_BASE_FLOOR + STANDING_PER_SQRT_EARNED * math.sqrt(max(0, earned))
        if self.running("corpus_written"):     standing += STANDING_CORPUS_WRITTEN
        if self.running("corpus_dispersed"):   standing += STANDING_CORPUS_DISPERSED
        # SQRT, NOT LINEAR. A third schoolhouse does not make you three times
        # as well known as the first one did - the standing a school buys is
        # mostly in having founded one at all, not in its size - so further
        # units add less each time, the same curve `earned` above already
        # uses for the same reason.
        if self.running("school_founded"):
            standing += STANDING_SCHOOL_FOUNDED_PER_SQRT_UNIT * self.institution_units("school_founded") ** 0.5
        if self.running("academy_network"):
            standing += STANDING_ACADEMY_NETWORK_PER_SQRT_UNIT * self.institution_units("academy_network") ** 0.5
        if self.running("patron_senatorial"):  standing += STANDING_PATRON_SENATORIAL
        if self.running("patron_imperial"):    standing += STANDING_PATRON_IMPERIAL
        if self.running("identity_cover"):     standing += STANDING_IDENTITY_COVER
        # Scandal is the one thing that eats into standing rather than sitting
        # alongside it: being notorious is not the same as being unknown.
        return max(0.0, standing - STANDING_SCANDAL_PENALTY_PER_POINT * self.household.scandal)

    def rep_factor(self):
        """How much easier reputation makes everything. 1.0 at zero reputation."""
        return 1.0 + self.household.reputation / REPUTATION_EASE_SCALE

    def economy_index(self):
        """Diffused technology enriches the whole Empire, not only your workshop.

        Britain's industrialisation paid for itself. So does yours: each heavy
        technology that spreads raises output everywhere, which raises what the
        State and the market can pay you. Without this term the model says an
        industrial revolution is unaffordable, which is false, and the reason it
        is false is that the revolution funds itself.
        """
        diffused = len(self.household.done - self.household.granted)
        index = 1.0 + ECONOMY_INDEX_PER_DIFFUSED_NODE * diffused
        if not self.running("corpus_dispersed"):
            index = 1.0 + ECONOMY_INDEX_PER_LOCKED_NODE * diffused      # knowledge locked in one workshop spreads slowly
        return index

    def cost_money_factor(self):
        """What a denarius of QUOTED cost means, for spending purposes.

        This exists because money_real was being multiplied into every price,
        and money_real FALLS as the currency is debased. So the worse the money
        got, the cheaper everything became: a naive tester found a pawnshop
        quoted at 5 denarii in 278 AD that had cost 1,025 when they built one in
        160, and correctly said debasement should push nominal prices UP, not
        collapse them by two orders of magnitude. They guessed the cause exactly:
        a multiplier tending to zero being multiplied in rather than divided.

        The model is in REAL terms. Debasement destroys the value of CASH, which
        is already handled by taking a haircut off capital when it fires. Real
        prices do not fall, so nothing here tracks money_real; it survives only
        as something to report. Applying both would have been a double count in
        opposite directions.
        """
        return float(self.price_index)

    OPPOSITION_COST_PER_UNIT = declare(
        "OPPOSITION_COST_PER_UNIT", 0.25, kind="temporary_heuristic",
        unit="fraction of cost added per unit of state opposition",
        source=None, confidence="D",
        why="How much bribes, delay and working through a front man add to "
            "a project's cost per unit of state_interest() opposition. "
            "state_interest() itself has no independent calibration against "
            "attested bribery or delay costs, so this conversion rate is "
            "tuned to feel like a real friction, not measured from one.")

    def opposition_factor(self, node_id):
        """Opposed work costs more: bribes, delay, a provincial site, a front man."""
        return 1.0 + self.OPPOSITION_COST_PER_UNIT * max(
            0.0, -self.state_interest(self.nodes[node_id]))

    def project_cost(self, node_id):
        """What this project will actually cost in money, all factors applied.

        This is the number `why` quotes and the number the project must have
        actually PAID before it can complete. A project must not complete on
        hours and calendar alone while step() charges only what you can
        afford each year, clamped at your balance: that would let the
        unpaid remainder of the true cost be forgiven outright, leaving
        money decorative and only hours real.
        """
        node = self.nodes[node_id]
        return (node["_total_cost"] * self.cost_money_factor()
                * self.opposition_factor(node_id)
                * self.civ_cost_factor(node_id) * self.material_cost_factor(node_id)
                * self.material_market_factor(node_id))

    def _done_changed(self):
        """Call after anything adds to or removes from self.household.done.

        Also invalidates capability_factor()'s cache: that walk filters
        done_in_order() by self.household.granted too, and every site that adds to
        self.household.granted does so in the same breath as adding to self.household.done (see
        the comments on capability_factor), so no separate granted-changed
        signal exists or is needed.
        """
        self.household._done_seq = None
        self.household._cap_factor = None
        self.household._done_ver = getattr(self.household, "_done_ver", 0) + 1

    def _operating_changed(self):
        """Call after anything adds to or removes from self.household.operating.

        The `_InvalidatingSet` self.household.operating is built from (see that
        class's comment, just above EconomyMixin) calls this on every
        mutation automatically - every `.add`/`.discard`/`.update`/... from
        any of the nine-odd call sites across core.py/projects.py/
        economy.py/society.py, and any future one, with nothing for any of
        them to remember. See capability_factor(), its only reader so far.

        A property (`self.household.operating` intercepting every READ, the way
        `revealed` in engine/fog.py intercepts every WRITE) was tried first
        and measured worse, not better: self.household.operating is read in the
        hottest loop in the engine - `_goods_category_state` and
        `goods_market_factor` alone read it roughly sixteen million times
        in the 300-year profile this fix was measured against - so a
        property's per-access overhead, paid on every one of those reads to
        protect a few thousand writes, cost far more than capability_factor
        saved; a 300-year profiled run got SLOWER (22.1s -> 27.5s). An
        `_InvalidatingSet` intercepts only mutation, which is what actually
        needs intercepting, at none of that cost: plain attribute reads
        (`in`, `for`, `sorted(...)`, truthiness) are exactly as fast as a
        plain set, unmeasurably so, because they are a plain set's own
        C-level methods, inherited unchanged.

        The gap a property would have closed is whole-object replacement -
        `s.operating = X`, which only two places in this codebase do: a
        fresh Sim's own __init__ (core.py), where there is nothing yet to
        invalidate, and load_state's generic `setattr` loop (protocol.py),
        which is NOT always acting on a freshly-constructed Sim - `load`
        issued mid-session through the agent/play JSON protocol loads into
        the SAME long-lived object a player goes on playing in, and every
        open/close/mothball after that load mutates .operating directly.
        Left alone, that setattr would silently downgrade self.household.operating to
        a plain, non-invalidating set for the rest of that process's life.
        load_state calls _reset_operating() (below) once, right after its
        generic loop, to close that one specific gap explicitly instead of
        taxing sixteen million reads to close a gap with exactly one door.

        ALSO bumps `_operating_ver`, a plain monotonic counter with the same
        reach as this hook (every one of the same nine-odd call sites, and
        no others - it is set here and nowhere else). `_goods_category_state`
        and `_revenue_upkeep_candidates` below both key a cache on this
        counter instead of re-deriving their own answer from `operating`'s
        contents on every call, for the same reason `_cap_factor` already
        does: those two are read from the hottest loops in the engine (see
        _goods_category_state's own comment - 75,748 calls in a 150-year
        profile, more than any other function in this file) and their
        actual inputs (self.year plus this set) change far less often than
        they are read. It carries the exact same one known gap this
        docstring already describes for `_cap_factor` - a caller that
        replaces `self.household.operating` with a plain `set()` rather than going
        through `_reset_operating()` (test_regressions.py's ROUND 8 close-
        order test does this once, deliberately, to build a fixture) stops
        this counter advancing for the rest of that object's life, same as
        it already stops `_cap_factor` invalidating. Not a new risk this
        change introduces: the existing cache already lives with it, on the
        same object, for the same reason, and no reference run in
        perf_fingerprint.py's suite ever does this to a live Sim - only that
        one hand-built test fixture does, and it never asks for a goods
        price, an income factor, or a revenue/upkeep total afterward.
        """
        self.household._cap_factor = None
        self.household._operating_ver = getattr(self.household, "_operating_ver", 0) + 1

    def _reset_operating(self):
        """Re-wrap self.household.operating in a fresh `_InvalidatingSet` and
        invalidate once. See the long comment on _operating_changed() for
        why this exists and why it is not a property instead: this is the
        one call site (load_state, protocol.py) that replaces
        self.household.operating wholesale on a Sim that may go on being mutated
        afterward in the same process."""
        self.household.operating = _InvalidatingSet(self.household.operating, on_change=self._operating_changed)
        self._operating_changed()

    def _active_changed(self):
        """Call after anything adds to, removes from, or updates self.household.active."""
        self.household._active_ver = getattr(self.household, "_active_ver", 0) + 1

    def _reset_active(self):
        """Re-wrap self.household.active in a fresh `_InvalidatingDict` and invalidate once."""
        self.household.active = _InvalidatingDict(self.household.active, on_change=self._active_changed)
        self._active_changed()

    def _workforce_changed(self):
        """Call after anything mutates self.household.employees or workforce counts."""
        self.household._workforce_ver = getattr(self.household, "_workforce_ver", 0) + 1

    def _reset_workforce(self):
        """Re-wrap self.household.employees in a fresh `_InvalidatingDict` and invalidate once."""
        self.household.employees = _InvalidatingDict(self.household.employees, on_change=self._workforce_changed)
        self._workforce_changed()

    def done_in_order(self):
        """Everything you have finished, in a FIXED order.

        `self.household.done` is a set of strings, and a set of strings iterates in an
        order that depends on PYTHONHASHSEED, which Python randomises per
        process. Three places summed floats over it - revenue, upkeep and
        material demand - and floating point addition is not associative, so
        the totals differed in their last bits between one process and the
        next. Over five hundred years those last bits decide which side of a
        threshold you land on, and the same --seed gave two different answers
        on alternate invocations. Three other sites were fixed for this before
        by sorting; these were missed because nothing here touches the RNG, and
        the arithmetic looked innocent.

        `self.order` is a list, and a list is a list.
        """
        # CACHED, because this is O(nodes) and revenue() calls it. Uncached it
        # was 2.2 seconds of a 3.5 second `can_start` once something else began
        # calling revenue() thousands of times: correct, and quadratic. The
        # cache is invalidated by hand at the twelve places that add to or
        # remove from `done`, rather than by a length check, because a year that
        # abandons one work and completes another leaves the length identical
        # and the contents different.
        seq = getattr(self.household, "_done_seq", None)
        if seq is None:
            seq = self.household._done_seq = [node_id for node_id in self.order if node_id in self.household.done]
        return seq

    # WHAT ONE PERSON'S PRACTICE IS WORTH, against what the tree quotes for the
    # trade as a going concern. A physician working alone, out of a rented room,
    # with no partners and no staff, does not take what an organised practice
    # takes; a third is the figure the whole opening is calibrated around.
    #
    # This number was already in the game and was reached by accident. A granted
    # skill has no entry in done_year, so its "age" was zero every year for ever
    # and the revenue ramp - meant to say a NEW business takes three years to
    # find its custom - pinned it at the first step of three and never moved it.
    # The arithmetic came out right and the meaning came out wrong: a break
    # tester read `why` at 500 a year, saw 166.7 in the ledger, and could find
    # nothing anywhere that explained the difference or said whether it would
    # ever close. It will not. It is not a ramp; it is the size of your practice.
    PRACTICE_SHARE = declare(
        "PRACTICE_SHARE", 1.0 / 3.0, kind="temporary_heuristic",
        unit="fraction of the tree's quoted trade revenue", source=None,
        confidence="D",
        why="What a lone practitioner working out of a rented room, with "
            "no partners and no staff, actually takes home against what "
            "the tree quotes for the trade as an organised going concern. "
            "Per the comment above, this number was reached by ACCIDENT "
            "(a revenue-ramp bug that happened to land on a defensible "
            "fraction) and then kept because the whole opening of the game "
            "is now calibrated around it - moving it requires re-tuning "
            "the early game, not just picking a better number.")
    DEFAULT_ANNUAL_WAGE_FALLBACK = declare(
        "DEFAULT_ANNUAL_WAGE_FALLBACK", 375.0, kind="temporary_heuristic",
        unit="denarii/year", source=None, confidence="D",
        why="Stand-in annual wage for a craft trade that ANNUAL_WAGE (see "
            "labour.py, outside this file's scope) has no entry for, so a "
            "missing trade does not crash the workshop-output or "
            "stall-diagnosis wage sums. A round, plausible mid-table wage, "
            "not sourced to any specific trade.")

    # Capital to create one tonne per year of standing extraction capacity, and
    # the recurring cost of actually getting that tonne out. DERIVED, not
    # measured: a Roman coal hewer working a shallow drift wins on the order of
    # a tonne a day, so 250 t/yr a man, and the miner wage of 0.09 den/hr over
    # 2000 hours is 180 den a year, giving roughly 0.7 den per tonne in wages
    # before haulage. Doubling it for haulage, timbering and overseers gives the
    # figures below. Metal ores cost far more per tonne of METAL because of the
    # ore grade and the smelting, and the capital rises with depth and drainage.
    # Gold is here so debasement has an answer: if the money is being ruined
    # by having less silver in it, a man who digs his own metal is not ruined
    # with it. Roman gold (Dacia, Las Medulas) was mined at enormous cost and
    # that is what the capex says.
    MINE_CAPEX_PER_T_YR_COAL = declare(
        "MINE_CAPEX_PER_T_YR_COAL", 9.0, kind="engineering_estimate",
        unit="denarii per tonne/year of capacity sunk",
        source="The base figure this file derives explicitly: a Roman coal hewer working a shallow drift wins on the order of a tonne a day (~250 t/yr/man); at a miner's wage of 0.09 denarii/hour over 2000 hours/year (180 den/yr), that is roughly 0.7 den/tonne in wages before haulage, doubled here for haulage, timbering and overseers.",
        confidence='B', why="Capital to create one tonne per year of standing extraction capacity for this material - see the class comment above for how coal's own figure is derived from Roman wage and productivity evidence (a hewer at ~250 t/yr, a miner's wage of 0.09 den/hr over 2000 hours, doubled for haulage/timbering/overseers) and the other metals scale up from ore grade, smelting and depth/drainage cost, cross-checked against attested Roman workings (Rio Tinto, Dacia, Las Medulas for gold).")
    MINE_CAPEX_PER_T_YR_IRON = declare(
        "MINE_CAPEX_PER_T_YR_IRON", 60.0, kind="hardcoded_outcome",
        unit="denarii per tonne/year of capacity sunk",
        source="Scaled up from coal's derived figure for ore grade and smelting, cross-checked against iron's own book price (the GENERIC_MINE_CAPEX_MULTIPLE comment below notes iron's capex is close to 60x its book price, the same multiple the generic fallback for every other material now uses).",
        confidence='C', why="Capital to create one tonne per year of standing extraction capacity for this material - see the class comment above for how coal's own figure is derived from Roman wage and productivity evidence (a hewer at ~250 t/yr, a miner's wage of 0.09 den/hr over 2000 hours, doubled for haulage/timbering/overseers) and the other metals scale up from ore grade, smelting and depth/drainage cost, cross-checked against attested Roman workings (Rio Tinto, Dacia, Las Medulas for gold).")
    MINE_CAPEX_PER_T_YR_COPPER = declare(
        "MINE_CAPEX_PER_T_YR_COPPER", 240.0, kind="hardcoded_outcome",
        unit="denarii per tonne/year of capacity sunk",
        source="As iron, scaled for copper's own ore grade and smelting; close to 60x copper's own book price.",
        confidence='C', why="Capital to create one tonne per year of standing extraction capacity for this material - see the class comment above for how coal's own figure is derived from Roman wage and productivity evidence (a hewer at ~250 t/yr, a miner's wage of 0.09 den/hr over 2000 hours, doubled for haulage/timbering/overseers) and the other metals scale up from ore grade, smelting and depth/drainage cost, cross-checked against attested Roman workings (Rio Tinto, Dacia, Las Medulas for gold).")
    MINE_CAPEX_PER_T_YR_LEAD = declare(
        "MINE_CAPEX_PER_T_YR_LEAD", 80.0, kind="engineering_estimate",
        unit="denarii per tonne/year of capacity sunk",
        source="As iron, scaled for lead's own ore grade and smelting.",
        confidence='C', why="Capital to create one tonne per year of standing extraction capacity for this material - see the class comment above for how coal's own figure is derived from Roman wage and productivity evidence (a hewer at ~250 t/yr, a miner's wage of 0.09 den/hr over 2000 hours, doubled for haulage/timbering/overseers) and the other metals scale up from ore grade, smelting and depth/drainage cost, cross-checked against attested Roman workings (Rio Tinto, Dacia, Las Medulas for gold).")
    MINE_CAPEX_PER_T_YR_TIN = declare(
        "MINE_CAPEX_PER_T_YR_TIN", 420.0, kind="hardcoded_outcome",
        unit="denarii per tonne/year of capacity sunk",
        source="As iron, scaled for tin's own ore grade and smelting; close to 42x tin's own book price.",
        confidence='C', why="Capital to create one tonne per year of standing extraction capacity for this material - see the class comment above for how coal's own figure is derived from Roman wage and productivity evidence (a hewer at ~250 t/yr, a miner's wage of 0.09 den/hr over 2000 hours, doubled for haulage/timbering/overseers) and the other metals scale up from ore grade, smelting and depth/drainage cost, cross-checked against attested Roman workings (Rio Tinto, Dacia, Las Medulas for gold).")
    MINE_CAPEX_PER_T_YR_SILVER = declare(
        "MINE_CAPEX_PER_T_YR_SILVER", 9000.0, kind="hardcoded_outcome",
        unit="denarii per tonne/year of capacity sunk",
        source="As iron, scaled for silver's much higher ore value and smelting/refining cost; close to 28x silver's own book price.",
        confidence='C', why="Capital to create one tonne per year of standing extraction capacity for this material - see the class comment above for how coal's own figure is derived from Roman wage and productivity evidence (a hewer at ~250 t/yr, a miner's wage of 0.09 den/hr over 2000 hours, doubled for haulage/timbering/overseers) and the other metals scale up from ore grade, smelting and depth/drainage cost, cross-checked against attested Roman workings (Rio Tinto, Dacia, Las Medulas for gold).")
    MINE_CAPEX_PER_T_YR_GOLD = declare(
        "MINE_CAPEX_PER_T_YR_GOLD", 160000.0, kind="hardcoded_outcome",
        unit="denarii per tonne/year of capacity sunk",
        source="Attested Roman gold workings (Dacia, Las Medulas) were mined at enormous cost, reflected here; close to 46x gold's own book price. Included specifically so debasement has an escape valve - a founder who mines their own gold is not ruined by a debased currency the way one holding cash is.",
        confidence='C', why="Capital to create one tonne per year of standing extraction capacity for this material - see the class comment above for how coal's own figure is derived from Roman wage and productivity evidence (a hewer at ~250 t/yr, a miner's wage of 0.09 den/hr over 2000 hours, doubled for haulage/timbering/overseers) and the other metals scale up from ore grade, smelting and depth/drainage cost, cross-checked against attested Roman workings (Rio Tinto, Dacia, Las Medulas for gold).")
    MINE_CAPEX_PER_T_YR = {
        'coal': MINE_CAPEX_PER_T_YR_COAL,
        'iron': MINE_CAPEX_PER_T_YR_IRON,
        'copper': MINE_CAPEX_PER_T_YR_COPPER,
        'lead': MINE_CAPEX_PER_T_YR_LEAD,
        'tin': MINE_CAPEX_PER_T_YR_TIN,
        'silver': MINE_CAPEX_PER_T_YR_SILVER,
        'gold': MINE_CAPEX_PER_T_YR_GOLD,
    }

    # ~1 iugerum of woodland per 0.25 ha. Named so that `quote forest` and the
    # purchase itself cannot drift apart: a player must be able to ask the
    # price of coppice before spending capital on it, not only after.
    FOREST_COST_PER_HA = declare(
        "FOREST_COST_PER_HA", 250.0, kind="temporary_heuristic",
        unit="denarii/hectare", source=None, confidence="D",
        why="Purchase price of a hectare of coppice woodland. No attested "
            "Roman land-price figure backs this; it exists mainly so "
            "`quote forest` and the purchase itself agree on a real price "
            "at all, per the comment above.")
