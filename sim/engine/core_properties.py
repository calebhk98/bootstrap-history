"""The outside-facing property surface for the extracted Household.

These are properties of Sim; they live in a mixin only so this one
mechanically near-identical block can sit in a file of its own instead
of pushing every other reader of core.py past all of them
to reach anything else.

THE COUNT: this file holds 87 forwarding properties
(`grep -c "^    @property"` on this file). A property belongs here only
if it has at least one call site through the `Sim` surface, in
`SAVE_FIELDS`, or both - measured across the whole repository:
engine-internal reads already going through `self.household.x` directly,
reads through the `Sim` surface from proto/cli/simulator.py/tests,
`SAVE_FIELDS` (sim/engine/proto/saveload.py), and dynamic reach by field
list (sim/perf_fingerprint.py's `state_of`). A property nothing outside
the engine reads and nothing inside the engine reaches THROUGH is pure
dead weight and does not belong here; see this file's own git history for
which properties were removed on that basis and why.

Two properties that LOOK like they belong here stayed in core.py instead,
on purpose: `pop_scale` and `wage_index` are not one-line forwards - each
computes a value from self.population, self.civ and a couple of other Sim
attributes, and `wage_index` reads `self.pop_scale` in turn - so moving
them here would put real logic in a file whose whole point is that
everything in it is inert boilerplate. Grouping by what the code actually
does, not by where it happened to sit, is the same principle
SIM_DECOMPOSITION_REVISITED.md section 4 applies to Sim.step() itself.

MIND THE PERFORMANCE, NOT JUST THE GROUPING: these stay `@property`, never
`__getattr__`. docs/architecture/HOUSEHOLD_EXTRACTION.md section 2 measured
a `@property` forwarder at 60.3ns per access against `__getattr__`'s
519.4ns (51x slower), so moving this block to its own file costs nothing -
it changes where the code is READ, not what it does when it runs.
"""


class ForwardingPropertiesMixin:
    """Composition point only: every property below is a plain forward onto
    self.household or self.population, moved verbatim out of core.py's
    `class Sim(...)`, which still inherits this mixin so nothing outside
    core.py has to change to keep resolving these by name - the JSON
    protocol, save/load (sim/engine/proto/saveload.py's SAVE_FIELDS), the
    CLI and the tests all read these off a live Sim instance exactly as
    they did before this file existed.
    """

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
    def _last_buy_refusal(self):
        # LAZY: absence is meaningful (see the section comment above).
        # Do not add a default here.
        return self.household._last_buy_refusal

    @_last_buy_refusal.setter
    def _last_buy_refusal(self, value):
        self.household._last_buy_refusal = value

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

    # WIRING MILESTONE 4, COMMIT 2 (docs/architecture/WIRING_MILESTONE_4.md
    # SS3, SS6): three forwarding properties, same shape as the household
    # ones just above, so `self.population`'s three cohort floats each get a
    # SAVE_FIELDS slot without a save format that has ever seen a nested
    # object (see that section for why three flat floats, not one struct).
    # Before this, none of the nine attributes _demographic_recovery's
    # scalar model used were ever saved at all - a live, currently-shipping
    # bug (a --session game silently wiped a demographic shock's wage
    # premium on the very next command, because cli.py reconstructs a fresh
    # Sim and load_state()s the save over it) which this fixes for the
    # REPLACEMENT model rather than reproducing it. `Population` itself is
    # never constructed by `load_state` - `Sim.__init__` already built one
    # (with the civilisation's UNSHOCKED baseline size) before load_state
    # runs, and these three setters overwrite its cohort counts in place
    # with whatever the save recorded, the same "setattr over a live
    # default" shape every other field in SAVE_FIELDS already uses.
    @property
    def pop_children(self):
        return self.population.children

    @pop_children.setter
    def pop_children(self, value):
        self.population.children = float(value)

    @property
    def pop_working_age(self):
        return self.population.working_age

    @pop_working_age.setter
    def pop_working_age(self, value):
        self.population.working_age = float(value)

    @property
    def pop_elderly(self):
        return self.population.elderly

    @pop_elderly.setter
    def pop_elderly(self, value):
        self.population.elderly = float(value)
