"""Money, materials, and the works that consume both.

These are methods of Sim; they are a mixin only so that they can live in a
file of their own.
"""
import math
from sim.constants import declare
from . import money_units

from .economy_goods import GoodsMixin
from .economy_materials import MaterialSupplyMixin
from .economy_electricity import ElectricityMixin
from .economy_freight import FreightMixin
from .economy_mining import MiningMixin
from .economy_credit import CreditMixin
from .economy_debt_service import DebtServiceMixin
from .economy_capital_market import CapitalMarketMixin
from .economy_interest_pool import InterestPoolMixin
from .economy_absorption import MarketAbsorptionMixin
from .projects_cost_tail import ProjectCostTailMixin
from .economy_production import ProductionMixin
from .project_materials import ProjectMaterialsMixin
from .view_share import ViewShareMixin


from sim.invalidating import _InvalidatingDict, _InvalidatingSet  # noqa: F401


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


class EconomyMixin(GoodsMixin, MaterialSupplyMixin, ElectricityMixin, FreightMixin,
                    MiningMixin, CreditMixin, DebtServiceMixin, CapitalMarketMixin, InterestPoolMixin, MarketAbsorptionMixin, ProjectCostTailMixin, ProductionMixin, ProjectMaterialsMixin, ViewShareMixin):
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
    the solved price table, and the ox-cart-and-dirt-track physical
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
    (standing_floor/rep_factor), the generic cost of a
    project (cost_money_factor/opposition_factor/project_cost), the
    `done`/`operating` set-identity and ordering plumbing every
    sub-mixin reads through self
    (done_in_order/_done_changed/_operating_changed/_reset_operating,
    alongside _InvalidatingSet above, which the last two use), and a
    handful of constants (FOREST_COST_PER_HA)
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
        projects = self.state.projects
        earned = len(projects.done) - len(projects.granted)
        standing = STANDING_BASE_FLOOR + STANDING_PER_SQRT_EARNED * math.sqrt(max(0, earned))
        # SQRT, NOT LINEAR. A third schoolhouse does not make you three times
        # as well known as the first one did - the standing a school buys is
        # mostly in having founded one at all, not in its size - so further
        # units add less each time, the same curve `earned` above already
        # uses for the same reason.
        standing = self.effect_sum("standing", standing)
        # Scandal is the one thing that eats into standing rather than sitting
        # alongside it: being notorious is not the same as being unknown.
        return max(0.0, standing - STANDING_SCANDAL_PENALTY_PER_POINT * self.state.household.scandal)

    def rep_factor(self):
        """How much easier reputation makes everything. 1.0 at zero reputation."""
        return 1.0 + self.state.household.reputation / REPUTATION_EASE_SCALE

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
        frozen = (self.state.projects.active.get(node_id) or {}).get("bill")
        if frozen is not None:
            return frozen
        return self.project_cost_now(node_id)

    def project_cost_now(self, node_id):
        """The cost if the project started today: labour and capital, plus
        the materials you do not already hold at current market prices."""
        materials, _up_front = self.project_material_parts(node_id)
        return ((self.project_cost_without_materials(node_id) + materials)
                * self.geography.material_cost_factor(node_id) * self.opposition_factor(node_id))

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
        self.household.bump_done_version()

    def _operating_changed(self):
        """Call after anything adds to or removes from self.household.operating."""
        self.household._cap_factor = None
        self.household.bump_operating_version()

    def _reset_operating(self):
        """Re-wrap operating in a fresh `_InvalidatingSet` and invalidate once."""
        self.state.projects.operating = _InvalidatingSet(self.state.projects.operating or set(), on_change=self._operating_changed)
        self._operating_changed()

    def _active_changed(self):
        """Call after anything adds to, removes from, or updates self.state.projects.active."""
        self.household.bump_active_version()

    def _reset_active(self):
        """Re-wrap active in a fresh `_InvalidatingDict` and invalidate once."""
        self.state.projects.active = _InvalidatingDict(
            self.state.projects.active or {},
            on_change=self._active_changed
        )
        self._active_changed()

    def _workforce_changed(self):
        """Call after anything mutates workforce state."""
        self.household.bump_workforce_version()

    def _reset_workforce(self):
        """Re-wrap employees in a fresh `_InvalidatingDict` and invalidate once."""
        self.state.household.employees = _InvalidatingDict(self.state.household.employees or {}, on_change=self._workforce_changed)
        self._workforce_changed()

    def _reset_economic_caches(self):
        """Wipe all transient economic derived-state caches and re-wrap containers on save/load."""
        self.household._done_seq = None
        self.household._cap_factor = None
        self.household._revenue_cache_key = None
        self.household._revenue_cache_val = None
        self.household._annual_mat_demand_cache = None
        self.household._rev_up_candidates_cache = None
        self.household._practice_cache = None
        self.household._goods_cat_state_cache = None
        self.household._goods_category_ratios_cache = None
        self.household._income_factor_cache = None
        self.household._goods_mkt_op_factor_cache = None
        self.household._material_demand_cache = None
        self.household._demand_by_tag_cache = None
        self._done_changed()
        self._reset_operating()
        self._reset_active()
        self._reset_workforce()

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
            seq = self.household._done_seq = [node_id for node_id in self.order if node_id in self.state.projects.done]
        return seq

    # Named so that `quote forest` and the
    # purchase itself cannot drift apart: a player must be able to ask the
    # price of coppice before spending capital on it, not only after.
    FOREST_LABOUR_HOURS_PER_HA = declare(
        "FOREST_LABOUR_HOURS_PER_HA", 5000.0, kind="temporary_heuristic",
        unit="labour hours per hectare", source=None, confidence="D",
        why="Purchase price of a hectare of coppice woodland. No attested "
            "attested land-price figure backs this; it exists mainly so "
            "`quote forest` and the purchase itself agree on a real price "
            "at all, per the comment above.")
    FOREST_COST_PER_HA = money_units.PricedInLabourHours("FOREST_LABOUR_HOURS_PER_HA")
