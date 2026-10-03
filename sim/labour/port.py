"""The labour port: every question outside code asks about people, staff, wages and where the
household stands, answered by the labour mixins on the simulation. `sim.labour` is this object.
Each member delegates to the mixin method of the same name; the market every employer asks is
`market`."""


class LabourPort:
    """Questions and transactions about labour, for one simulation."""

    def __init__(self, sim):
        self._sim = sim

    @property
    def market(self):
        """The labour market every employer asks (labour_market_api.LabourMarket)."""
        return self._sim.labour_market

    def allocate_farm_workforce(self, adult_equivalent_population):
        return self._sim._allocate_farm_workforce(adult_equivalent_population)

    def apply_land_clearing(self):
        return self._sim._apply_land_clearing()

    def grant_staff(self, scholars=0.0, artisans=0.0):
        return self._sim._grant_staff(scholars, artisans)

    def opening_wage_schedule(self):
        return self._sim._opening_wage_schedule()

    def resync_pools(self):
        return self._sim._resync_pools()

    def room_advice(self):
        return self._sim._room_advice()

    def set_farm_area(self, hectares):
        return self._sim._set_farm_area(hectares)

    def staff_advice(self, kind, deficit=None):
        return self._sim._staff_advice(kind, deficit)

    def stochastic_round(self, x):
        return self._sim._stochastic_round(x)

    def trade_headcount_pending(self, trade):
        return self._sim._trade_headcount_pending(trade)

    def auto_commission_for_blocked(self, look=40):
        return self._sim.auto_commission_for_blocked(look)

    def available_trades(self):
        return self._sim.available_trades()

    def base_annual_wage(self, trade):
        return self._sim.base_annual_wage(trade)

    def base_tile(self):
        return self._sim.base_tile()

    def book_money(self, denarii):
        return self._sim.book_money(denarii)

    def buy_slaves(self, n_people):
        return self._sim.buy_slaves(n_people)

    def close_wage_year(self):
        return self._sim.close_wage_year()

    def commission(self, trade, hours):
        return self._sim.commission(trade, hours)

    def commission_check(self, trade, hours):
        return self._sim.commission_check(trade, hours)

    def craft_hands_available(self):
        return self._sim.craft_hands_available()

    def director_hours_committed(self):
        return self._sim.director_hours_committed()

    def director_pool(self):
        return self._sim.director_pool()

    def distance_to_tile_km(self, tile):
        return self._sim.distance_to_tile_km(tile)

    def effective_scholars(self):
        return self._sim.effective_scholars()

    def farm_share_of_hours(self):
        return self._sim.farm_share_of_hours()

    def fire(self, trade, count):
        return self._sim.fire(trade, count)

    def found_trade_school(self, trade, seats):
        return self._sim.found_trade_school(trade, seats)

    def headcount(self):
        return self._sim.headcount()

    def hire(self, trade, count):
        return self._sim.hire(trade, count)

    def hire_check(self, trade, count):
        return self._sim.hire_check(trade, count)

    def hired_cap(self):
        return self._sim.hired_cap()

    def hold_staff_reserve(self):
        return self._sim.hold_staff_reserve()

    def home_town_population_estimate(self):
        return self._sim.home_town_population_estimate()

    def hours_reserved(self, trade):
        return self._sim.hours_reserved(trade)

    def hours_you_can_call_on(self, trade):
        return self._sim.hours_you_can_call_on(trade)

    def household_room(self):
        return self._sim.household_room()

    def idle_specialists(self):
        return self._sim.idle_specialists()

    def keep_flagged_concerns_staffed(self):
        return self._sim.keep_flagged_concerns_staffed()

    def literacy_factor(self, trade):
        return self._sim.literacy_factor(trade)

    def literate_capacity(self, trade):
        return self._sim.literate_capacity(trade)

    def local_market_share(self):
        return self._sim.local_market_share()

    def log_staff_reduction(self, cause, before):
        return self._sim.log_staff_reduction(cause, before)

    def manumit(self, n_people):
        return self._sim.manumit(n_people)

    def market_supply(self, trade):
        return self._sim.market_supply(trade)

    def market_supply_split(self, trade):
        return self._sim.market_supply_split(trade)

    def money_per_labour_hour(self):
        return self._sim.money_per_labour_hour()

    def move_base(self, tile):
        return self._sim.move_base(tile)

    def national_trade_population(self, trade):
        return self._sim.national_trade_population(trade)

    def people_who_exist(self, trade):
        return self._sim.people_who_exist(trade)

    def population_report(self):
        return self._sim.population_report()

    def project_staffing_shortfall(self, node):
        return self._sim.project_staffing_shortfall(node)

    def reachable_trade_population(self, trade):
        return self._sim.reachable_trade_population(trade)

    def relocation_quote(self, tile):
        return self._sim.relocation_quote(tile)

    def replace_lost_foremen(self):
        return self._sim.replace_lost_foremen()

    def scholar_hands_available(self):
        return self._sim.scholar_hands_available()

    def settlement_tiles(self):
        return self._sim.settlement_tiles()

    def slave_quote(self, n_people):
        return self._sim.slave_quote(n_people)

    def sole_supervisors(self):
        return self._sim.sole_supervisors()

    def staff_capacity(self):
        return self._sim.staff_capacity()

    def staff_snapshot(self):
        return self._sim.staff_snapshot()

    def supervision_room(self):
        return self._sim.supervision_room()

    def supervision_room_from(self):
        return self._sim.supervision_room_from()

    def trade_available(self, trade):
        return self._sim.trade_available(trade)

    def trades_drawn_on(self):
        return self._sim.trades_drawn_on()

    def train(self, trade, count, frm=None):
        return self._sim.train(trade, count, frm)

    def train_check(self, trade, count, frm=None):
        return self._sim.train_check(trade, count, frm)

    def trainee_wage_bill(self, trade, count):
        return self._sim.trainee_wage_bill(trade, count)

    def update_wages(self):
        return self._sim.update_wages()

    def wage_bill(self):
        return self._sim.wage_bill()

    def wage_per_hour(self, trade):
        return self._sim.wage_per_hour(trade)

    def wage_work_this_year(self):
        return self._sim.wage_work_this_year()

    def work_for_wages(self, trade, hours):
        return self._sim.work_for_wages(trade, hours)

    def work_for_wages_dry_run(self, trade, hours):
        return self._sim.work_for_wages_dry_run(trade, hours)

    def workforce_report(self):
        return self._sim.workforce_report()
