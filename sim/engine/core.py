"""The simulation itself: what one year does, and the loop over years."""
import collections, json, math, os, random

from .data import *          # the shared tables and loaders
from .data import (ANNUAL_WAGE, DEFAULTS, WAGES, load_civ, load_geography,
                   load_resources, trade_family)


from .economy import EconomyMixin
from .fog import FogMixin
from .geography import GeographyMixin
from .labour import LabourMixin
from .projects import ProjectsMixin
from .society import SocietyMixin
from .actors import Household


class Sim(EconomyMixin, FogMixin, GeographyMixin, LabourMixin,
          ProjectsMixin, SocietyMixin):
    def __init__(self, nodes, order, rng, events=True, cfg=None, verbose=False,
                 bounty_set=None, civ=None, manual=False):
        self.nodes = nodes
        # PRECOMPUTED ONCE: which node ids carry a `win_condition` at all,
        # sorted for the same reproducibility reason _check_win_conditions
        # (below) needs a fixed order. self.nodes is the loaded tech tree -
        # assigned exactly once, right here, and never reassigned or mutated
        # (checked: `grep -rn "self\.nodes\[.*\]\[.*\] *="` across every file
        # in this package turns up nothing, and every other write of
        # `self.nodes` anywhere is a *different* class's unrelated attribute
        # of the same name in commodities.py's CommodityLedger). So a node's
        # win_condition membership can never change after this point, and
        # this list can be built once here rather than every single year:
        # _check_win_conditions used to do `for k in sorted(self.nodes)`,
        # re-sorting all ~2,849 node ids from scratch every year to reach
        # the handful that actually carry a win_condition.
        self._win_condition_keys = sorted(
            k for k, n in nodes.items() if n.get("win_condition"))
        self.order = list(order)
        self.rng = rng
        self.events = events
        self.cfg = dict(DEFAULTS, **(cfg or {}))
        self.verbose = verbose
        self.bounty_set = set(bounty_set or ())
        self.civ = civ or load_civ()
        # MANUAL MODE: the optimizer in step() 4b never starts anything on its
        # own. The only projects that ever become active are ones something
        # called start_project() on, i.e. a human or an agent choosing them.
        # See the comment on step() 4b and on start_project() for why this
        # exists: without it, "choosing" a node in `play` was cosmetic.
        self.manual = bool(manual)
        self.w = self.civ["values"]
        # A civilization brings its own date, its own price level and its own
        # capacity to fund things. Norse Scandinavia does not start in 100 AD.
        self.cfg["start_year"] = int(self.civ.get("year", self.cfg["start_year"]))
        self.price_index = float(self.civ.get("price_index", 1.0))
        self.wage_index = float(self.civ.get("wage_index", 1.0))
        self._wage_index_base = self.wage_index
        self.state_capacity = float(self.civ.get("state_capacity", 0.7))
        self.pop_scale = max(0.05, float(self.civ.get("population", 65e6)) / 65e6)
        # A PLAGUE IS A HIT TO THE WHOLE LABOUR MARKET, NOT ONLY TO YOU. A
        # playtester watched the Black Death take a third of their own staff
        # and nothing else happen to the world around them, and asked why a
        # mortality event this size left everybody ELSE's wages untouched.
        # self._pop_scale_base is this civilization's steady-state size;
        # self.pop_deficit is how far below it the whole society currently
        # sits, and self.pop_scale (read everywhere else in the engine) is
        # always base * (1 - deficit). _demographic_recovery() below is the
        # only place that moves deficit, wage_index or pop_scale_base after
        # today; _shocks() in society.py only ever adds to the deficit.
        self._pop_scale_base = self.pop_scale
        self.pop_deficit = 0.0
        self._pop_recovery_years = 0.0
        # Population-raising technologies (sanitation, antisepsis, crop
        # rotation, canning...) queue their effect here instead of applying
        # it the year they complete - see apply_tech_effects in society.py.
        # Each entry is [fraction-of-baseline added per year, years left to
        # add it]: a lower death rate shows up in a headcount a generation
        # later, not the day a latrine opens.
        self._pop_tech_pending = []
        self.year = self.cfg["start_year"]
        c = self.cfg
        # THE FOUNDER'S HOUSEHOLD: money, staff, knowledge, plant and standing,
        # as its own object rather than eighty-odd attributes of this one. See
        # sim/engine/actors/household.py for what it holds and
        # docs/architecture/HOUSEHOLD_EXTRACTION.md for why: making this an
        # object of its own, rather than more state on `Sim`, is what would let
        # a government, a rival household or a firm exist someday, each owning
        # its own purse and its own knowledge instead of sharing this one.
        #
        # AT THIS SOCIETY'S PRICES, like everything else you will spend it on.
        # The kits are quoted in Rome 100 AD denarii, and once revenue and
        # living costs started converting (see economy.living_cost) leaving the
        # purse flat meant "four hundred denarii" bought a third more months of
        # bread in Luoyang than in Scandinavia, silently, for no modelled
        # reason. A kit is "a few months' subsistence", and a few months'
        # subsistence costs what it costs where you are. Computed here, where
        # `price_index` is in scope, and handed in as a plain number: a
        # Household should not need to know the shape of a run's config dict
        # to be built.
        #
        # `operating_changed=self._operating_changed`: `self` (this Sim) is
        # fully allocated already, even this early in `__init__` - Python
        # hands `__init__` a real, if not-yet-populated, instance - so a bound
        # method of it can be passed down right now. See Household.__init__'s
        # own docstring for why the callback travels this way instead of the
        # household reaching back up for it.
        self.household = Household(
            starting_capital=float(c["start_capital"]) * self.price_index,
            operating_changed=self._operating_changed)
        # EVERY AUTOMATIC BEHAVIOUR, IN ONE PLACE, SWITCHABLE.
        #
        # A tester's objection, and the right one: "everything that is automatic
        # should be controllable by players, allowing them to enable/disable
        # that, as well as manually doing it". Each of these was a thing the
        # engine did on its own with no way to stop it and, in several cases, no
        # log line saying it had happened. Defaults differ between the optimizer
        # and a human: the optimizer has to run unattended, so it manages its own
        # household; a player is handed nothing they did not ask for.
        #
        # STAYS ON `Sim`, NOT ON `Household` - see household.py's module
        # docstring: one key, auto_court_heir, is written for succession after
        # a mortal owner's death, and the rest of the dict is not worth
        # splitting away from it for that.
        self.policy = {
            "auto_hire":     not manual,   # grow the staff toward what you can support
            # ON for the optimizer, OFF for a player, and that distinction is the
            # whole of what the tester actually objected to. Their complaint was
            # not that the model has slavery, it was that it bought people on
            # THEIR behalf, in a game they were playing by hand, with no prompt
            # and no line in the log. An unattended run of a slave economy that
            # says "bought 6 people for the workshop" in its log is modelling the
            # thing; a player who never typed the command and finds twenty people
            # in their household is being lied to.
            "auto_buy_people": not manual,
            "auto_manumit":  not manual,
            "auto_train":    not manual,   # teach trades this society does not have
            "auto_mine":     not manual,   # sink shafts when a material binds
            "auto_forest":   not manual,   # buy coppice when charcoal binds
            "auto_mothball": True,         # stop working what you cannot pay for
            # OFF FOR A PLAYER, like every other automation, and on for the
            # optimizer, which the long civilisation runs are calibrated
            # against. This is the most consequential thing the game does
            # without being asked: it discards technologies you built, which
            # under fog are the only score there is. A break tester found it on
            # by default and quietly deleting their work. Nothing stops a
            # player shedding a loss-maker by hand - `mothball` does exactly
            # that, and gets it back with `restore`.
            "auto_shed":     not manual,
            # Open every concern that plainly pays for itself. On for the
            # optimizer, whose long runs are calibrated against a household
            # that does run what it builds, and off for a player, for whom
            # deciding what to actually operate is the point.
            "auto_open":     not manual,
            "auto_court_heir": not manual,  # court a dead patron's successor
            # Buy a job from an outside shop when a few pairs of hands are the
            # only thing standing between you and something you need.
            "auto_commission": not manual,
            "auto_bribe":    not manual,   # pay your way out of a scandal
        }
        # A HANDFUL OF "LAST TIME I SAID/DID X" TRACKERS, GIVEN A REAL
        # STARTING VALUE HERE INSTEAD OF SPRINGING INTO EXISTENCE ON FIRST
        # USE. Each of these used to be read exclusively through
        # `getattr(self, name, default)`, in a path that runs every single
        # step (some in step() itself, some in SocietyMixin's per-year
        # calls) with no assignment anywhere that could run before the
        # first possible read - so every read paid a dict-and-default
        # lookup to reconstruct a value this constructor can just set once.
        # Every default below is exactly the getattr default already in use
        # at every call site, so this cannot change behaviour... PROVIDED
        # the attribute is not also one perf_fingerprint.py hashes: that
        # tool hashes protocol.py's SAVE_FIELDS list at year 0, and several
        # of ITS OWN comments say a save MISSING one of those fields reads
        # back as "has never happened yet" (None) - a state distinct from
        # an explicit zero or sentinel. Giving such a field a real value
        # here would make year 0's hash disagree with a baseline recorded
        # before this field existed, and that is exactly what happened the
        # first time this was tried: all nine fingerprint scenarios
        # diverged at year 0, every one of them tracing back to a
        # SAVE_FIELDS member.
        #
        # ONLY THE FIELDS THAT STAYED ON `Sim` remain here after the household
        # extraction - the household's own equivalents of this same pattern
        # (`insolvent_years`, `wage_hours_this_year`, `_said_deputies`, and
        # the rest) moved to Household.__init__ along with everything else it
        # owns; see that constructor's own copy of this comment. What is left
        # below is WORLD state (a shock or a debasement is something that
        # happened to the whole society, not to this household alone) and so
        # was never a candidate to move.
        self._said_wage_cascade = -999     # last year a wage-cascade note was printed; -999 guarantees the first qualifying year always warns
        self._literacy_said = -999            # last year a literacy-census note was printed
        self._food_diffusion_said = -999      # last year a food-diffusion note was printed
        self._said_condition = set()          # hazard-condition messages already printed once
        # THE FOLLOWING EIGHT FIELDS ARE BIOGRAPHICAL TO ONE MORTAL PERSON, not
        # to a household in general, and stay on `Sim` for exactly that reason
        # - see household.py's module docstring for the full argument. Moving
        # them would mean deciding, right now, with no second example to
        # design against, what death, personal hours or a patron mean for a
        # firm or a government; that is a real design question and this
        # extraction does not answer it by default.
        self.founder_alive = True
        self.dead_reason = None
        self.director_hours_spent_founder = 0.0
        # founder remaining lifespan, elite male already aged 35
        self.life_left = (1e9 if self.cfg["immortal"]
                          else max(5, rng.gauss(self.cfg["founder_life_mean"],
                                                self.cfg["founder_life_sd"])))
        self.living_cost_paid = 0.0
        # WORLD state: monetary and real facts about the whole civilisation,
        # not about this household. money_real is currency debasement;
        # economy/output_factor are the size and health of the whole imperial
        # economy relative to 100 AD, crushed by war and plague, not by any
        # one household's fortunes.
        self.money_real = 1.0     # purchasing power of a denarius, 1.0 at 100 AD
        self.economy = 1.0        # size of the imperial economy relative to 100 AD
        self.output_factor = 1.0  # real output, crushed by war and plague, not by debasement
        # --- RAW MATERIAL QUANTITIES -------------------------------------
        # Until this existed the model assumed that if a material existed
        # anywhere you had unlimited quantities of it. That was the largest
        # remaining falsehood in the simulation.
        self.res = load_resources()
        # --- GEOGRAPHY: where things are, FOR THE CIVILIZATION IN PLAY -----
        # geography.json used to give every region one Rome-centric `reach`
        # and nothing in this file ever read it. See load_geography() and
        # region_reach()/material_reach() below for the fix: real coordinates,
        # a reach computed from THIS civ's own home ground, and a material
        # cost that follows from it. All of the below depends only on the
        # civ file and the (static) geography file, so it is computed once.
        self.geo = load_geography()
        self._regions = {k: v for k, v in (self.geo.get("regions") or {}).items()
                          if not k.startswith("_")}
        self._home_centroid = self._compute_home_centroid()
        # node id -> located_materials key. Lets material_cost_factor() find
        # the geography entry for a location-gated tech node (mat_gutta_percha,
        # mat_natural_rubber, ...) without the tech tree needing to know
        # anything about geography itself.
        self._mat_unlock = {}
        for mk, md in (self.geo.get("located_materials") or {}).items():
            if mk.startswith("_"):
                continue
            for nid in (md.get("unlocks") or []):
                self._mat_unlock[nid] = mk
        # Mineral market access used to be `self.pop_scale`, i.e. "how much
        # coal can you buy" scaled by HOW MANY PEOPLE YOU HAVE. That is wrong
        # in both directions: Norse Scandinavia got 2.3% of Rome's coal
        # because it has 2.3% of the people, and England in 1300 got 7%,
        # when England is precisely where the coal actually IS. Geology is
        # not demography. See _compute_mineral_scale() for the replacement.
        # It depends only on home_regions and reach, neither of which change
        # during a run, so it is computed once here rather than every year.
        self._mineral_scale = {m: self._compute_mineral_scale(m)
                                for m in ("iron", "coal", "copper", "lead",
                                          "tin", "silver", "saltpetre")}
        # Whatever this civilization already has is free and already done, and it
        # is GRANTED, not earned. A playtester pointed out that these were being
        # counted in done_earned as though the founder had built them, which both
        # flatters the player and, worse, exposed a society's own ancestral
        # crafts to being "forgotten" in a sacking. Han China does not forget how
        # to cast iron because your workshop burned down.
        #
        # Populates self.household.done/.granted, not a fresh set here, and
        # stays on Sim rather than moving into Household.__init__ because it
        # needs the loaded tree and civ record to validate against (and to
        # raise ValueError on an unknown starting technology) - state this
        # class deliberately does not hold a reference to.
        starting_techs = self.civ["starting_techs"]
        missing = sorted(k for k in starting_techs if k not in self.nodes)
        if missing:
            # Refuse a corrupt opening rather than merely warning and running a
            # different scenario. Eight ids were once silently dropped across
            # three civilizations, including four of the Mexica's five.
            raise ValueError("civilization %r lists unknown starting technologies: %s"
                             % (self.civ.get("id", "?"), ", ".join(missing)))
        for k in starting_techs:
            self.household.done.add(k)
            self._done_changed()
            self.household.granted.add(k)
        # Starting ownership is deliberately exhausted by starting_techs.
        # Tier and zero cost describe a node's position in the universal graph;
        # they do not mean every society on Earth already owns it.  In
        # particular, never infer Roman materials or institutions for another
        # civilization from those fields.

    # ---- OUTSIDE-SURFACE PROPERTIES FOR THE EXTRACTED HOUSEHOLD ----------
    #
    # Everything below is a thin, single-line forward to `self.household`,
    # for the JSON protocol, save/load, the CLI and the tests - none of them
    # hot, all of them outside the engine. See
    # docs/architecture/HOUSEHOLD_EXTRACTION.md section 2 for why this is a
    # property here and a rewritten call site (`self.household.x`) inside the
    # six mixins and core.py's own methods, rather than one convenient
    # `__getattr__` covering both: measured at 51x slower per access than the
    # rewrite, and slow exactly on the path - `self.x` succeeding today,
    # `__getattr__` firing only on failure - that is the COMMON case for every
    # one of these once the field lives on `household` instead of `self`.
    #
    # Every getter is exactly one attribute access and nothing else, on
    # purpose (see the same section): a bug inside a longer property body
    # would raise its own AttributeError, indistinguishable from the
    # intentional one below, and get silently swallowed by any caller using
    # `getattr(sim, name, default)`.
    #
    # LAZY FIELDS (the household never assigns these until something actually
    # happens worth recording) are marked below: the getter raises
    # AttributeError exactly when `self.household` does not have the
    # attribute yet, ON PURPOSE - it supplies no default of its own, so
    # `getattr(sim, name, default)` still sees the field's true, possibly-
    # absent, state, exactly as it did before this field moved. See
    # sim/ARCHITECTURE.md for the one time promoting a lazily-created field
    # to a real attribute passed the whole suite while silently breaking
    # this exact contract.

    @property
    def _cap_factor(self):
        return self.household._cap_factor

    @_cap_factor.setter
    def _cap_factor(self, value):
        self.household._cap_factor = value

    @property
    def _done_seq(self):
        return self.household._done_seq

    @_done_seq.setter
    def _done_seq(self, value):
        self.household._done_seq = value

    @property
    def _said_confiscation_band(self):
        return self.household._said_confiscation_band

    @_said_confiscation_band.setter
    def _said_confiscation_band(self, value):
        self.household._said_confiscation_band = value

    @property
    def _said_eminence(self):
        return self.household._said_eminence

    @_said_eminence.setter
    def _said_eminence(self, value):
        self.household._said_eminence = value

    @property
    def _said_notice_approach(self):
        return self.household._said_notice_approach

    @_said_notice_approach.setter
    def _said_notice_approach(self, value):
        self.household._said_notice_approach = value

    @property
    def _said_requisition(self):
        return self.household._said_requisition

    @_said_requisition.setter
    def _said_requisition(self, value):
        self.household._said_requisition = value

    @property
    def _spend_this_year(self):
        return self.household._spend_this_year

    @_spend_this_year.setter
    def _spend_this_year(self, value):
        self.household._spend_this_year = value

    @property
    def _staff_scale(self):
        return self.household._staff_scale

    @_staff_scale.setter
    def _staff_scale(self, value):
        self.household._staff_scale = value

    @property
    def active(self):
        return self.household.active

    @active.setter
    def active(self, value):
        self.household.active = value

    @property
    def artisans(self):
        return self.household.artisans

    @artisans.setter
    def artisans(self, value):
        self.household.artisans = value

    @property
    def atrocity(self):
        return self.household.atrocity

    @atrocity.setter
    def atrocity(self, value):
        self.household.atrocity = value

    @property
    def binding(self):
        return self.household.binding

    @binding.setter
    def binding(self, value):
        self.household.binding = value

    @property
    def bondage_debt(self):
        return self.household.bondage_debt

    @bondage_debt.setter
    def bondage_debt(self, value):
        self.household.bondage_debt = value

    @property
    def bondage_years_left(self):
        return self.household.bondage_years_left

    @bondage_years_left.setter
    def bondage_years_left(self, value):
        self.household.bondage_years_left = value

    @property
    def bountied(self):
        return self.household.bountied

    @bountied.setter
    def bountied(self, value):
        self.household.bountied = value

    @property
    def bounties_paid(self):
        return self.household.bounties_paid

    @bounties_paid.setter
    def bounties_paid(self, value):
        self.household.bounties_paid = value

    @property
    def bribes_ytd(self):
        return self.household.bribes_ytd

    @bribes_ytd.setter
    def bribes_ytd(self, value):
        self.household.bribes_ytd = value

    @property
    def capital(self):
        return self.household.capital

    @capital.setter
    def capital(self, value):
        self.household.capital = value

    @property
    def commissioned(self):
        return self.household.commissioned

    @commissioned.setter
    def commissioned(self, value):
        self.household.commissioned = value

    @property
    def contract_hours(self):
        return self.household.contract_hours

    @contract_hours.setter
    def contract_hours(self, value):
        self.household.contract_hours = value

    @property
    def contract_projects(self):
        return self.household.contract_projects

    @contract_projects.setter
    def contract_projects(self, value):
        self.household.contract_projects = value

    @property
    def credit_frozen_until(self):
        return self.household.credit_frozen_until

    @credit_frozen_until.setter
    def credit_frozen_until(self, value):
        self.household.credit_frozen_until = value

    @property
    def directors_extra(self):
        return self.household.directors_extra

    @directors_extra.setter
    def directors_extra(self, value):
        self.household.directors_extra = value

    @property
    def done(self):
        return self.household.done

    @done.setter
    def done(self, value):
        self.household.done = value

    @property
    def eminence(self):
        return self.household.eminence

    @eminence.setter
    def eminence(self, value):
        self.household.eminence = value

    @property
    def employees(self):
        return self.household.employees

    @employees.setter
    def employees(self, value):
        self.household.employees = value

    @property
    def failed_attempts(self):
        return self.household.failed_attempts

    @failed_attempts.setter
    def failed_attempts(self, value):
        self.household.failed_attempts = value

    @property
    def familiarity(self):
        return self.household.familiarity

    @familiarity.setter
    def familiarity(self, value):
        self.household.familiarity = value

    @property
    def forest_ha(self):
        return self.household.forest_ha

    @forest_ha.setter
    def forest_ha(self, value):
        self.household.forest_ha = value

    @property
    def forgotten(self):
        return self.household.forgotten

    @forgotten.setter
    def forgotten(self, value):
        self.household.forgotten = value

    @property
    def freedmen(self):
        return self.household.freedmen

    @freedmen.setter
    def freedmen(self, value):
        self.household.freedmen = value

    @property
    def goal_year(self):
        return self.household.goal_year

    @goal_year.setter
    def goal_year(self, value):
        self.household.goal_year = value

    @property
    def gov(self):
        return self.household.gov

    @gov.setter
    def gov(self, value):
        self.household.gov = value

    @property
    def granted(self):
        return self.household.granted

    @granted.setter
    def granted(self, value):
        self.household.granted = value

    @property
    def hour_allocations(self):
        return self.household.hour_allocations

    @hour_allocations.setter
    def hour_allocations(self, value):
        self.household.hour_allocations = value

    @property
    def last_military_demand(self):
        return self.household.last_military_demand

    @last_military_demand.setter
    def last_military_demand(self, value):
        self.household.last_military_demand = value

    @property
    def last_settlement(self):
        return self.household.last_settlement

    @last_settlement.setter
    def last_settlement(self, value):
        self.household.last_settlement = value

    @property
    def last_taught(self):
        return self.household.last_taught

    @last_taught.setter
    def last_taught(self, value):
        self.household.last_taught = value

    @property
    def log(self):
        return self.household.log

    @log.setter
    def log(self, value):
        self.household.log = value

    @property
    def manumitted_total(self):
        return self.household.manumitted_total

    @manumitted_total.setter
    def manumitted_total(self, value):
        self.household.manumitted_total = value

    @property
    def market_pressure(self):
        return self.household.market_pressure

    @market_pressure.setter
    def market_pressure(self, value):
        self.household.market_pressure = value

    @property
    def mine_cost_paid(self):
        return self.household.mine_cost_paid

    @mine_cost_paid.setter
    def mine_cost_paid(self, value):
        self.household.mine_cost_paid = value

    @property
    def mine_pending(self):
        return self.household.mine_pending

    @mine_pending.setter
    def mine_pending(self, value):
        self.household.mine_pending = value

    @property
    def mine_ready(self):
        return self.household.mine_ready

    @mine_ready.setter
    def mine_ready(self, value):
        self.household.mine_ready = value

    @property
    def mine_tranches(self):
        # LAZY: absence is meaningful (see the section comment above).
        # Do not add a default here.
        return self.household.mine_tranches

    @mine_tranches.setter
    def mine_tranches(self, value):
        self.household.mine_tranches = value

    @property
    def mines(self):
        return self.household.mines

    @mines.setter
    def mines(self, value):
        self.household.mines = value

    @property
    def mothballed(self):
        return self.household.mothballed

    @mothballed.setter
    def mothballed(self, value):
        self.household.mothballed = value

    @property
    def nitre_bed_m2(self):
        return self.household.nitre_bed_m2

    @nitre_bed_m2.setter
    def nitre_bed_m2(self, value):
        self.household.nitre_bed_m2 = value

    @property
    def opened_year(self):
        return self.household.opened_year

    @opened_year.setter
    def opened_year(self, value):
        self.household.opened_year = value

    @property
    def operating(self):
        return self.household.operating

    @operating.setter
    def operating(self, value):
        self.household.operating = value

    @property
    def paid_towards(self):
        return self.household.paid_towards

    @paid_towards.setter
    def paid_towards(self, value):
        self.household.paid_towards = value

    @property
    def protection(self):
        return self.household.protection

    @protection.setter
    def protection(self, value):
        self.household.protection = value

    @property
    def reputation(self):
        return self.household.reputation

    @reputation.setter
    def reputation(self, value):
        self.household.reputation = value

    @property
    def scandal(self):
        return self.household.scandal

    @scandal.setter
    def scandal(self, value):
        self.household.scandal = value

    @property
    def scholars(self):
        return self.household.scholars

    @scholars.setter
    def scholars(self, value):
        self.household.scholars = value

    @property
    def shortages(self):
        return self.household.shortages

    @shortages.setter
    def shortages(self, value):
        self.household.shortages = value

    @property
    def slaves(self):
        return self.household.slaves

    @slaves.setter
    def slaves(self, value):
        self.household.slaves = value

    @property
    def stalled(self):
        return self.household.stalled

    @stalled.setter
    def stalled(self, value):
        self.household.stalled = value

    @property
    def teaching_hours_this_year(self):
        return self.household.teaching_hours_this_year

    @teaching_hours_this_year.setter
    def teaching_hours_this_year(self, value):
        self.household.teaching_hours_this_year = value

    @property
    def throttle(self):
        return self.household.throttle

    @throttle.setter
    def throttle(self, value):
        self.household.throttle = value

    @property
    def total_spend(self):
        return self.household.total_spend

    @total_spend.setter
    def total_spend(self, value):
        self.household.total_spend = value

    @property
    def trade_hours_used(self):
        return self.household.trade_hours_used

    @trade_hours_used.setter
    def trade_hours_used(self, value):
        self.household.trade_hours_used = value

    @property
    def trade_introduced_year(self):
        return self.household.trade_introduced_year

    @trade_introduced_year.setter
    def trade_introduced_year(self, value):
        self.household.trade_introduced_year = value

    @property
    def trades_created(self):
        return self.household.trades_created

    @trades_created.setter
    def trades_created(self, value):
        self.household.trades_created = value

    @property
    def trades_endemic(self):
        return self.household.trades_endemic

    @trades_endemic.setter
    def trades_endemic(self, value):
        self.household.trades_endemic = value

    @property
    def training(self):
        return self.household.training

    @training.setter
    def training(self, value):
        self.household.training = value

    @property
    def wages_paid(self):
        return self.household.wages_paid

    @wages_paid.setter
    def wages_paid(self, value):
        self.household.wages_paid = value

    @property
    def wages_prepaid(self):
        return self.household.wages_prepaid

    @wages_prepaid.setter
    def wages_prepaid(self, value):
        self.household.wages_prepaid = value

    @property
    def work_trade(self):
        return self.household.work_trade

    @work_trade.setter
    def work_trade(self, value):
        self.household.work_trade = value

    @property
    def _dashboard_history(self):
        # LAZY: absence is meaningful (see the section comment above).
        # Do not add a default here.
        return self.household._dashboard_history

    @_dashboard_history.setter
    def _dashboard_history(self, value):
        self.household._dashboard_history = value

    @property
    def _demand_by_emp_key_cache(self):
        # LAZY: absence is meaningful (see the section comment above).
        # Do not add a default here.
        return self.household._demand_by_emp_key_cache

    @_demand_by_emp_key_cache.setter
    def _demand_by_emp_key_cache(self, value):
        self.household._demand_by_emp_key_cache = value

    @property
    def _demand_by_tag_cache(self):
        # LAZY: absence is meaningful (see the section comment above).
        # Do not add a default here.
        return self.household._demand_by_tag_cache

    @_demand_by_tag_cache.setter
    def _demand_by_tag_cache(self, value):
        self.household._demand_by_tag_cache = value

    @property
    def _goods_cat_state_cache(self):
        # LAZY: absence is meaningful (see the section comment above).
        # Do not add a default here.
        return self.household._goods_cat_state_cache

    @_goods_cat_state_cache.setter
    def _goods_cat_state_cache(self, value):
        self.household._goods_cat_state_cache = value

    @property
    def _labour_pressure(self):
        # LAZY: absence is meaningful (see the section comment above).
        # Do not add a default here.
        return self.household._labour_pressure

    @_labour_pressure.setter
    def _labour_pressure(self, value):
        self.household._labour_pressure = value

    @property
    def _last_buy_refusal(self):
        # LAZY: absence is meaningful (see the section comment above).
        # Do not add a default here.
        return self.household._last_buy_refusal

    @_last_buy_refusal.setter
    def _last_buy_refusal(self, value):
        self.household._last_buy_refusal = value

    @property
    def _last_subst_gap(self):
        # LAZY: absence is meaningful (see the section comment above).
        # Do not add a default here.
        return self.household._last_subst_gap

    @_last_subst_gap.setter
    def _last_subst_gap(self, value):
        self.household._last_subst_gap = value

    @property
    def _material_demand_cache(self):
        # LAZY: absence is meaningful (see the section comment above).
        # Do not add a default here.
        return self.household._material_demand_cache

    @_material_demand_cache.setter
    def _material_demand_cache(self, value):
        self.household._material_demand_cache = value

    @property
    def _material_stock_ledger(self):
        # LAZY: absence is meaningful (see the section comment above).
        # Do not add a default here.
        return self.household._material_stock_ledger

    @_material_stock_ledger.setter
    def _material_stock_ledger(self, value):
        self.household._material_stock_ledger = value

    @property
    def _operating_ver(self):
        # LAZY: absence is meaningful (see the section comment above).
        # Do not add a default here.
        return self.household._operating_ver

    @_operating_ver.setter
    def _operating_ver(self, value):
        self.household._operating_ver = value

    @property
    def _practice_cache(self):
        # LAZY: absence is meaningful (see the section comment above).
        # Do not add a default here.
        return self.household._practice_cache

    @_practice_cache.setter
    def _practice_cache(self, value):
        self.household._practice_cache = value

    @property
    def _rev_up_candidates_cache(self):
        # LAZY: absence is meaningful (see the section comment above).
        # Do not add a default here.
        return self.household._rev_up_candidates_cache

    @_rev_up_candidates_cache.setter
    def _rev_up_candidates_cache(self, value):
        self.household._rev_up_candidates_cache = value

    @property
    def _said_autoopen(self):
        # LAZY: absence is meaningful (see the section comment above).
        # Do not add a default here.
        return self.household._said_autoopen

    @_said_autoopen.setter
    def _said_autoopen(self, value):
        self.household._said_autoopen = value

    @property
    def _said_deputies(self):
        # LAZY: absence is meaningful (see the section comment above).
        # Do not add a default here.
        return self.household._said_deputies

    @_said_deputies.setter
    def _said_deputies(self, value):
        self.household._said_deputies = value

    @property
    def _said_near_limit(self):
        # LAZY: absence is meaningful (see the section comment above).
        # Do not add a default here.
        return self.household._said_near_limit

    @_said_near_limit.setter
    def _said_near_limit(self, value):
        self.household._said_near_limit = value

    @property
    def _said_parallelism(self):
        # LAZY: absence is meaningful (see the section comment above).
        # Do not add a default here.
        return self.household._said_parallelism

    @_said_parallelism.setter
    def _said_parallelism(self, value):
        self.household._said_parallelism = value

    @property
    def _said_scandal(self):
        # LAZY: absence is meaningful (see the section comment above).
        # Do not add a default here.
        return self.household._said_scandal

    @_said_scandal.setter
    def _said_scandal(self, value):
        self.household._said_scandal = value

    @property
    def _said_stack_caution(self):
        # LAZY: absence is meaningful (see the section comment above).
        # Do not add a default here.
        return self.household._said_stack_caution

    @_said_stack_caution.setter
    def _said_stack_caution(self, value):
        self.household._said_stack_caution = value

    @property
    def _stock_throttle_cache(self):
        # LAZY: absence is meaningful (see the section comment above).
        # Do not add a default here.
        return self.household._stock_throttle_cache

    @_stock_throttle_cache.setter
    def _stock_throttle_cache(self, value):
        self.household._stock_throttle_cache = value

    @property
    def _stock_throttle_sig(self):
        # LAZY: absence is meaningful (see the section comment above).
        # Do not add a default here.
        return self.household._stock_throttle_sig

    @_stock_throttle_sig.setter
    def _stock_throttle_sig(self, value):
        self.household._stock_throttle_sig = value

    @property
    def done_year(self):
        # LAZY: absence is meaningful (see the section comment above).
        # Do not add a default here.
        return self.household.done_year

    @done_year.setter
    def done_year(self, value):
        self.household.done_year = value

    @property
    def farm_hectares(self):
        # LAZY: absence is meaningful (see the section comment above).
        # Do not add a default here.
        return self.household.farm_hectares

    @farm_hectares.setter
    def farm_hectares(self, value):
        self.household.farm_hectares = value

    @property
    def granted_staff(self):
        # LAZY: absence is meaningful (see the section comment above).
        # Do not add a default here.
        return self.household.granted_staff

    @granted_staff.setter
    def granted_staff(self, value):
        self.household.granted_staff = value

    @property
    def insolvent_years(self):
        # LAZY: absence is meaningful (see the section comment above).
        # Do not add a default here.
        return self.household.insolvent_years

    @insolvent_years.setter
    def insolvent_years(self, value):
        self.household.insolvent_years = value

    @property
    def inst_units(self):
        # LAZY: absence is meaningful (see the section comment above).
        # Do not add a default here.
        return self.household.inst_units

    @inst_units.setter
    def inst_units(self, value):
        self.household.inst_units = value

    @property
    def interest_paid(self):
        # LAZY: absence is meaningful (see the section comment above).
        # Do not add a default here.
        return self.household.interest_paid

    @interest_paid.setter
    def interest_paid(self, value):
        self.household.interest_paid = value

    @property
    def last_withdrawal(self):
        # LAZY: absence is meaningful (see the section comment above).
        # Do not add a default here.
        return self.household.last_withdrawal

    @last_withdrawal.setter
    def last_withdrawal(self, value):
        self.household.last_withdrawal = value

    @property
    def scandal_last_year(self):
        # LAZY: absence is meaningful (see the section comment above).
        # Do not add a default here.
        return self.household.scandal_last_year

    @scandal_last_year.setter
    def scandal_last_year(self, value):
        self.household.scandal_last_year = value

    @property
    def shut_for_staff(self):
        # LAZY: absence is meaningful (see the section comment above).
        # Do not add a default here.
        return self.household.shut_for_staff

    @shut_for_staff.setter
    def shut_for_staff(self, value):
        self.household.shut_for_staff = value

    @property
    def spend_last_year(self):
        # LAZY: absence is meaningful (see the section comment above).
        # Do not add a default here.
        return self.household.spend_last_year

    @spend_last_year.setter
    def spend_last_year(self, value):
        self.household.spend_last_year = value

    @property
    def trade_schools(self):
        # LAZY: absence is meaningful (see the section comment above).
        # Do not add a default here.
        return self.household.trade_schools

    @trade_schools.setter
    def trade_schools(self, value):
        self.household.trade_schools = value

    @property
    def wage_hours_this_year(self):
        # LAZY: absence is meaningful (see the section comment above).
        # Do not add a default here.
        return self.household.wage_hours_this_year

    @wage_hours_this_year.setter
    def wage_hours_this_year(self, value):
        self.household.wage_hours_this_year = value

    @property
    def wages_earned(self):
        # LAZY: absence is meaningful (see the section comment above).
        # Do not add a default here.
        return self.household.wages_earned

    @wages_earned.setter
    def wages_earned(self, value):
        self.household.wages_earned = value

    @property
    def worker_housing_places(self):
        # LAZY: absence is meaningful (see the section comment above).
        # Do not add a default here.
        return self.household.worker_housing_places

    @worker_housing_places.setter
    def worker_housing_places(self, value):
        self.household.worker_housing_places = value

    @property
    def revealed(self):
        # LAZY, AND A RATCHET, NOT A DEFAULT: the real ratchet logic
        # (union-only writes) lives on Household.revealed, moved there with
        # the rest of fog-of-war visibility - see fog.py's FogMixin comment
        # and sim/engine/actors/household.py. This is a plain forward, not
        # a second ratchet: assigning through it calls Household's setter
        # exactly once.
        return self.household.revealed

    @revealed.setter
    def revealed(self, value):
        self.household.revealed = value

    def _demographic_recovery(self, yr):
        """Mortality shocks fade and population-raising technologies build in.

        Two unrelated inputs move the same two numbers, self.pop_scale and
        self.wage_index, and they are handled together because both ARE the
        same underlying thing: how many people this society has to work with
        this year. A staff_loss hazard in _shocks() (society.py) adds to
        self.pop_deficit, the fraction the whole society currently sits
        below its baseline size. A population-raising technology adds to
        self._pop_scale_base through self._pop_tech_pending, queued by
        apply_tech_effects() (society.py).

        The deficit decays EXPONENTIALLY rather than healing on a fixed
        clock, so a run always reads "a little better than last year" rather
        than sitting frozen until some cliff-edge recovery date:
        deficit *= exp(-1/tau), with tau set so that after
        self._pop_recovery_years the deficit is down to about 5% of where
        the shock left it (e**-3 ~= 0.05, the standard "three time
        constants" rule of thumb). England's population took roughly 150
        years to regain its pre-Black-Death level (Broadberry et al.,
        British Economic Growth, 2015), and england_1300.json's Black Death
        entry is staff_loss 0.45, so 150 years is calibrated to THAT hazard
        specifically; every other hazard's recovery horizon scales off it in
        proportion to how much of the population it actually took, so the
        Antonine plague (0.28) gets a shorter, gentler recovery than the
        Black Death, not the same 150 years regardless of size.
        """
        if self.pop_deficit > 1e-6:
            tau = max(10.0, self._pop_recovery_years) / 3.0
            self.pop_deficit *= math.exp(-1.0 / tau)
        else:
            self.pop_deficit = 0.0
        if self._pop_tech_pending:
            still = []
            for per_year, years_left in self._pop_tech_pending:
                self._pop_scale_base += per_year
                if years_left > 1:
                    still.append((per_year, years_left - 1))
            self._pop_tech_pending = still
        self._refresh_demographic_indexes(yr)

    def _refresh_demographic_indexes(self, yr):
        """Apply the current demographic shortfall to population and wages.

        Kept separate from recovery so a shock can make its announced effects
        visible immediately, without also granting a free year of recovery.
        """
        self.pop_scale = max(0.05, self._pop_scale_base * (1.0 - self.pop_deficit))
        # LABOUR SCARCER, SO DEARER. Elasticity 0.9 means a population still a
        # third below trend (deficit 0.33) carries about a 30% wage premium;
        # run for a century, as the Black Death's deficit roughly does before
        # it has decayed away, and that compounds into the rough doubling
        # Phelps Brown and Hopkins' English real-wage index shows across the
        # century after 1348, without the elasticity itself needing to be
        # implausibly large. wage_index is what ANNUAL_WAGE, WAGES and every
        # hiring, teaching and payroll cost in the engine are already
        # multiplied by, so this one number is the whole of "higher wages
        # raise the cost of everything built with labour" - nothing else
        # downstream needs to change.
        self.wage_index = self._wage_index_base * (1.0 + 0.9 * self.pop_deficit)
        # SAY WHY THE WAGE BILL MOVED. A plague that quietly doubles every
        # hiring and teaching cost for decades and never says so reads as the
        # economy drifting for no reason - exactly the complaint this whole
        # mechanism exists to answer. Throttled the same way the debasement
        # and output_factor messages are (see _shocks): once when it is worth
        # mentioning, then a reminder at most every 15 years, not every year
        # of a shortfall that can run for a century.
        premium = (self.wage_index / self._wage_index_base - 1.0) * 100
        if premium > 0.5 and yr - self._said_wage_cascade >= 15:
            self._said_wage_cascade = yr
            self.household.log.append((yr, "population still %d%% below trend: wages "
                                 "(and anything billed in them) are running "
                                 "%d%% above normal for here, and will ease "
                                 "as the population does"
                             % (round(self.pop_deficit * 100), round(premium))))

    # -- helpers ------------------------------------------------------------

    # Years between one automatic teaching of a trade and the next. Long
    # enough that restoring a lost trade is an event rather than a habit.
    RETEACH_EVERY = 25

    def has(self, k):
        return k in self.household.done

    # THE ONE PLACE that answers "what is my corpus worth against a
    # sacking" - the sack in SocietyMixin._shocks and the `risk` reply in
    # FogMixin.knowledge_risk used to each carry their own copy of this
    # table, and they drifted: `risk` was fixed to read `has()` (a corpus
    # that is written and dispersed does not stop existing because the
    # scriptorium that produced it closed - copies already in other
    # people's hands are still in other people's hands), and the sack was
    # never brought along, so it kept reading `running()` and applied
    # corpus_written's weaker 0.45/0.22 to a household `risk` was telling,
    # in the same breath, it had corpus_dispersed's 0.12/0.08. A player
    # who trusted the screen lost nearly three times what they were told
    # to expect. Call this, from both places, rather than re-deriving it -
    # that is the only way to make the two screens unable to disagree
    # again.
    def corpus_hedge(self):
        """(loss_chance, fraction_lost, hedge_name) a sacking faces right now.

        `has`, not `running`: see the comment above `has` itself and
        FogMixin.knowledge_risk for the fuller argument. `hedge_name` is
        None if neither corpus exists yet.
        """
        if self.has("corpus_dispersed"):
            return 0.12, 0.08, "corpus_dispersed"
        if self.has("corpus_written"):
            return 0.45, 0.22, "corpus_written"
        return 0.80, 0.40, None

    # ---- GEOGRAPHY: reach and material cost, FOR THE CIVILIZATION IN PLAY --
    # geography.json used to hard-code one `reach` per region, measured from
    # Italy, and nothing in this file ever read it as a cost: `civs` printed
    # `base_reach` and that was the entire effect either number had. Play Han
    # China and the model still treated Chinese silk as three reach-steps
    # away and Malaya, which Chinese and Malay traders already sail to
    # routinely, as an exotic frontier, while Italy -- a place that
    # civilization has never seen -- was reach 0. That is backwards for
    # every civilization except Rome. Everything below computes reach from
    # the ACTUAL civilization's own home ground instead.

    def step(self):
        c = self.cfg
        yr = self.year
        # WHERE SCANDAL STOOD WHEN THE PLAYER LAST LOOKED. `state` prints the
        # chance of being denounced from the CURRENT scandal, and scandal moves
        # DURING the step - so a break tester read "scandal 21.9 ... 0% chance
        # of being denounced this year", pressed step once, and the same batch
        # printed the first warning and "RUN ENDS: denounced: as a sorcerer".
        # The figure was never wrong; it was answering about a year that had
        # already gone. A player needs the direction as well as the level, and
        # this is the only place that knows both.
        self.household.scandal_last_year = self.household.scandal

        # 0. PEOPLE WHOSE APPRENTICESHIP ENDED. This block used to sit at the
        #    very BOTTOM of step(), after the year's work had already been
        #    handed out - so machinists promised "ready in 102" were not usable
        #    on anything until 103, and a break tester timed both the message
        #    and the ready_year and found each a year late. A man who finishes
        #    his training at the turn of the year works that year.
        # People bought this year are not artisans this year.
        if self.household.training:
            still = []
            for row in self.household.training:
                cap, ready = row[0], row[1]
                trade = row[2] if len(row) > 2 else None
                count = row[3] if len(row) > 3 else 0.0
                if self.year >= ready:
                    if trade:
                        # A trade you taught. They are now yours to pay, and
                        # they are that trade and no other.
                        self.household.employees[trade] = self.household.employees.get(trade, 0.0) + count
                        self.household.log.append((self.year, "%g %s%s finish their training"
                                         % (count, trade, "s" if count != 1 else "")))
                        self._resync_pools()
                    else:
                        # They are trained now, so _resync_pools counts them
                        # from the people you actually hold - see the note
                        # there about why adding to self.household.artisans directly was
                        # thrown away at the next call.
                        self.household.log.append((self.year,
                                         "%g of the people you bought finish "
                                         "learning the work" % round(cap / 0.55, 1)))
                else:
                    still.append(row)
            # BEFORE the resync, not after: _resync_pools counts who is still
            # learning off this very list, so recomputing while the matured row
            # was still on it cost a whole extra year of everybody's time.
            self.household.training = still
            self._resync_pools()


        # 1. staff. ATTRITION IS UNCONDITIONAL: people die, are poached and grow
        #    old whatever your policy is. GROWTH IS NOT. It used to be, and that
        #    was the same fault as buying people without being asked: a player
        #    who never issued a single command watched the staff climb on its own.
        #
        #    With auto_hire on (the default for the optimizer, off for a player)
        #    the old smoothing toward capacity runs as before, which is what the
        #    long civilization runs are calibrated against. With it off, the only
        #    things that change the staff are hire, fire, train, buy and manumit.
        sc_cap, ar_cap, di_cap = self.staff_capacity()
        ATTRITION = 0.035           # Roman adult mortality plus normal turnover
        # PEOPLE ARE WHOLE. This used to multiply every trade's headcount by
        # (1 - ATTRITION) and carry on, so ten smiths lost exactly 0.35 of a
        # smith and the engine went on holding the fraction: a household
        # could read "1.32 artisans" or "0.03 engineers" on its own roster,
        # the latter drawing 0.03 of a wage while supervising nothing. The
        # user's objection was exact: a death is a discrete thing that either
        # happens to a particular person this year or does not, so each of
        # the whole people actually on the books now gets their own yearly
        # roll against self.rng - sorted by trade name so the draws happen in
        # the same order whatever PYTHONHASHSEED the process started with,
        # which is what every other rng loop over this dict already does
        # (see the "cannot pay" shedding loop below). Summed over many
        # people this reproduces the same 3.5%-a-year average the smooth
        # version was tuned against; no single person is ever a third of a
        # casualty.
        _lost = {}
        for t in sorted(self.household.employees):
            head = int(round(self.household.employees[t]))
            survivors = sum(1 for _ in range(head) if self.rng.random() >= ATTRITION)
            if head - survivors > 0:
                _lost[t] = head - survivors
            if survivors > 0:
                self.household.employees[t] = float(survivors)
            else:
                self.household.employees.pop(t)
        # AND SAY SO. Now that a death is a whole person rather than three
        # hundredths of one, it is a thing that HAPPENED, and it was happening
        # in complete silence. A break tester hired five scholars, stepped five
        # years, watched the payroll go five, four, three, three, two, and found
        # nothing in the log or the events to say why - so they reported it as
        # staff vanishing, which is exactly what it looks like from the chair.
        # The rate is right (measured at 0.825 survival over five years against
        # 0.837 expected, across forty seeds); the reporting was missing.
        if _lost:
            self.household.log.append((yr, "you lose %s to death and to better offers"
                             % ", ".join("%d %s%s" % (n, t, "" if n == 1 else "s")
                                         for t, n in sorted(_lost.items()))))
        self._resync_pools()
        # A HOUSEHOLD THAT CANNOT PAY ITS PEOPLE LETS THEM GO. This is the whole
        # answer to "you built it from nothing, so you must be able to rebuild
        # it": the thing that kept a ruined run frozen for two centuries was a
        # payroll it could not carry and never reduced. A run that fired its
        # staff, lived cheaply and started again earned 300 technologies; the
        # same run holding on to eleven people it could not pay earned 18.
        # TWO THINGS WERE WRONG WITH HOW THIS USED TO DECIDE, and a break tester
        # found both at once: they hired six smiths with two thirds of their
        # credit line still unused, stepped one year, and every one of the six
        # was gone, with nothing whatever in the log to say so.
        #
        # 1. The trigger was `capital < 0`, which is being overdrawn, not being
        #    unable to pay. A household with credit left borrows and makes
        #    payroll; that is what credit is for, and enforce_credit_limit
        #    already models the point where it runs out. Letting your staff go
        #    the first year you dip a denarius below zero, with the lender still
        #    willing, is not what an enterprise does.
        # 2. The gap it tried to close was measured with living_cost(), which
        #    INCLUDES the wage bill, so the deficit being closed was the payroll
        #    PLUS the founder's own food, rent and appearances. Firing people
        #    cannot buy your own dinner. Whenever base living exceeded revenue -
        #    which it does in every early game - the loop ran off the end of the
        #    staff list and emptied it. And the log line sat inside `if net >=
        #    0`, so the one case that always happened was the one case that said
        #    nothing at all.
        #
        # The honest rule is that your people are paid out of what is left after
        # everything else, INCLUDING what somebody will still lend you, and you
        # shed only the part of the payroll that will not cover.
        payroll = self.wage_bill()
        other = (self.upkeep() + (self.living_cost() - payroll)
                 + self.mine_operating_cost())
        # capital is negative in arrears; credit_limit() is how far into arrears
        # anyone will let you go, so this is what you can actually still spend.
        headroom = max(0.0, self.household.capital + self.credit_limit())
        can_pay = self.revenue() - other + headroom
        # NOT GATED BY A POLICY, and this is the one automatic thing that is not.
        # A policy switch is for something the game decides FOR you - who to
        # hire, what to mothball - and every one of those is yours to turn off.
        # People leaving a household that has no money and no credit to pay them
        # is not a decision the game is making on your behalf, it is the world
        # answering one you already made, the same as the arrears bleed below.
        # The `policy` reply says so in as many words now, because the tester
        # read its promise as covering this and was entitled to.
        if payroll > can_pay and self.household.employees:
            short = payroll - can_pay
            gone = 0.0
            # shed, dearest first, until the wages you are left with fit
            for t in sorted(self.household.employees, key=lambda t: -self.annual_wage(t)):
                if short <= 0:
                    break
                wage = self.annual_wage(t)
                if wage <= 0:
                    continue
                # A WHOLE PERSON, ROUNDED UP. `short / wage` is a quantity of
                # wages, not a quantity of people, and cutting that fraction
                # straight used to leave "0.3 smiths" still on the books,
                # still drawing 0.3 of a wage nobody had just said could be
                # paid. Rounding up sheds one whole person too many at worst,
                # which is the safe direction for a household that genuinely
                # cannot make payroll.
                cut = min(self.household.employees[t], math.ceil(short / wage - 1e-9))
                self.household.employees[t] -= cut
                short -= cut * wage
                gone += cut
                if self.household.employees[t] < 0.5:
                    self.household.employees.pop(t)
            self._resync_pools()
            # ALWAYS, not only when it worked. Losing the staff you paid to hire
            # is more consequential than any of the flavour events that do get
            # logged, and a player who is not told has to notice their own wage
            # bill hit zero to find out.
            if gone > 0.005:
                self.household.log.append((yr, "you cannot pay everyone: %.1f of your staff "
                                     "leave for work that pays" % gone))
        # NOT `capital > 0`. This is the same catch-22 auto_open_ventures was
        # already caught by and had fixed: a household in arrears could never
        # take on the people whose work is the only way out of arrears. And a
        # run that keeps a project going keeps a balance in the red almost
        # permanently, so the gate was not "you are ruined", it was "you are
        # building something". A Rome run traced for this comment sat at about
        # -5,000 against a credit line of 8,000 for five hundred years with a
        # clear surplus of 650 a year and hired NOBODY: zero scholars and zero
        # craftsmen in 600 AD, 387 technologies, no goal. Deep in arrears is
        # deep in arrears; the affordability arithmetic below - which already
        # subtracts living cost, upkeep and the wages you are carrying - is
        # what decides how many, and it correctly says nobody when there is
        # nothing spare.
        _hire_room = (self.household.capital >= 0
                      or -self.household.capital <= self.credit_limit() * 0.75)
        if (self.policy.get("auto_hire", not self.manual) and _hire_room):
            # Scaled by the SAME affordability figure staff_capacity() just
            # used for sc_cap/ar_cap (see the comment there): supervision-room
            # headroom is not a free six people, it is six people you still
            # have to pay for.
            extra = self.supervision_room() * self.household._staff_scale
            # THE SAME WALL hire() AND train() ENFORCE. This used to smooth
            # self.household.scholars toward sc_cap directly, mutating the pool itself
            # with no call anywhere near literate_capacity() - the wall a
            # player typing `hire scholar 12` was refused at 5.9, "ever, at
            # any price". A break tester turned auto_hire on, came back forty
            # years later to the same civilisation, and found 146.4 scholars:
            # one rulebook at the keyboard and a twenty-five-times-larger one
            # for the automation, for the identical number. See
            # literate_capacity()'s own docstring for the other half of this
            # fix - widening the wall enough that clamping to it here does not
            # simply strand every long civilisation run short of what the
            # tree actually asks for (the goal wants 25; building the
            # institutions staff_capacity() already credits widens this same
            # wall past that well before the goal is in reach).
            target_sc = min(sc_cap + extra * 0.35, self.literate_capacity("scholar"))
            desired_sc = self.household.scholars + (target_sc - self.household.scholars) * 0.18
            target_ar = ar_cap + extra
            desired_ar = self.household.artisans + (target_ar - self.household.artisans) * 0.22
            # Keep the per-trade books honest about the aggregate: staff taken on
            # for you are generic craftsmen and scribes, and that is all they are.
            craft = max(0.0, desired_ar - self.household.freedmen - self.household.slaves * 0.7)
            generic = self.household.employees.get("artisan", 0.0)
            specials = sum(v for t, v in self.household.employees.items()
                           if t not in ("artisan", "scholar") and trade_family(t) == "craft")
            # SPECIALISTS MUST NOT EAT THE GENERALISTS. The generic bucket was
            # the remainder after every taught trade had taken its share, so
            # once the top-up kept five specialist trades at two apiece the
            # artisans were squeezed to nothing - a play tester watched theirs
            # go 6.0 to 0.03 while scholars filled every place, and since
            # artisans are what supervise a concern, twenty-two concerns closed
            # and their net went from +8,010 a year to -3,027. A household of
            # nothing but specialists cannot keep its own doors open.
            #
            # PEOPLE ARE WHOLE. This was the other place "0.03 engineers"
            # actually came from: the smoothing above is a continuous
            # approach to a continuous target, by design, and writing that
            # target straight into `employees` handed a player a fractional
            # person every single year forever, never quite arriving.
            # _stochastic_round spends the fractional remainder as this
            # year's chance of the next whole hire, so the long-run average
            # this formula was tuned against is unchanged and every actual
            # year's headcount is an integer (see its own docstring).
            # THROUGH hire(), NOT AROUND IT. The user asked why this does not
            # simply call hire() and reuse the code, and the honest answer was
            # that there is no reason: it grew as a direct write to the pools
            # and every rule hire() enforces had to be re-enforced here by hand,
            # or silently was not. The literacy ceiling was the one that got
            # noticed (a player refused at 5.9 while this reached 146), and it
            # was fixed by duplicating the check rather than sharing the code,
            # which left the others. Measured, for four artisans: hire() takes
            # 1,000 denarii as a finder's fee and the first year in advance,
            # records it so the year is not billed twice, and bids that trade's
            # price up to 1.021. This took the same four people for nothing and
            # left the market at 1.000. The automation was cheaper than playing
            # by hand, which is exactly backwards from what `policy` promises.
            #
            # Routing through hire() makes all of that impossible by
            # construction rather than by vigilance: the advance, the household
            # room, the literacy wall, the price pressure and the refusals are
            # whatever hire() says they are, for player and optimizer alike. A
            # refusal here is not an error - it is the same wall a player hits -
            # so it is simply not acted on.
            def _grow_to(trade, want):
                have = self.household.employees.get(trade, 0.0)
                delta = self._stochastic_round(want) - have
                if delta >= 1.0:
                    self.hire(trade, int(delta))
                elif delta <= -1.0:
                    self.fire(trade, int(-delta))
            _grow_to("artisan", max(craft * 0.25, craft - specials))
            if desired_sc > 0:
                _grow_to("scholar", desired_sc)
            # REPLACE THE PEOPLE YOU LOSE, trade by trade. Attrition was eating
            # the taught trades (the engineers went from 1.9 to 0.3 over sixty
            # years) and nothing ever replaced them, because the top-up only knew
            # about the two generic buckets. A programme that trains the first
            # machinists in the world and then lets them die out has not trained
            # anybody.
            # FROM THE TRADES YOU TAUGHT, not from the keys that happen to be
            # left. A trade falls out of `employees` entirely once the last of
            # them drops below 0.05, and this loop only ever looked at the
            # keys - so the moment a taught trade went to nothing it stopped
            # being replaced, permanently. That is the leak behind a Rome run
            # that built 829 technologies and could not begin
            # precision_three_plate: not that machinists were never taught, but
            # that the last one died and the top-up had already forgotten they
            # existed.
            for t in sorted(set(self.household.employees) | set(self.household.trades_created)):
                if t in ("artisan", "scholar"):
                    continue
                have = self.household.employees.get(t, 0.0)
                want = max(have, 2.0 if t in self.household.trades_created else 0.0)
                short = want - have
                if short > 0.02 and self.household.capital > self.annual_wage(t) * 6:
                    self.household.employees[t] = have + short
                    self.household.capital -= short * self.annual_wage(t)
            self._resync_pools()
        # BUY A JOB WHEN A HANDFUL OF HANDS IS THE ONLY THING IN THE WAY.
        # Letting contracted craftsmen count toward a project's staff
        # requirement fixed the Norse deadlock for a person at a keyboard and
        # not at all for the optimizer, because nothing in the engine had ever
        # called commission(). A run that can see the wall, has the money, and
        # has no way to spend it on the wall is the same dead end wearing a
        # different hat.
        if self.policy.get("auto_commission", not self.manual):
            self.auto_commission_for_blocked()
        self.household.directors_extra += (di_cap - self.household.directors_extra) * 0.12 - self.household.directors_extra * ATTRITION
        self.household.artisans = max(0.0, self.household.artisans)
        self.household.scholars = max(0.0, self.household.scholars)
        self.household.directors_extra = max(0.0, self.household.directors_extra)
        # SAY IT WHEN IT CROSSES A WHOLE PERSON. A play tester noticed "10,175
        # founder-hours free this year (2,000 of your own, plus 4.5 deputies at
        # 1,800 hours each)" by accident, after playing for a century on the
        # assumption that their year was two thousand hours and would stay
        # that way. The single largest change to the resource the whole game
        # is built on had never announced itself.
        _whole = int(self.household.directors_extra)
        if _whole > int(getattr(self.household, "_said_deputies", 0)):
            self.household._said_deputies = _whole
            self.household.log.append((yr, "you now have %d deput%s directing work in "
                                 "your name: your year is %s hours instead of "
                                 "%s. They came with the institutions you built"
                             % (_whole, "y" if _whole == 1 else "ies",
                                "{:,.0f}".format(self.director_pool()),
                                "{:,.0f}".format(self.cfg["founder_hours_per_year"]))))

        # 2. money
        self.economy = self.economy_index()
        lc = self.living_cost()
        # THE YEAR YOU PAID FOR IN ADVANCE IS NOT BILLED AGAIN. `hire` takes a
        # finder's fee and the first year's wages up front, and living_cost()
        # carries the whole payroll, so a smith at 281 a year cost 566 in his
        # first year: the advance, then the identical year again at the next
        # step. A break tester found hire-then-fire in one turn burned the
        # advance for no work at all.
        prepaid = min(lc, self.household.wages_prepaid)
        lc -= prepaid
        self.household.wages_prepaid = 0.0
        self.living_cost_paid += lc
        mo = self.mine_operating_cost()
        self.household.mine_cost_paid += mo
        self.household.capital += self.revenue() - self.upkeep() - lc - mo
        # A mine you cannot pay for is a mine you stop working. Without this the
        # opex accrued for ever against a bankrupt enterprise: the England run
        # sank a large mine, lost its revenue and then ran three centuries at
        # minus four million denarii, unable to afford anything at all, which
        # the log reported as being "blocked" on a treadle lathe.
        if self.household.capital < 0 and self.mine_capacity and self.policy.get("auto_mothball", True):
            self.mothball_mines()
        # A CONCERN NEEDS SOMEBODY WATCHING IT EVERY YEAR, not only on the day
        # you open it. `open` refused without supervisors and then nothing ever
        # looked again, so a break tester hired five craftsmen, opened eleven
        # concerns in one turn, fired all six people, and watched net income
        # RISE - "EMPLOY: 0 people" with seventeen concerns running, and the
        # same loom still paying 435 a year in 1800 with nobody employed,
        # straight through the Black Death.
        # THE OTHER HALF OF THE SAME RULE, and applied FIRST: staff hired or
        # taught this same year (the block just above) should get first claim
        # on reclaiming what attrition shut, before anything is judged still
        # short and closed again. See reopen_restaffed_ventures's own
        # docstring for why this is not gated by auto_open - three
        # playtesters spent most of a run on the treadmill this closes.
        self.reopen_restaffed_ventures(yr)
        self.close_unstaffed_ventures(yr)
        # Open what plainly pays for itself, before the books are struck: a
        # concern you opened this year is a concern that earns this year.
        if self.policy.get("auto_open", not self.manual):
            self.auto_open_ventures()
        self.charge_interest(yr)
        if self.policy.get("auto_shed", True):
            self.shed_loss_makers(yr)
        self.warn_near_the_limit(yr)
        self.enforce_credit_limit(yr)

        # INSOLVENCY. A playtester ran to minus 4.12 million denarii over eighty
        # years and nothing whatever happened: no event, no block, no attrition.
        # That is not a hard game made easy, it is an accounting fiction, and it
        # quietly made every cost in the model optional.
        #
        # The consequence is deliberately the realistic one rather than a
        # dramatic one. Nobody arrests you for debt. What happens is that people
        # you cannot pay stop turning up, and nobody will extend you credit for
        # something new while you are in arrears.
        if self.household.capital < 0:
            # BEING IN DEBT IS NOT THE SAME AS BEING INSOLVENT. This counted a
            # year of arrears for every year capital was below zero, whatever
            # the household was earning - so a Rome run with revenue of 1,006
            # against 470 of living costs, paying its debt down at 522 a year,
            # was still "in arrears 183 years" and still refused permission to
            # start anything, which is what kept it from ever climbing out. A
            # household running a surplus is paying its creditors, and nobody
            # calls that insolvency; what the counter is for is the household
            # whose income does not cover its costs.
            _net = (self.revenue() - self.upkeep() - self.living_cost()
                    - self.mine_operating_cost())
            if _net > 0:
                self.household.insolvent_years = 0
            else:
                self.household.insolvent_years = getattr(self.household, "insolvent_years", 0) + 1
            floor = -max(4000.0, self.revenue() * 2.0)
            if self.household.capital < floor and self.household.insolvent_years >= 3:
                # wages unpaid: freedmen leave first, they are free to
                # A FLOOR, because the first version was a doom loop. Staff bled
                # without limit, so fewer people earned less, which deepened the
                # arrears, which bled more people. One Norse run sat insolvent
                # for 495 years with 2.9 artisans left, unable to recover and
                # unable to end. Insolvency should cost you your expansion, not
                # trap you in a state you can never leave: a household that has
                # shed everything also stops paying for it, and can climb back.
                bleed = min(0.15, 0.04 * self.household.insolvent_years)
                self.household.artisans = max(3.0, self.household.artisans * (1.0 - bleed))
                self.household.scholars = max(1.0, self.household.scholars * (1.0 - bleed * 0.6))
                if self.household.insolvent_years in (3, 6, 12, 25):
                    self.household.log.append((yr, "IN ARREARS for %d years: staff are leaving "
                                         "because you cannot pay them" % self.household.insolvent_years))
                # ABANDONMENT, and this is what makes insolvency survivable.
                # The failed Norse run carried 3,920 denarii of upkeep against
                # 3,134 of revenue: permanently underwater, floored at three
                # artisans, simulating 495 years of nothing and reporting it as
                # "ran out of horizon". An enterprise that cannot maintain its
                # works does not pay for them for five centuries. It lets them
                # go, and the buildings fall down. You lose what they gave you
                # and can rebuild later, which is a real cost and a real way out.
                net = (self.revenue() - self.upkeep() - self.living_cost()
                       - self.mine_operating_cost())
                # ONLY WORKS THAT COST MORE THAN THEY RETURN, and only if you let
                # it happen at all. Both halves were wrong and a tester called the
                # result "an unrecoverable softlock", correctly: the loop ran
                # until the books balanced rather than until shedding stopped
                # helping, so once the genuine loss-makers were gone it went on
                # to destroy eleven works earning 2,700 a year against 330 of
                # upkeep, each one making the deficit worse, for ever. And it did
                # it whether or not auto_shed was switched off, in a game whose
                # own help says "every one of them is a switch you control".
                if net < 0 and self.policy.get("auto_shed", True):
                    burden = sorted((k for k in self.household.done
                                     if self.nodes[k]["up"] > self.nodes[k]["rev"]
                                     and k not in self.household.granted
                                     and not self.never_abandon(k)),
                                    key=lambda k: (self.nodes[k]["rev"] - self.nodes[k]["up"]))
                    shed = []
                    for k in burden:
                        if net >= 0:
                            break
                        n = self.nodes[k]
                        net += n["up"] - n["rev"]
                        # CLOSE IT, DO NOT UNLEARN IT - and above all do not do
                        # both. Discarding from `done` while adding to
                        # `mothballed` produced a state no verb could clear: a
                        # play tester lost precision_three_plate to a sack, and
                        # `start` sent them to `restore`, `restore` said they no
                        # longer knew how, `open` said they had not built it and
                        # `mothball` said there was nothing to shut. That node
                        # gates the whole precision branch, so `available` read
                        # "0 startable now" for a hundred and eighty years while
                        # they sat on a quarter of a billion denarii. The same
                        # pair of lines was fixed in enforce_credit_limit and in
                        # shed_loss_makers and survived here.
                        self.household.operating.discard(k)
                        self.household.mothballed.add(k)   # you can buy it back
                        shed.append(k)
                    if shed:
                        # NAME THEM, for the same reason as shed_loss_makers and
                        # the creditors' seizure below: a bare count does not
                        # tell a player what they lost or why it later
                        # reappeared mothballed rather than gone for good.
                        self.household.log.append((yr, "ABANDONED %d works you could no longer "
                                             "maintain; they have fallen into disrepair: %s"
                                             % (len(shed), ", ".join(shed))))
        else:
            self.household.insolvent_years = 0
        # A standing workforce policy, and ONLY when the optimizer is playing.
        #
        # This used to run in manual mode too, so a player who never issued a
        # buy command watched `slaves` climb on its own with no prompt and no log
        # line. A tester caught it and put the objection better than I can: the
        # game's own justification for modelling slavery at all is that "a model
        # that hides it lies about the cost of everything", and then it was
        # hiding the acquisition. Buying people on someone's behalf without
        # telling them is the worst version of that.
        if self.policy.get("auto_buy_people", False):
            if self.household.capital > 6000 and self.household.artisans < 12 and self.running("workshop_first"):
                got = self.buy_slaves(min(6, int(self.household.capital // 1500)))
                if got:
                    self.household.log.append((yr, "bought %d people for the workshop" % got))
        if self.policy.get("auto_manumit", not self.manual) and self.household.slaves:
            if self.rng.random() < 0.25:
                freed = self.manumit(max(1, self.household.slaves // 4))
                if freed:
                    self.household.log.append((yr, "freed %d people" % freed))
        # currency debasement and war damage now come from the civilization's
        # own hazard list, not from Rome's dates baked into the engine
        if self.output_factor < 1.0:
            # A STATE THAT CAN DEFEND ITSELF REBUILDS FASTER. This used to be
            # a flat rate no matter what the founder had done about the war -
            # a civilization that built the whole military branch and one
            # that ignored it recovered from the SAME war at the SAME speed,
            # which is the finding that started this change: measured against
            # a founder with none of the tree's 111+ military nodes, nothing
            # about the state's fortunes moved at all. military_leverage() is
            # the same count update_protection() and
            # hazard_relief("output_factor") (society.py) already read off
            # self.household.done; at full leverage the recovery rate doubles, so an
            # armed empire is back to normal trade in roughly half the years
            # an unarmed one takes, not instantly - the war still happened
            # and the years it cost are not given back.
            self.output_factor = min(1.0, self.output_factor
                                     + 0.006 * (1.0 + self.military_leverage()))
        # Population and the wage premium it drives recover/build in on their
        # own clock too, and must run before this year's shocks get a chance
        # to add a fresh deficit - see _demographic_recovery for why.
        self._demographic_recovery(yr)
        # Literacy and taught-trade naturalisation move on the same kind of
        # slow, generational clock as population above - see
        # SocietyMixin.advance_society (society.py) for the mechanism. Run
        # here, before 4a2's auto_train reads literate_capacity() below, so
        # a year's schooling gain is visible to this same year's teaching
        # decisions rather than lagging a full step behind them.
        self.advance_society(yr)
        # 2c. THRESHOLD GOALS. A node carrying a `win_condition` (see
        # data.py's WIN_CONDITION_LABELS and tech_tree.json's own goals
        # using one) is never built - start_reason refuses it outright -
        # it completes itself the moment a live measurement crosses its
        # target. Checked here, right after the literacy/trade growth this
        # same measurement usually depends on has moved for the year, so a
        # threshold crossed this year is seen this year rather than lagging
        # a full step behind it.
        self._check_win_conditions(yr)

        # 3. dated shocks
        if self.events:
            self._shocks(yr)
            if self.dead_reason:
                return

        # 4a2. TEACH THE TRADES THIS SOCIETY DOES NOT HAVE. The optimizer has to
        #      do this for itself or half the tree is unreachable; a player does
        #      it with `train`, or turns this on.
        if self.policy.get("auto_train", not self.manual):
            want = {}
            # LOCAL, PER-YEAR MEMO for market_supply()/trade_available().
            # Both are pure functions of staff and trades_created, which this
            # whole block only READS - train(), below, adds to trades_created,
            # but that happens once, at the very end, after every use of these
            # memos - so the same handful of distinct trade names (maybe
            # thirty) get recomputed from scratch once per NODE that lists
            # them in `lab`, and hundreds of nodes across the tree share the
            # same absent trade (machinist, engineer, ...). This dict is a
            # plain local, created fresh every call and discarded when the
            # block ends, so it needs no invalidation logic at all: nothing
            # outside this block ever reads it, so it cannot go stale.
            _ms_memo, _ta_memo = {}, {}
            def _market_supply(t):
                v = _ms_memo.get(t)
                if v is None:
                    v = _ms_memo[t] = self.market_supply(t)
                return v
            def _trade_avail(t):
                v = _ta_memo.get(t)
                if v is None:
                    v = _ta_memo[t] = self.trade_available(t)
                return v
            # Anything already in hand that has lost its trade comes FIRST: those
            # projects are burning a slot and will be halted if nobody turns up.
            for k in self.household.active:
                for t in self.nodes[k]["lab"]:
                    if _market_supply(t) <= 0.0:
                        want[t] = want.get(t, 0) + 500
            # WORK THE PLAYER COULD START TODAY, not the whole tree. The old
            # test was "direct prerequisites satisfied", which is not "wanted":
            # it looked past cost, staff, state approval and every OTHER trade
            # a node needs, so it walked deep into the order training engineers,
            # then chemists, machinists and opticians, with no active project
            # asking for any of them. Its own description promises "when a
            # project needs them", and a project three tiers away with money
            # you do not have is not a project you need anything for yet.
            # ignore_trade asks the one question that answers that: if this
            # trade existed, would everything ELSE already let it start?
            # EXISTING IS NOT THE SAME AS ANYBODY BEING LEFT. A trade you
            # taught stays "available" for ever, so once the last machinist
            # had died of old age this loop skipped every node that needed
            # one and nobody was ever taught again. A Rome run built 829
            # technologies, sat on 31.9M denarii, and could not begin
            # precision_three_plate - which gates master_screw, the screw
            # lathe and the entire precision branch, ninety-nine of the
            # hundred and forty-six nodes on the road to the goal. This is
            # the same distinction start_reason learned an hour earlier.
            # Hoisted out of the loop below: it closes only over `self` and
            # the memos above, never over the loop variable `k`, so defining
            # it fresh on every one of ~2,800 iterations bought nothing.
            #
            # _gone(t) ITSELF IS NOW MEMOIZED TOO (_gone_memo), for the same
            # reason _market_supply/_trade_avail already are: it reads only
            # _trade_avail(t), _market_supply(t) and
            # self._trade_headcount_pending(t), and the last of those
            # (labour.py) reads only self.household.training and self.household.employees -
            # neither mutated anywhere in this block; train(), at the very
            # end of it, is the only thing that changes either, exactly as
            # the comment above already established for the other two. So
            # _gone(t) is just as pure a function of (staff, trades_created)
            # across this whole block as they are, and is safe to cache the
            # same way.
            #
            # That matters because this used to be a plain function called
            # through `any(_gone(t) for t in n["lab"])`, and the per-trade
            # RESULT (not just its two cheap sub-memos) was never cached -
            # so recomputing it, for the same handful of distinct trade
            # names, cost one Python function call for EVERY ONE of the
            # ~2,800 nodes in `order` that names them, even after the first
            # node had already worked out the answer. Profiling 150 years
            # found the `any()` generator alone at 895,244 calls / 0.83s
            # cumulative. _is_gone below answers the identical question,
            # through the identical `any()` (so a node whose FIRST lab
            # trade is already known gone, or one that fails
            # start_reason() right after, costs exactly what it always
            # did - no extra work done on the strength of a guess that it
            # would be needed), but every trade's verdict is computed once
            # and reused for every later node that names it, instead of
            # recomputing the same two calls from scratch each time.
            _gone_memo = {}
            def _is_gone(t):
                v = _gone_memo.get(t)
                if v is None:
                    v = _gone_memo[t] = (
                        not _trade_avail(t)
                        or (_market_supply(t) <= 0.0
                            and self._trade_headcount_pending(t) <= 0.0))
                return v
            for k in self.order:
                if k in self.household.done or k in self.household.active:
                    continue
                n = self.nodes[k]
                if not any(_is_gone(t) for t in n["lab"]):
                    continue
                if not self.start_reason(k, ignore_trade=True)[0]:
                    continue
                for t in n["lab"]:
                    if _is_gone(t):
                        want[t] = want.get(t, 0) + 1
            # NOT EVERY YEAR. Teaching two of a trade costs about nine hundred
            # of the founder's two thousand hours plus their keep, and once
            # re-teaching a lost trade was possible at all the loop did it
            # continuously: three Rome seeds fell from 829, 858 and 1,257
            # technologies to 229, 56 and 188, the whole difference going into
            # a teaching treadmill. A trade is worth restoring; it is not worth
            # half of every year for ever.
            _taught = self.household.last_taught
            want = {t: v for t, v in want.items()
                    if yr - _taught.get(t, -999) >= self.RETEACH_EVERY}
            # AND ONLY IF YOU CAN PAY THEM. train() checked hours, literacy and
            # household room and never once looked at money - so a Rome
            # household earning 1,232 a year taught itself two engineers at
            # 625 each, and every year after that its whole income went on
            # their wages. That is the poverty trap three separate testers
            # described from three directions: "auto_train bought me chemists,
            # engineers, machinists and opticians I had no work for", "-6,900
            # denarii in three steps", and a run that sat at 144 technologies
            # from 125 AD to 300. A trade you cannot pay for is not a trade you
            # have; it is a wage bill that stops you building anything.
            #
            # Two standards, because the two cases are not alike. A trade a
            # project ALREADY IN HAND is waiting on (scored 500 above) is worth
            # borrowing against: that work is paid for and stops without it.
            # A trade for something you might start one day has to come out of
            # what you are actually clearing.
            _spare_tr = self.revenue() - self.upkeep() - self.living_cost()
            for t, _score in sorted(want.items(), key=lambda kv: (-kv[1], kv[0]))[:1]:
                _wages = 2.0 * self.annual_wage(t)
                _budget = (max(0.0, _spare_tr) + max(0.0, self.household.capital) * 0.10
                           if _score >= 500 else max(0.0, _spare_tr) * 0.5)
                if _wages > _budget:
                    continue
                _first = t not in self.household.trades_created
                ok, _msg = self.train(t, 2)
                # THE COOLDOWN IS ON TEACHING, NOT ON TRYING. Recording the
                # attempt meant a refusal - no room in the household, no hours
                # left, nobody to teach from - burned the trade's whole
                # twenty-five years, so the run went on needing machinists and
                # never asked again.
                if ok:
                    _taught[t] = yr
                    self.household.log.append((yr, "you begin teaching the first %ss this "
                                         "world has ever had" % t if _first else
                                     "the last %ss are gone; you begin teaching "
                                     "more" % t))

        # 4a(ii). THE STANDING "WORK" DIRECTIVE. `work` (protocol.py) sells
        # hours for wages the moment a player types it; `allocate` lets them
        # say "sell N hours a year this way" ONCE and have it happen every
        # year without retyping it, the same standing-instruction idea as
        # the project directives just below. Run BEFORE `pool` is struck so
        # director_hours_committed() (which counts wage hours already sold
        # this year) sees it, exactly as it would if the player had typed
        # `work` by hand a moment ago.
        #
        # TOPPED UP, NOT DOUBLED. A player who already called `work` by hand
        # earlier this same turn has already sold some of the hours this
        # directive wants; this only sells the remainder, never the whole
        # directive again on top of what was already sold.
        _wd = self.household.hour_allocations.get("work")
        if _wd and _wd > 0 and self.household.work_trade:
            _already = getattr(self.household, "wage_hours_this_year", 0.0)
            _want = max(0.0, _wd - _already)
            if _want > 0.5:
                _room = max(0.0, self.director_pool() - self.director_hours_committed())
                _take = min(_want, _room)
                _got = 0.0
                if _take > 0.5:
                    _pay, _werr = self.work_for_wages(self.household.work_trade, _take)
                    # pay > 0 with an error is a WARNING (a bad trade, or
                    # starving an active project of its last hours), not a
                    # refusal - see work_for_wages's own docstring. The sale
                    # happened either way; only a genuine refusal (pay <= 0)
                    # means none of it landed.
                    if _pay > 0 or not _werr:
                        _got = _take
                # SAY SO, THE SAME WAY AN UNHONOURED PROJECT DIRECTIVE DOES,
                # BELOW. A standing instruction nobody is told failed is the
                # same unfairness either way: the founder-hours it asked for
                # either went unsold or went somewhere the player never
                # chose.
                if _wd - (_already + _got) > 1.0:
                    self.household.log.append((yr, "DIRECTED HOURS UNUSED: your standing "
                                         "order to sell %s hours a year as a "
                                         "%s only managed %s this year - %s. "
                                         "'allocate' changes or clears it"
                                     % ("{:,.0f}".format(_wd), self.household.work_trade,
                                        "{:,.0f}".format(_already + _got),
                                        "no more of your own hours were left "
                                        "to sell once your projects and "
                                        "training had theirs"
                                        if _room < _want else
                                        "nobody here will pay for that trade "
                                        "any longer" )))

        # 4b. start new projects
        pool = max(0.0, self.director_pool() - self.director_hours_committed())
        hired_left = self.hired_cap()
        # MANUAL MODE STOPS HERE. This loop is "the optimizer": it walks
        # `order` and starts whatever it judges best, which is exactly the
        # behaviour a free-choice player must NOT get. The old `play` command
        # let you type a node id, but that only did `order.remove/insert(0)`
        # a few lines above this loop's own input; the loop then ran anyway
        # and started other things you never asked for. `self.manual` cuts
        # that off at the root: nothing is ever added to `self.household.active` here,
        # so the only way anything starts is start_project(), called by a
        # human or a script. Everything below this block (materials, staff,
        # money, hazards, the calendar) is untouched by `manual` and keeps
        # running exactly as before.
        if not self.manual and yr >= self.household.credit_frozen_until:
            # More directors means more things in hand at once, and a big trained staff
            # lets routine work proceed without the founder watching it.
            # How many things can be in hand at once. I tried doubling this on
            # the theory that money is now the real constraint and attention need
            # not stand in for a budget. It made every civilization worse,
            # including Rome, from 33% of runs reaching the transistor to none:
            # more projects in hand divide the same purse into smaller annual
            # payments, so everything crawls and nothing finishes. Spreading a
            # fixed budget across more work is not more work. Left as it was.
            max_active = int(2 + self.director_pool() / 2000.0
                             + self.household.scholars / 12.0 + self.household.artisans / 25.0)
            # EARN A LIVING FIRST. Now that a project must actually be paid for,
            # a founder who arrives with 400 denarii and walks the goal-ordered
            # list starves: every human tester worked this out for themselves
            # within a few turns and went hunting for the cheap revenue nodes,
            # and the optimizer had no such instinct. When the surplus is thin,
            # prefer whatever pays best for what it costs; the goal order resumes
            # the moment there is money to pursue it with.
            fixed0 = self.upkeep() + self.living_cost() + self.mine_operating_cost()
            candidates = self.order
            if self.revenue() - fixed0 < max(400.0, fixed0 * 0.25):
                earners = [k for k in self.order
                           if self.nodes[k]["rev"] - self.nodes[k]["up"] > 0]
                earners.sort(key=lambda k: self.project_cost(k)
                             / max(1.0, self.nodes[k]["rev"] - self.nodes[k]["up"]))
                # `set(earners)` HOISTED OUT OF THE COMPREHENSION. Written
                # inline as `if k not in set(earners)`, this rebuilt the set
                # from scratch on every one of the 2,833 iterations of the
                # walk over self.order - one throwaway set per node, an
                # O(|order| x |earners|) rebuild for what a single set
                # covers in O(|order|). Profiling a 300-year single-seed run
                # found this one line costing 0.81s of self time over just
                # 21 calls - a tight-money branch, but each call did the
                # equivalent of an extra multi-hundred-thousand-item pass.
                # See PERFORMANCE.md.
                _earner_set = set(earners)
                candidates = earners + [k for k in self.order if k not in _earner_set]
            # INCREMENTAL COUNT, NOT A SET REBUILT PER ITERATION. Written as
            # `len(self.household.active) - len(self.household.bountied & set(self.household.active))`
            # inside the loop below, this rebuilt `set(self.household.active)` from
            # scratch on every one of the 2,849 iterations of `candidates` -
            # the identical mistake `_earner_set` (above) had already been
            # fixed for, 30 lines earlier in this same function. Unlike
            # `earners`, `self.household.active` IS mutated inside this loop (a normal
            # start at the bottom, or post_bounty() below, which adds to both
            # `self.household.active` and `self.household.bountied` at once), so the fix cannot
            # be "hoist one set outside the loop" - it has to track the two
            # mutations as they happen instead:
            #   - post_bounty(k) succeeding adds k to self.household.active AND to
            #     self.household.bountied together, so a bountied project never counts
            #     against max_active: _non_bountied_active is left unchanged.
            #   - a normal start only adds k to self.household.active, so
            #     _non_bountied_active goes up by one.
            # Nothing else in this loop's body (can_start, project_cost,
            # funding_capacity, committed_spend, bounty_eligible) touches
            # self.household.active or self.household.bountied - checked in projects.py and
            # economy.py - so these two increments are the only places the
            # tracked count can move, and it is computed once up front
            # (O(active), not O(order)) rather than every iteration.
            _non_bountied_active = len(self.household.active) - len(self.household.bountied & set(self.household.active))
            for k in candidates:
                if _non_bountied_active >= max_active:
                    break
                if not self.can_start(k):
                    continue
                n = self.nodes[k]
                # do not start something we cannot plausibly fund this decade.
                # material_cost_factor is geography.json's contribution: a
                # located material (mat_gutta_percha and the like) costs more
                # or less to reach depending on how far THIS civ actually is
                # from it, not on Rome's distance to it.
                # Do not begin what you cannot pay for. This used to allow three
                # times your capital plus six years of GROSS revenue, which was
                # harmless while the money was notional and the bill was quietly
                # forgiven at completion. Now that the bill has to be paid, the
                # same heuristic commits the household to more than it can ever
                # fund, the creditors halt everything, and the spend is lost.
                # INTEREST IS A FIXED COST, and leaving it out is how a
                # household in arrears decides it has a surplus. A Rome run
                # paying 552 a year of interest computed its five years of
                # headroom as though that money did not exist, committed
                # against it, and went from -369 to -7,827 in twenty-five
                # years - then bled for four centuries. Every other net in this
                # program was taught to count arrears; this one was missed
                # because it is not a net, it is a budget.
                #
                # funding_capacity()/committed_spend() (economy.py), NOT A
                # SECOND COPY OF THIS FORMULA. This heuristic is where the
                # formula was first worked out; it has since been factored
                # out so the player-facing aggregate warning in `start`
                # (protocol.py) answers the identical question with the
                # identical number, rather than risking the two quietly
                # drifting apart.
                room = self.funding_capacity() - self.committed_spend()
                if self.project_cost(k) > room:
                    continue
                if k in self.bounty_set and self.bounty_eligible(k) and self.post_bounty(k):
                    # post_bounty() just added k to both self.household.active and
                    # self.household.bountied - the count of NON-bountied active
                    # projects is unchanged.
                    continue
                # lab_left starts full here too, for the same reason
                # start_project (projects.py) sets it at creation rather than
                # leaving lab_year_draw to guess it from ph_left the first
                # time it runs - see the comment there.
                self.household.active[k] = dict(ph_left=float(n["ph"]), yrs=0.0, spent=0.0,
                                      cost_left=self.project_cost(k),
                                      lab_left=dict(n["lab"]))
                _non_bountied_active += 1

        # 4c. materials. Buy the woodland and dig the beds BEFORE the shortage
        #     bites, which is what a competent manager does and what the old
        #     model never had to think about at all.
        self.commission_mines()
        thr = self.resource_throttle()
        # THE GATE WAS THE DEADLOCK. `capital > 3000` was meant to stop this
        # spending a poor household's last coin, and instead it made charcoal
        # a wall nobody in arrears could ever climb: no woodland, so the
        # furnaces run at a fraction, so nothing is built, so no money, so
        # still no woodland. An England run measured 521 charcoal-short years
        # out of 700, ended on 31 technologies with 71 hectares of coppice and
        # -6,332 in hand, and settled its debts twenty-eight times.
        #
        # Coppice is the cheapest thing in the tree and the one that decides
        # whether a furnace runs at all, so what it is really gated on is
        # whether you can raise the price of some, which is what
        # spending_power says. Below that the branch does nothing anyway,
        # because buy_forest refuses what you cannot pay for.
        _can_raise = self.spending_power("buy")
        if (thr < 0.9 and _can_raise > self.FOREST_COST_PER_HA * self.price_index
                and (self.policy.get("auto_mine", not self.manual)
                     or self.policy.get("auto_forest", not self.manual))):
            # Charcoal is GROWN, so the answer is woodland. Everything else in
            # this list is DUG, so the answer is a mine, and the old model had
            # no answer at all for coal: the binding constraint fell through
            # both branches and the run simply sat throttled. That is why coal
            # showed 1,669 shortage-years in a 395 year run.
            if self.household.binding == "charcoal":
                if self.policy.get("auto_forest", not self.manual):
                    # SIZED FROM THE SHORTFALL, like the mine branch below,
                    # rather than from a flat share of cash. A tenth of a
                    # denarius of capital bought a ten-thousandth of a hectare
                    # while the demand was measured in hundreds of tonnes.
                    _need_t = (self.annual_material_demand().get("charcoal_kg", 0.0)
                               / 1000.0) - self.household.forest_ha * self.CHARCOAL_PER_HA
                    _want_ha = max(0.0, _need_t) / max(self.CHARCOAL_PER_HA, 1e-9)
                    _afford_ha = (_can_raise * 0.35
                                  / (self.FOREST_COST_PER_HA * self.price_index))
                    self.buy_forest(min(400.0, _want_ha, _afford_ha))
            elif (self.household.binding in self.MINE_CAPEX_PER_T_YR
                    and self.policy.get("auto_mine", not self.manual)):
                # Size the mine from ALL the material keys that feed this
                # bucket, not one of them. The throttle counted iron ore AND
                # iron bar against "iron"; the investment response looked only
                # at iron bar. A run needing 10,330 tonnes of ore a year sank a
                # mine sized for the 13 tonnes of bar, stayed throttled for
                # centuries, and ended with its capital untouched.
                dem = self.annual_material_demand()
                # DERIVED FROM MATERIAL_CHECKS, not a second hand-kept copy of
                # it. This was a literal dict, and the moment copper wire,
                # drawn wire and gold were added to MATERIAL_CHECKS - so that
                # 36 electrical nodes and the central bank's thousand
                # kilograms could be throttled at all - a Rome run died with
                # KeyError: 'gold' the first year gold was the binding
                # material. Two lists of the same thing is one list too many,
                # and the regression suite could not catch it because no check
                # runs a long enough optimizer game to make gold bind.
                # sorted(), because this feeds a float sum.
                keys = tuple(sorted(kk for kk, (bucket, _tag)
                                    in self.MATERIAL_CHECKS.items()
                                    if bucket == self.household.binding))
                short = sum(dem.get(kk, 0.0) for kk in keys)
                want = max(0.0, short - self.mine_capacity.get(self.household.binding, 0.0))
                self.open_mine(self.household.binding, min(want, self.household.capital * 0.25
                                                 / max(1.0, self.MINE_CAPEX_PER_T_YR[self.household.binding])))
                # Iron and the base metals are smelted with charcoal, so the
                # ore is only half the answer.
                if self.household.binding in ("iron", "copper", "lead"):
                    self.buy_forest(min(200.0, self.household.capital / 1800.0))
            elif (self.household.binding == "saltpetre"
                    and self.policy.get("auto_mine", not self.manual)):
                # GATED, like every other automatic purchase. This branch sat
                # outside the policy check and took five per cent of a manual
                # player's capital every year they were short of nitre,
                # without a line in the log and without anything they typed.
                # A FLAT CEILING, AND IT IS NOT AN OVERSIGHT. Sizing this to
                # the measured shortfall the way the mine branch above does
                # is the obvious symmetry, it was tried, and it measured
                # WORSE on every count: Rome's saltpetre shortage went from
                # 277 run-years to 678, its reputation from 99 to 31, and its
                # first blocked node regressed from point_contact_transistor -
                # the last step of the whole programme - back to
                # atomic_theory, which it had cleared in its third century.
                # Spending a quarter of capital a year against a shortfall
                # that beds cannot close at any affordable scale starves
                # everything else, and in a household that falls into arrears
                # the interest then pins it there. Two thousand denarii a year
                # is what leaves the rest of the programme funded.
                #
                # The shortage is real and unresolved; more money is not the
                # answer to it, and this comment is here so the next person to
                # notice the asymmetry does not spend the afternoon I did.
                spend = min(self.household.capital * 0.05, 2000)
                self.household.capital -= spend
                self.household.nitre_bed_m2 += spend / self.NITRE_COST_PER_M2
                self.household.log.append((yr, "laid down %d square metres of nitre bed "
                                     "for %d denarii (auto_mine)"
                                 % (spend / self.NITRE_COST_PER_M2, spend)))
        if thr < 0.6 and self.household.binding:
            # SAY WHAT TO DO ABOUT IT. A play tester read "SHORT OF SALTPETRE:
            # work at 5% of plan" for thirty years and could not find out what
            # saltpetre was for, who wanted it, or what would fix it. A number
            # that low with no remedy attached reads as the game being stuck.
            self.household.log.append((yr, "SHORT OF %s: work running at %d%% of plan. %s"
                             % (self.household.binding.upper(), thr * 100,
                                self.shortage_remedy(self.household.binding))))

        # 5. progress. Director hours go to the HIGHEST-PRIORITY active projects
        #    first, not spread evenly: a director who gives every project equal
        #    attention finishes nothing, which is a real failure mode but not the
        #    one we are trying to model here.
        #
        # ONLY THE HANDFUL OF KEYS active_sorted ACTUALLY NEEDS, NOT EVERY
        # NODE IN THE TREE. This used to be a bare
        # `{k: i for i, k in enumerate(self.order)}` - a fresh 2,849-entry
        # dict built from scratch every single year to answer `rank.get(k,
        # 9999)` for the at most a few dozen keys in self.household.active. Nothing
        # below reads `rank` for any node NOT in self.household.active (checked: its
        # only other use is the `_pool_rank` loop variable a few lines
        # further down, an unrelated name), so recording a position for
        # every other one of the ~2,849 nodes was pure waste - 0.64ms/year
        # of pure self time with nothing under it, since dict-comprehension
        # and enumerate are both C-level with no further calls to profile.
        # This still walks self.order and cannot skip any of it in the
        # worst case (an active key can be anywhere in `order`), so it is
        # not a complexity win - but it stops paying for ~2,849 dict
        # insertions when only a few dozen are ever read, and exits the
        # walk the moment every active key's position has been found
        # (start_project, in projects.py, moves a project to the FRONT of
        # `order` the instant a human starts it by hand, so active keys
        # skew early there in practice, though the automated 4b loop above
        # does not reorder `order` and gives no such guarantee - the early
        # exit is a bonus, not a requirement of correctness). Recomputed
        # fresh every call, exactly as before: no cache, no staleness risk.
        _active_left = set(self.household.active)
        rank = {}
        if _active_left:
            for i, k in enumerate(self.order):
                if k in _active_left:
                    rank[k] = i
                    _active_left.discard(k)
                    if not _active_left:
                        break
        # A STANDING ALLOCATION IS A PROMISE, NOT A PRIORITY BID. Without
        # this, a project the player explicitly told `allocate` to give 500
        # hours a year could still be starved by three higher-`order`
        # undirected projects taking the whole pool first - the exact
        # opposite of what asking for an explicit split means. Every project
        # the player has put a standing instruction on is moved to the
        # FRONT of the queue (still ordered among themselves by the usual
        # priority, so two directed projects do not disagree about which of
        # them goes first); everything without one shares whatever is left
        # exactly as it always has, by the same `order`-based priority. A
        # player who never calls `allocate` has an empty hour_allocations,
        # every project sorts into the same single undirected bucket it
        # always did, and this line changes nothing for them.
        active_sorted = sorted(
            self.household.active,
            key=lambda k: (0 if self.household.hour_allocations.get(k, 0.0) > 0 else 1,
                           rank.get(k, 9999)))
        remaining = pool
        self.household.trade_hours_used = {}
        # Summed as the loop runs, not re-read from self.household.active afterwards,
        # because a project that completes THIS year is popped from
        # self.household.active before we would get to it. See the hours_this_year
        # summary this feeds, below the loop.
        hours_effective_total = 0.0
        # NAMED, NOT JUST STORED ON THE PROJECT. `why_underfunded` (set below,
        # in the arrears branch) answered "why is this stalled" when a player
        # thought to ask `why` or `portfolio` - but a Rome playtester lost
        # several turns of confusion before finding it, and wrote that the
        # consequence "isn't obvious from any single screen... reads more
        # like flavor than a mechanical warning". Founder-hours are the one
        # resource that never banks: a year of them lost to arrears and never
        # announced is the least fair thing a status screen can leave out.
        # Collected here and logged once, after the loop, so a step that
        # starves three projects at once gets one clear line, not three.
        _arrears_hours_lost = []
        # AN ALLOCATION THE PLAYER EXPLICITLY ASKED FOR, AND DID NOT GET.
        # hour_allocations is a promise the player made about their OWN one
        # resource that never banks; silently handing back less than it
        # asked for - because the project's own pace, its trade, or its
        # money was the real ceiling, not the founder's hours - is the same
        # unfairness the arrears line above exists to stop, aimed at a
        # player who took the extra step of directing their hours on
        # purpose. Collected here, per project, and logged once below.
        _directed_hours_unused = []
        # WHY A PROJECT IS GETTING THE SHARE IT IS GETTING, STORED HERE AND
        # NOWHERE ELSE. A player who had already won the game asked for
        # exactly this: "this project is receiving 420 of your 25,000
        # available directed hours this year because 11 active projects are
        # sharing organizational attention" - and the only honest way to
        # print that sentence is to read the numbers this loop actually used,
        # never to guess at them again from outside. pool_total/active_count
        # are the same for every project processed this step; rank and
        # remaining_before are this project's own position in the queue and
        # what was left of the pool when its own turn came. _agent_state and
        # `portfolio` (protocol.py) read these fields back verbatim - they do
        # not, and must not, recompute a share that could then disagree with
        # what this loop actually handed out.
        _pool_total_this_year = pool
        _pool_active_count_this_year = len(active_sorted)
        for _pool_rank, k in enumerate(active_sorted, start=1):
                st = self.household.active[k]
                n = self.nodes[k]
                st["pool_total_this_year"] = _pool_total_this_year
                st["pool_active_count_this_year"] = _pool_active_count_this_year
                st["pool_rank_this_year"] = _pool_rank
                st["pool_remaining_before_this_year"] = round(remaining, 1)
                # IS THERE ANYBODY TO DO THE WORK? If a trade this project needs
                # has vanished since it started (the machinists you taught died
                # out, say), nothing can be done on it this year, and your own
                # hours should go somewhere they are useful rather than into a
                # project that cannot absorb them.
                #
                # This matters more than it sounds. Without it a project whose
                # trade had disappeared sat in `active` for ever: hours went in,
                # no money was spent because no work was done, so the bill was
                # never paid, so it could never complete, so it never released
                # the slot. Four of those deadlocked a run at 98 technologies for
                # two hundred and fifty years.
                #
                # ONLY A TRADE THIS PROJECT STILL OWES SOMETHING TO. This used to
                # test n["lab"]'s ORIGINAL total (`want > 0`), which never goes
                # back to zero no matter how much of that trade's hours the
                # project has already drawn - lab_year_draw and trade_draw_plan
                # both correctly stop asking a trade for more once lab_left hits
                # zero, but this check kept vetoing the project on it forever. A
                # Han playtester fired a specialist whose hired-labour line
                # already read "0% owed" - the trade had nothing left to give
                # this project - and the very next step killed it anyway with
                # "no engineer here", a reason `why` had never shown because
                # `_waiting_on` (protocol.py) already knew, correctly, that
                # lab_left made this trade a non-issue. Two places answering
                # "does this project still need this trade" differently; this
                # makes the stall check agree with the one that draws the hours.
                _lab_left = st.get("lab_left")
                if _lab_left is None:
                    _lab_left = n["lab"]
                blocked = [t for t, want in n["lab"].items()
                           if want > 0 and _lab_left.get(t, want) > 0
                           and self.market_supply(t) <= 0.0]
                if blocked:
                    st["stalled_years"] = st.get("stalled_years", 0) + 1
                    st["blocked_on_trades"] = blocked
                    if st["stalled_years"] >= 4:
                        self.household.log.append((yr, "HALTED %s: there is nobody here who can "
                                             "do this work (%s). What you spent is lost"
                                         % (k, ", ".join(blocked[:2]))))
                        self.household.active.pop(k, None)
                        self.household.bountied.discard(k)
                    else:
                        # WARN BEFORE THE MONEY GOES. Six projects were wiped in
                        # one year for a play tester who had no way to list what
                        # was at risk: the countdown ran silently for three years
                        # and then took everything spent. Say it each year, with
                        # the number of years left and what would fix it.
                        _left = 4 - st["stalled_years"]
                        self.household.log.append((yr, "%s cannot go on: no %s here. It has "
                                             "%d year%s before it is abandoned and "
                                             "what you spent on it is lost. Teach "
                                             "the trade, or 'stop %s' now and keep "
                                             "your hours"
                                         % (k, " or ".join(blocked[:2]), _left,
                                            "" if _left == 1 else "s", k)))
                        # Nothing happened here this year - say so, rather than
                        # leaving last year's hours_offered/effective sitting on
                        # the entry looking like they still applied.
                        st["hours_offered_this_year"] = 0.0
                        st["hours_effective_this_year"] = 0.0
                    continue
                st["stalled_years"] = 0
                # project_hour_pace (projects.py) is this same formula, read
                # rather than re-derived, so 'work's own pre-sale warning
                # about starving an active project can never disagree with
                # what this loop actually offers it.
                #
                # A STANDING ALLOCATION IS A CEILING, NOT A FLOOR. hour_
                # allocations.get(k) is only ever a THIRD candidate in this
                # min() - never a reason to offer MORE than remaining or the
                # project's own pace would otherwise allow - so a directed
                # project can still never outrun the pool it shares with
                # everything else, and never get hours faster than its own
                # calendar floor could ever use. What it changes is ORDER
                # (active_sorted, above) and that an undirected project
                # never crowds this one out of the share the player asked
                # for it to have.
                _dir_hours = self.household.hour_allocations.get(k)
                _pace_cap = self.project_hour_pace(k)
                _project_throttle = self.project_resource_throttle(k)
                if _dir_hours and _dir_hours > 0:
                    per = min(remaining, _pace_cap, _dir_hours) * _project_throttle
                else:
                    per = min(remaining, _pace_cap) * _project_throttle
                remaining -= per
                # WHAT WAS ACTUALLY TAKEN OFF, which is not the same as what was
                # offered: `per` is allowed to exceed ph_left (the max() above
                # offers a full year's worth even to a project with an hour to
                # run), and the subtraction clamps at zero. The refunds below
                # were computed from `per` regardless, so a project with 10
                # hours left could be offered 500, have its 10 taken, and be
                # handed 200 back - ending the year with twenty times the hours
                # it began with. A playtester found the far end of that: a
                # progress bar reading "-67% of your hours spent", with
                # founder_hours_left larger than founder_hours_total. You cannot
                # be refunded work you never did.
                spent_hours = min(per, st["ph_left"])
                st["ph_left"] = max(0.0, st["ph_left"] - per)
                self.director_hours_spent_founder += per if self.founder_alive else 0
                # Hours OFFERED this year vs hours that actually did anything.
                # `refunded` tracks the difference: hours credited back to
                # ph_left below because a trade or the money to pay for it
                # fell short. Four projects each showed EXACTLY HALF their
                # founder hours left after one year and a tester called it
                # "confusing and feels artificial" - it was: nothing told them
                # `per` had been offered in full and half of it handed straight
                # back. See hours_this_year in `state`.
                st["hours_offered_this_year"] = round(per, 1)
                # WHAT THE PLAYER ACTUALLY ASKED FOR, READ BACK AT THE END OF
                # THE YEAR - `portfolio` and `why` print this field verbatim,
                # same reasoning as pool_total_this_year and its neighbours
                # just above: never recompute a number a player is told,
                # always read the one this loop actually used.
                st["hours_directed_this_year"] = (round(_dir_hours, 1)
                                                  if _dir_hours else None)
                # SAY SO WHEN THE PROMISE ITSELF WAS NOT KEPT, before any
                # trade or money shortfall even has a chance to bite further
                # in. A directive can be cut short right here, two ways: the
                # POOL had already given the rest away (to a higher-priority
                # directed project, or simply was not big enough for every
                # standing order at once), or this project's OWN pace -
                # what is left to do, or its calendar floor - could not use
                # that many hours even with the whole pool behind it. Either
                # is a real, nameable reason; "it disappeared" is not.
                if _dir_hours and _dir_hours > 0 and _dir_hours - per > 1.0:
                    if (_project_throttle < 0.98 and self.household.binding
                            and _pace_cap >= _dir_hours - 0.5):
                        _directed_hours_unused.append((k, round(_dir_hours - per, 0),
                            "a shortage of %s has every project (this one "
                            "included) running at %d%% of the pace its "
                            "hours alone would allow"
                            % (self.household.binding, round(_project_throttle * 100))))
                    elif _pace_cap * _project_throttle < _dir_hours - 0.5:
                        _directed_hours_unused.append((k, round(_dir_hours - per, 0),
                            "its own pace this year - at most %s hours, set "
                            "by how much of it is left to do or its "
                            "calendar floor, not by your hours - could not "
                            "use the rest" % "{:,.0f}".format(
                                _pace_cap * _project_throttle)))
                    else:
                        _directed_hours_unused.append((k, round(_dir_hours - per, 0),
                            "your other standing allocations and active "
                            "work already claimed the rest of this year's "
                            "%s hours before this one's turn came"
                            % "{:,.0f}".format(_pool_total_this_year)))
                refunded = 0.0
                st["yrs"] += 1
                frac = min(1.0, 1.0 / max(1.0, n["yrs"]))
                # Diagnostic callers can construct active-project dictionaries
                # directly, so initialise an omitted bill defensively.
                if st.get("cost_left") is None:
                    st["cost_left"] = max(0.0, self.project_cost(k) - st["spent"])
                # LABOUR BY TRADE. The old model pooled every trade into one
                # bucket of hired hours, so 450 hours of engineer and 450 hours
                # of labourer were the same resource. They are not, and the wage
                # table has said so all along. What binds now is the scarcest
                # trade this project actually needs.
                #
                # HOURS ARE A TOTAL AND A CEILING NOW, NOT A FIXED ANNUAL TOLL.
                # See ProjectsMixin.lab_year_draw (projects.py) for the finding
                # that forced this and the reasoning behind the new shape; this
                # call site only has to act on what it returns.
                hh, worst, frac, _abandon = self.lab_year_draw(k, st, frac, hired_left)
                if _abandon:
                    self.household.log.append((yr, "ABANDONED %s: %s" % (k, _abandon)))
                    self.household.active.pop(k, None)
                    self.household.bountied.discard(k)
                    continue
                if worst < 1.0:
                    # NEVER ALL OF IT. The refund says "hours offered but not
                    # usable, because the trade was booked" - and with no floor
                    # under it, it could hand back every hour that had actually
                    # gone in. A break tester watched a project's founder-hours
                    # sit unchanged for ever because its scarcest trade was
                    # short, the bill fully paid, the calendar long past, making
                    # no progress at all while holding an entire trade's pool
                    # and freezing other projects behind it.
                    #
                    # If a fraction `worst` of the work could be done, then a
                    # fraction `worst` of it WAS done, and that much can never
                    # be given back. Progress is now strictly positive whenever
                    # anybody at all can be found.
                    give_back = min(spent_hours - refunded,
                                    per * 0.4 * (1.0 - worst),
                                    spent_hours * (1.0 - worst))
                    st["ph_left"] += max(0.0, give_back)
                    refunded += max(0.0, give_back)
                    # Remember it. A tester sat on 696,350 denarii watching three
                    # projects report waiting_on "money" with 2.3, 84 and 158
                    # denarii left to pay, and reasonably concluded the spend cap
                    # was broken. It was not: the trades those projects needed
                    # were fully booked, so almost nothing could be paid FOR. The
                    # mechanic was right and the label was a lie. (short_of_trade
                    # itself is now set inside lab_year_draw, against the same
                    # pace this comment describes.)
                if hh > hired_left:
                    frac *= hired_left / max(hh, 1e-9)
                    hh = hired_left
                # THE INSTALMENT IS WHAT A CONSTRAINED YEAR CAN DO; THE BILL IS
                # WHAT IS LEFT. This used to work the payment out first and then
                # multiply it by each shortage in turn, so once the remaining
                # balance was smaller than a year's instalment you paid a
                # FRACTION OF WHAT WAS LEFT every year, for ever: a geometric
                # decay that approaches zero and never reaches it, while
                # completion needs the bill down to half a denarius. A
                # playtester watched one project sit at "71% done" for
                # twenty-five years with cash in hand and no idea why. Working
                # it out from the already-scaled `frac` means a shortage sets
                # how FAST you can pay and never stops the last payment landing.
                money = min(st["cost_left"], self.project_cost(k) * frac)
                hired_left -= hh
                # You may spend into debt, up to what someone will lend you, and
                # no further. Beyond that the work simply does not get paid for
                # this year, and a year nobody was paid for is a year of little
                # progress. What must NOT happen is the bill being forgiven.
                #
                # The margin is deliberate. Spending to the last denarius of your
                # credit means next year's rent breaches the limit and the
                # creditors halt every project you have, which turns "I was
                # ambitious" into "everything I had in hand was destroyed". A
                # lender who will advance you a thousand will not let you draw
                # the last two hundred of it against a half-built balloon.
                # Reserve next year's fixed costs AND most of the credit line.
                # Drawing the line to its last denarius is how one ambitious
                # project destroyed everything else a tester had in hand: the
                # limit itself falls as reputation and revenue fall, so a balance
                # exactly at the limit this year is over it next year, and over
                # the line every project in progress is halted at once.
                # Reserve only the SHORTFALL, not the whole running cost. This
                # year's rent and wages have already been taken out of capital at
                # the top of step(); reserving them again left a household with
                # 6,670 in hand and 31,000 of costs covered by 31,600 of income
                # unable to spend a single denarius on its own projects, so four
                # of them sat unpayable and unfinished for two hundred years.
                fixed = self.living_cost() + self.upkeep() + self.mine_operating_cost()
                reserve = max(0.0, fixed - self.revenue())
                purse = self.household.capital + self.credit_limit() * 0.6 - reserve
                # NOTHING OWED IS NOT THE SAME AS NOTHING AFFORDABLE. A
                # project with cost_left already at zero asks for money=0
                # this year, and money(0) > purse was still true whenever
                # purse itself had gone negative - deep arrears, not this
                # project's own bill - so a FULLY PAID project, needing not
                # one more denarius, was refunded nearly all of per anyway
                # (funded_frac forced to 0.0 below whenever money <= 0) and
                # made zero hour progress purely calendar-waiting projects
                # should still be free to make. Three playtesters on three
                # civilisations hit this as "arrears freezes ALL
                # founder-hour progress, even on fully-paid work" - and they
                # were exactly right: the gate was on the household's purse,
                # not on whether this project needed anything from it.
                if money > 0 and money > purse:
                    # PROPORTIONAL, not a flat half. This used to refund
                    # exactly per*0.5 whenever the purse fell short AT ALL,
                    # whether by one denarius or by the whole bill, which is
                    # what produced the "exactly half" a tester flagged as
                    # arbitrary-looking: four unrelated projects each showing
                    # precisely half their founder hours left after one year
                    # is not a coincidence, it is this constant. A project
                    # funded to 95% of what it needed lost the same fixed
                    # half of its hour's progress as one funded to 5%; the
                    # trade-shortage case two blocks up already scales its
                    # refund by how much of the need went unmet (worst), and
                    # this should too.
                    funded_frac = 0.0 if money <= 0 else max(0.0, min(1.0, purse / money))
                    money = max(0.0, purse)
                    # Capped at what was actually taken off, and at what has not
                    # already been handed back by the trade-shortage refund
                    # above. See spent_hours: you cannot be refunded work you
                    # never did, and you cannot be refunded the same hour twice.
                    give_back = min(spent_hours - refunded, per * (1.0 - funded_frac))
                    st["ph_left"] += max(0.0, give_back)
                    refunded += max(0.0, give_back)
                    st["underfunded_this_year"] = True
                    # WHY, not just that. A playtester ran deep into debt and
                    # watched every project report hours "offered" and none
                    # "effective", with nothing in help, why, money or risk
                    # explaining it. Arrears are the reason: the purse a project
                    # may draw on is what you hold plus part of your credit,
                    # less what your fixed costs need, and in arrears that is
                    # nothing at all.
                    st["why_underfunded"] = (
                        "in arrears: after fixed costs there is nothing left to "
                        "draw on, so the hours offered this year did almost "
                        "nothing" if self.household.capital < 0 else
                        "this year's instalment is more than the purse will bear")
                    # SAY IT NOW, NOT ONLY WHEN ASKED. `why_underfunded` sits on
                    # the project and answers the question if a player thinks
                    # to check `why` or `portfolio` - but the founder-hours lost
                    # here never come back, whatever the player does next, and
                    # nothing prompted them to look. Recorded here (only the
                    # arrears case, only if it actually cost real hours) and
                    # logged once below, after the loop.
                    if self.household.capital < 0 and give_back > 1.0:
                        _arrears_hours_lost.append((k, round(give_back, 0)))
                else:
                    st.pop("underfunded_this_year", None)
                    st.pop("why_underfunded", None)
                self.household.capital -= money
                self.household.total_spend += money
                st["spent"] += money
                st["cost_left"] = max(0.0, st["cost_left"] - money)
                # spent_hours, NOT per. `per` is what was OFFERED, and it is
                # allowed to exceed the hours the project actually had left; the
                # refunds above are capped at spent_hours for exactly that
                # reason, and this line was left uncapped. A sweep of the
                # playtest notes found a project reporting 387.2 effective hours
                # a year for four consecutive years while founder_hours_left sat
                # unchanged at 112.8 - work reported that provably did not
                # happen, about the one resource the whole game is built on.
                st["hours_effective_this_year"] = round(max(0.0, spent_hours - refunded), 1)
                hours_effective_total += st["hours_effective_this_year"]
                # THE SECOND WAY A DIRECTIVE GOES UNHONOURED: OFFERED, THEN
                # HANDED BACK. Unlike the check above this one, it must NOT
                # fire just because spent_hours fell short of `per` - a
                # project a few hours from finished is offered a whole
                # year's pace and only needs a sliver of it, which is not a
                # shortage of anything, it is the project ending. Gated on
                # why_underfunded/short_of_trade actually being SET this
                # year - fields only the money and trade-shortage branches
                # above ever write - so this can only ever name a real
                # shortfall, never mistake "it finished" for one.
                if _dir_hours and _dir_hours > 0:
                    _inner_gap = st["hours_offered_this_year"] - st["hours_effective_this_year"]
                    # DEEP ARREARS ALREADY GETS ITS OWN LINE, BELOW - "IN
                    # ARREARS: ... did almost nothing this year" - and it is
                    # the sharper warning of the two. Saying the same
                    # shortfall twice in two different voices is not
                    # clearer, it is just noise; this fires only for the
                    # money-short case arrears does NOT already cover (the
                    # purse-can-only-absorb-so-much-a-year pace, which is
                    # real money trouble without capital actually being
                    # negative).
                    if _inner_gap > 1.0 and st.get("why_underfunded") and self.household.capital >= 0:
                        _directed_hours_unused.append(
                            (k, round(_inner_gap, 0), st["why_underfunded"]))
                    elif _inner_gap > 1.0 and st.get("short_of_trade"):
                        _directed_hours_unused.append((k, round(_inner_gap, 0),
                            "trade hours already booked: " + ", ".join(
                                sorted(st["short_of_trade"])[:2])))
                # Count it HERE, after the hired-hours scaling and the
                # affordability clamp, not before them. Accumulating the
                # notional figure made project_spend_last_year disagree with
                # the actual capital movement by a factor of 89, which a tester
                # caught by comparing three numbers in a single `state` reply.
                self.household._spend_this_year = self.household._spend_this_year + money
                # calendar_floor(k), NOT a second copy of this formula -
                # expected_calendar_years (projects.py) needs the identical
                # figure to project retries honestly, and a rule living in
                # two places is how this kind of arithmetic drifts apart.
                floor = self.calendar_floor(k)
                # THE BILL HAS TO BE PAID. Hours done and years elapsed are not
                # enough; if the money never arrived, the thing was never built.
                # HALF AN HOUR IS NOTHING LEFT TO DO. The give-back hands back a
                # fraction of what was offered, so on a throttled project
                # ph_left decays geometrically towards zero and never reaches
                # it: a break tester's `logarithms` sat at 1.29e-25 founder-hours
                # with the bill paid and thirty years elapsed, complete in every
                # sense except the comparison. The bill already had this exact
                # fix and this exact reason (see `money` just above, and
                # cost_left <= 0.5 on the same line); hours never got it.
                if st["ph_left"] < 0.5:
                    st["ph_left"] = 0.0
                if st["ph_left"] <= 0 and st["yrs"] >= floor and st["cost_left"] <= 0.5:
                    self._complete(k)
                elif st["ph_left"] <= 0 and st["yrs"] >= floor and st["cost_left"] > 0.5:
                    st["waiting_on_money"] = True

        # ARREARS COSTS YOU THE YEAR'S HOURS, NOT JUST THE MONEY - SAY SO. This
        # is the Rome playtester's sharpest complaint: "the arrears mechanic
        # silently wastes founder-hours, not just money", discovered only
        # after several turns of a project sitting at "did almost nothing"
        # with no explanation on the turn itself. Founder-hours are the one
        # resource in this whole model that never banks (see step 5b and
        # `state`'s free_hours_going_unused): a year of them lost silently is
        # worse than a year of money lost, because money can be earned back
        # on the same footing next year and this cannot be earned back at
        # all. Named per project, so 'why <id>' and this line never disagree
        # about which project or how much.
        if _arrears_hours_lost:
            _total_lost = sum(h for _, h in _arrears_hours_lost)
            _names = ", ".join("%s (%s hr)" % (k, "{:,.0f}".format(h))
                                for k, h in _arrears_hours_lost)
            self.household.log.append((yr, "IN ARREARS: %s founder-hours meant for %s did "
                                 "almost nothing this year, on top of the money "
                                 "- that time does not come back, arrears or not. "
                                 "'work' sells idle hours for wages instead of "
                                 "losing them here; clearing the arrears is what "
                                 "stops it happening again"
                             % ("{:,.0f}".format(_total_lost), _names)))

        # A STANDING ALLOCATION THE PLAYER GAVE, AND DID NOT GET - SAID, NOT
        # LEFT FOR THEM TO NOTICE. `allocate` is a promise about the one
        # resource that never banks; silently falling short of it is the
        # same unfairness the arrears line above exists to stop, aimed at a
        # player who took the extra step of directing their hours on
        # purpose rather than leaving the split to priority order. Sorted
        # by id for a deterministic order across runs with the same seed -
        # several projects can be cut short in the same year.
        if _directed_hours_unused:
            for _k, _hr, _why in sorted(_directed_hours_unused):
                self.household.log.append((yr, "DIRECTED HOURS UNUSED: you allocated hours "
                                     "to %s this year that it could not use - "
                                     "%s of them went begging because %s. "
                                     "'portfolio' shows the rest; 'allocate' "
                                     "changes or clears the standing order"
                                 % (self.nodes[_k]["name"],
                                    "{:,.0f}".format(_hr), _why)))

        # Snapshot BEFORE 5b spends more of `remaining` on wage work: otherwise
        # offered_to_projects below double-counts wage hours as though they had
        # been offered to projects too, since 5b draws from the same pool.
        remaining_after_projects = remaining

        # 5b. IF THERE IS NO WORK AND NO MONEY, TAKE A JOB. A man who arrives
        #     with four hundred denarii and a lens does not sit watching his
        #     savings run out; he teaches, or writes, or sets bones for money. It
        #     is in the protocol as `work` for a player and the optimizer had no
        #     equivalent, so a single bad year in the opening decade could end a
        #     run: one Rome seed earned four technologies in five hundred years
        #     because a fire in 103 took a fifth of everything it had.
        if (not self.manual and remaining > 100.0
                and (self.household.capital < self.living_cost() * 2 or not self.household.active)):
            trade = ("scholar" if self.effective_scholars() >= 1 else "scribe")
            hours = min(remaining, 1200.0)
            # ONLY IF IT PAYS BETTER THAN THE PRACTICE IT DISPLACES. Wage hours
            # now cost you the share of your practice they were sold out of
            # (see practice_attention), and without this check the optimizer
            # went on taking a scribe's wage at the price of a physician's fee
            # and lost Rome a sixth of its runs. A man with a practice does not
            # go and copy documents for less than the practice earns; that is
            # the whole reason `work` is the thing you do BEFORE you have one.
            # NOT `pool`. That name already held the year's project budget,
            # computed at 4b, and reusing it here overwrote it - so
            # hours_this_year then reported "offered_to_projects" against the
            # WHOLE year instead of against the project budget. The year's
            # hours added up to 2,900 out of 2,000, which is exactly the sort
            # of arithmetic a player cannot argue with and cannot trust.
            year_hours = max(1.0, self.director_pool())
            practice_lost = self.revenue() * (hours / year_hours) * (
                1.0 if self.practice_attention() > 0 else 0.0)
            rate = (self.annual_wage(trade) / self.HOURS_PER_PERSON_YEAR
                    * (1.0 + min(0.5, self.household.reputation / 200.0)))
            if hours * rate > practice_lost:
                _, err = self.work_for_wages(trade, hours)
                # Kept in step with `remaining` so hours_this_year (below) does
                # not count hours sold for wages here as still unused.
                if err is None:
                    remaining -= hours

        # 6. reputation, familiarity, protection, scandal
        #
        # Reputation DECAYS TOWARD WHAT YOU ARE ACTUALLY KNOWN FOR, not toward
        # zero. Three testers independently reported the same thing: reputation
        # slid from 10 to 0.2 over a century and a half with no event ever
        # explaining it, and one called it "less like a lever I could manage and
        # more like a clock running out in the background". They were right, and
        # decaying to zero was also wrong on its own terms. A physician with a
        # practice, a school and a written corpus does not become a man nobody
        # has heard of because thirty quiet years passed. What fades is novelty;
        # what remains is the work.
        floor = self.standing_floor()
        self.household.reputation = floor + (self.household.reputation - floor) * 0.97
        # ADAPTATION. Every year the world has known you, and every visible thing
        # you have already done, makes the next one less astonishing.
        pub = sum(1 for k in self.household.done
                  if set(self.nodes[k].get("traits", [])) & {"spectacle", "inexplicable"})
        self.household.familiarity = min(0.9, 1.0 - math.exp(-self.w["adaptation_rate"] *
                                                   (0.5 * pub + 0.25 * (self.year - 100))))
        # WHERE THE YEAR'S HOURS WENT. Four projects each showed exactly half
        # their founder hours left after one year, with 2,400 available and
        # only about 200 apparently spent, and a tester had no way to see why:
        # nothing in `state` accounted for a year's hours at all. Captured
        # here, before the tallies below reset for the next year, the same way
        # spend_last_year already captures the year's spending. See it as
        # `hours_this_year` in `state`.
        self.hours_this_year = {
            "available": round(self.director_pool(), 1),
            "wage_work": round(getattr(self.household, "wage_hours_this_year", 0.0), 1),
            "teaching": round(self.household.teaching_hours_this_year, 1),
            "offered_to_projects": round(max(0.0, pool - remaining_after_projects), 1),
            # OFFERED is what projects were given a shot at; EFFECTIVE is what
            # actually reduced their founder_hours_left. The gap between the
            # two is hours that went in and came straight back out again
            # because a trade or the money to pay for it fell short that year
            # - see hours_offered_this_year / hours_effective_this_year on
            # each project in `active`, and underfunded_this_year.
            "effective_on_projects": round(hours_effective_total, 1),
            "unused": round(max(0.0, remaining), 1),
        }
        # Reset AFTER the progress pass above, which is where the hours you sold
        # are subtracted from the hours you have left to direct.
        self.household.wage_hours_this_year = 0.0
        # Contracted work is bought for a year and expires with it: hours you
        # paid a shop for in 142 are not still sitting there in 143.
        self.household.contract_hours = {}
        self.household.teaching_hours_this_year = 0.0
        self.household.spend_last_year = self.household._spend_this_year
        self.household._spend_this_year = 0.0
        # Sellers restock, so the pressure your buying put on the market fades.
        self.household.market_pressure = max(0.0, self.household.market_pressure * 0.55 - 2.0)
        # WARN BEFORE IT KILLS YOU. A play tester built 952 technologies, was
        # three nodes from the goal, and the run ended on a 2% roll against an
        # eminence of 28.2 - with no escalation of any kind beforehand, and
        # nothing in the log ever mentioning it. Their words: "no escalation on
        # the stat that ends the run". It is the one hazard that cannot be
        # bribed away and the one the player was never told was closing in.
        _danger = self.cfg["eminence_danger"]
        if self.household.eminence > _danger * 0.75:
            _said = self.household._said_eminence
            _band = int(self.household.eminence / max(1.0, _danger * 0.15))
            if _band > _said:
                self.household._said_eminence = _band
                self.household.log.append((yr, "YOU ARE BECOMING CONSPICUOUS: eminence %.0f "
                                     "against a danger line of %.0f. This is the "
                                     "one thing no patron and no bribe protects "
                                     "you from, and it grows with reputation and "
                                     "visible wealth. A wide, dispersed "
                                     "institution is what survives you"
                                 % (self.household.eminence, _danger)))
        self.update_protection()
        # THE STATE NOTICES YOU. Requisition, the pressed office, a demand
        # for military supply, and the tail confiscation risk at the top of
        # the same scale - see SocietyMixin's own "THE STATE NOTICES YOU"
        # section (society.py) for the whole mechanic. Run after
        # update_protection() so this year's patronage and office standing
        # are what requisition/confiscation actually bargain against, and
        # before scandal/eminence below so a confiscation this mechanic
        # causes and the eminence-driven one further down are never
        # resolved in the same breath as two unrelated draws on the same
        # stale numbers.
        self._state_pressure(yr)
        self.household.scandal *= 0.90
        # Eminence accumulates in a SEPARATE pool, because bribery does not
        # touch it. You can buy a magistrate, an accuser and a jury. You cannot
        # buy an emperor's judgement that you have grown too large, and the
        # attempt is itself evidence against you.
        self.household.eminence = self.household.eminence * 0.93 + self.prominence_hazard()
        # you can buy your way out of trouble, and a sane player does
        if self.household.scandal > 8 and self.household.capital > 2000 and self.policy.get("auto_bribe", not self.manual):
            spend = min(self.household.capital * 0.12, self.household.scandal * 260)
            self.household.capital -= spend
            self.household.bribes_ytd = 0.7 * self.household.bribes_ytd + spend
            self.household.scandal -= spend / 300.0 * self.w["bribability"]
        else:
            self.household.bribes_ytd *= 0.7
        self.household.scandal = max(0.0, self.household.scandal)
        # WARN, THE WAY EMINENCE DOES. Denunciation ends the run outright and
        # said nothing at all first: a break tester read "RUN ENDS: denounced:
        # as a sorcerer" after eleven quiet years, with `state` showing
        # "scandal 33.55" and no threshold, no probability and no note - on the
        # same screen where eminence carefully explains that it is "dangerous
        # above 26 ... 0% chance the run ENDS this year". Two hazards of the
        # same shape, one of them legible.
        _sd = c["suspicion_danger"]
        if self.household.scandal > _sd * 0.75:
            _band = int(self.household.scandal / max(1.0, _sd * 0.15))
            if _band > int(getattr(self.household, "_said_scandal", 0)):
                self.household._said_scandal = _band
                self.household.log.append((yr, "YOU ARE BEING TALKED ABOUT: scandal %.0f "
                                     "against a line of %.0f. Past it you may be "
                                     "denounced, and that ends the run - about "
                                     "%.0f%% a year at this level. 'bribe' buys "
                                     "advocacy and piety; it falls a tenth a "
                                     "year on its own"
                                 % (self.household.scandal, _sd,
                                    100.0 * max(0.0, (self.household.scandal - _sd) / 60.0))))
        elif self.household.scandal < _sd * 0.5:
            self.household._said_scandal = 0
        if self.events and self.household.scandal > c["suspicion_danger"]:
            p = (self.household.scandal - c["suspicion_danger"]) / 60.0
            if self.rng.random() < p:
                self._catastrophe("denounced: %s" % ("as a sorcerer" if self.w["w_magic_fear"] > 0.5
                                                     else "as a subversive"))
        # The eminence hazard is separate and unbribable. Its usual outcome is a
        # bad year rather than a death: a confiscation, a patron destroyed in
        # someone else's quarrel, a forced withdrawal from public life.
        if self.events and self.household.eminence > c["eminence_danger"]:
            p = (self.household.eminence - c["eminence_danger"]) / 90.0
            if self.rng.random() < p:
                roll = self.rng.random()
                if roll < 0.45:
                    take = self.household.capital * 0.55
                    self.household.capital -= take
                    self.household.reputation = max(0.0, self.household.reputation - 18)
                    self.household.eminence *= 0.45
                    self.household.log.append((yr, "PROMINENCE: property confiscated, %d den lost, "
                                         "and you withdraw from public life for a while" % take))
                elif roll < 0.80:
                    for pat in ("patron_imperial", "patron_senatorial"):
                        if pat in self.household.done:
                            self.household.done.discard(pat)
                            self._done_changed()
                            self.household.log.append((yr, "PROMINENCE: your patron is destroyed in "
                                                 "someone else's quarrel and you lose %s" % pat))
                            break
                    self.household.eminence *= 0.5
                    self.household.reputation = max(0.0, self.household.reputation - 10)
                else:
                    self._catastrophe("too eminent: brought down not for what you built "
                                      "but for how large you had become")

        # 6b. serving out a debt. The hours you owe go to the creditor and the
        #     debt falls; when it is done you are free, and you keep everything
        #     you know.
        if self.household.bondage_years_left > 0:
            self.household.bondage_years_left -= 1
            paid = self.cfg["founder_hours_per_year"] * 0.75 * \
                (WAGES.get("labourer", 0.075) * 1.2) * self.wage_index * self.price_index
            self.household.bondage_debt = max(0.0, self.household.bondage_debt - paid)
            if self.household.bondage_debt <= 0 and self.household.bondage_years_left > 0:
                self.household.bondage_years_left = 0     # paid early
            if self.household.bondage_years_left <= 0:
                self.household.bondage_years_left = 0.0
                self.household.bondage_debt = 0.0
                self.household.log.append((yr, "your term is served and the debt is discharged; "
                                     "you are your own man again"))

        # 7. founder mortality
        if self.founder_alive:
            self.life_left -= 1
            if self.running("sanitation_antisepsis"):
                self.life_left += 0.12      # you at least do not die of a septic cut
            if self.life_left <= 0:
                self.founder_alive = False
                # SAY WHAT IT MEANS, not only that it happened. Two round-12
                # testers independently called this the worst thing in the
                # game: one wrote that a dead founder's run was "permanently
                # unwinnable from that point" with the game never saying so,
                # the other that a corpse went on being offered 69 startable
                # projects and actually accepted one. The engine is not in
                # fact silent about the consequence - deputies carry the work,
                # and with none the programme dissolves over twelve years - but
                # nothing ever told the player either half of that.
                _dep = self.household.directors_extra
                self.household.log.append((yr, "THE FOUNDER DIES, aged about %d. %s"
                                 % (self.cfg["founder_arrival_age"] + yr
                                    - self.cfg["start_year"],
                                    ("Your %.1f deputies direct the work in your "
                                     "name and the programme goes on without you: "
                                     "that is what training them was for."
                                     % _dep) if _dep >= 0.5 else
                                    "You trained no deputy, so there is nobody to "
                                    "direct anything. Nothing that needs your "
                                    "hours can ever be begun again, and what you "
                                    "built will be forgotten over the next twelve "
                                    "years unless a deputy appears. This run is "
                                    "effectively over; 'state' shows how far you "
                                    "got.")))
        # a programme with no director is not paused, it is dissolving
        if not self.founder_alive and self.household.directors_extra < 0.5:
            self.household.stalled += 1
            if self.household.stalled >= 3:
                losable = sorted(k for k in self.household.done if k not in self.household.granted)
                # sorted() matters: self.household.done is a SET, and a set iterates in an
                # order that depends on PYTHONHASHSEED, so feeding it unsorted to
                # rng.sample made the same --seed give a different answer on every
                # invocation. Every figure this project has reported was, strictly,
                # unreproducible.
                if losable:
                    for k in self.rng.sample(losable, max(1, len(losable) // 6)):
                        self.household.operating.discard(k)
                        self.household.done.discard(k)
                        self._done_changed()
            # COUNT IT DOWN WHERE THE PLAYER CAN SEE IT. Twelve years of a
            # dissolving programme passed with nothing said but the shedding
            # itself, so a tester read the losses as unexplained and the run as
            # merely unlucky rather than finished.
            if self.household.stalled in (3, 6, 9, 11):
                self.household.log.append((yr, "THE PROGRAMME IS DISSOLVING: %d year(s) "
                                     "since the founder died with no deputy to "
                                     "take over. What you built is being "
                                     "forgotten. The run ends at twelve."
                                 % self.household.stalled))
            if self.household.stalled >= 12:
                self._catastrophe("the founder died without training successors; "
                                  "the school dispersed and the work was forgotten")
        else:
            self.household.stalled = 0

        # 8. random events
        if self.events and not self.dead_reason:
            self._random_events(yr)

        self.year += 1

    # ---- THRESHOLD GOALS: completed by measurement, not by labour ---------
    # A goal need not be a thing you build. "Raise literacy past a fifth" or
    # "cut what epidemics take by four-fifths" are states of the whole
    # society, not a project with hours and materials - see data/tech_tree.json
    # meta.goals and its own note on why a threshold is still modelled as a
    # node (so closure()/critical_path()/Sim.run() never need a second idea
    # of what a goal is) rather than as a second mechanism bolted on beside
    # the ordinary one.
    WIN_CONDITION_METRICS = frozenset(
        ("literacy_general", "literacy_elite", "epidemic_relief"))

    def _win_condition_value(self, metric):
        """The live number a win_condition's `metric` names, 0..1. Raises for
        a metric this engine does not know how to read - at load time, via
        `validate`, not mid-game - rather than silently reading 0 forever for
        a typo no playtest would otherwise catch."""
        if metric in ("literacy_general", "literacy_elite"):
            return float(self.civ.get(metric, 0.0))
        if metric == "epidemic_relief":
            # hazard_relief returns the SURVIVING fraction of the harm
            # (1.0 = no protection at all); relief is what is cut, the rest
            # of it - see society.py's own docstring on the diminishing,
            # never-quite-zero shape of that number.
            return 1.0 - self.hazard_relief("staff_loss")[0]
        raise ValueError("unknown win_condition metric %r" % metric)

    def _check_win_conditions(self, yr):
        """Once a year: every node carrying a `win_condition` that is not
        already done gets checked against the live measurement it names,
        and completes itself - exactly like a normal completion (done,
        done_year, the log, goal_year if it is the running goal) but with
        no cost charged and no `apply_tech_effects`/reputation/scandal call,
        because nobody did any work; a measurement crossed a line. Sorted
        so the order is reproducible under a fixed PYTHONHASHSEED, the same
        reasoning `topo_order` and the attrition loop above already give
        for walking `self.nodes`/`self.household.done` in id order rather than a bare
        set's own iteration order.

        Walks `self._win_condition_keys` (built once, in __init__, from the
        static node data - see the comment there), not `sorted(self.nodes)`:
        this used to re-sort every one of the ~2,849 node ids in the whole
        tree, every single year, to reach the handful that actually carry a
        win_condition at all - pure self time (`sorted` and dict-get, both
        C-level, nothing further to profile under it).
        """
        for k in self._win_condition_keys:
            if k in self.household.done:
                continue
            wc = self.nodes[k]["win_condition"]
            if not wc:
                continue
            val = self._win_condition_value(wc["metric"])
            op, target = wc["op"], wc["value"]
            met = (val >= target) if op == ">=" else (val <= target) if op == "<=" else False
            if not met:
                continue
            self.household.done.add(k)
            self._done_changed()
            self.household.done_year[k] = yr
            self.household.log.append((yr, "achieved: " + self.nodes[k]["name"]))
            if k == self.goal and self.household.goal_year is None:
                self.household.goal_year = yr

    def run(self, goal, horizon=None):
        self.goal = goal
        self.household.done_year = {}
        horizon = horizon or self.cfg["horizon_years"]
        end = self.cfg["start_year"] + horizon
        while self.year < end and not self.dead_reason and self.household.goal_year is None:
            self.step()
        return self


# ----------------------------------------------------------------------------
# Strategies
# ----------------------------------------------------------------------------
