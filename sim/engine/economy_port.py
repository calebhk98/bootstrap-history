"""The one door between the engine and the economy.

The tree, the founder, projects, actors and screens ask this port about prices, wages, rates, money
and what a concern takes, and post their purchases, sales and hires through it. They do not read
the price tables, the coin stock or the market book directly, so the model behind the port can
change without them knowing. This is the only engine module that may import `sim.economy`
(sim/tests/test_economy_imports.py); the agent economy answers, and the engine's own opening figures answer
while it opens.
"""
from . import node_upkeep, opening_money


class EconomyPort:
    """Questions and transactions about the economy, for one simulation."""

    def __init__(self, sim):
        self._sim = sim
        self._agent = None

    # ---- the agent economy (economy_port_year.py), the game's one economy ---------------------------
    @property
    def agent(self):
        """The game's agent economy (it opens when first asked, or at the game's start)."""
        if self._agent is None:
            from .economy_port_year import AgentEconomy
            self._agent = AgentEconomy(self._sim)
        return self._agent

    def _answering_agent(self):
        """The agent economy, opened, when it should answer; None while it opens (the opening reads the
        engine's own figures)."""
        agent = self.agent
        if self._opening:
            return None
        self.open_agent()
        return agent

    def acting_tile(self):
        """The tile the acting seat buys and sells on: where its household operates from."""
        return self._sim.labour.base_tile()

    def producer_capacities(self):
        """[(recipe id, capacity in runs)] of every producer in the opened agent economy; empty before it opens."""
        return self.agent.producer_capacities()

    def agent_prices_at(self, tile=None):
        """The agent economy's price of each good on a tile (the acting one by default) in coin, or None while it
        opens: what a buyer or seller there faces. A good the economy has no market for is absent."""
        agent = self._answering_agent()
        return None if agent is None else agent.prices_at(self.acting_tile() if tile is None else tile)

    def agent_offered_tonnes(self, material, tile=None):
        """Tonnes the sellers of a material in the tile's market area held at the last clearing; None while the
        economy opens or when the area has no book for it."""
        agent = self._answering_agent()
        return None if agent is None else agent.offered_tonnes(material, self.acting_tile() if tile is None else tile)

    def agent_prices(self):
        """The agent economy's prices by good in coin, or None to use the engine's."""
        agent = self._answering_agent()
        return None if agent is None else agent.answers(self._sim.acting_country())[0]

    def agent_wage_per_hour(self, trade):
        """The wage in the acting seat's own labour markets: its country's when it is a partner country's seat."""
        agent = self._answering_agent()
        return None if agent is None else agent.wage_per_hour(trade, self._sim.acting_country())

    def unskilled_wage(self):
        """Money one hour of the unskilled trade is paid in the agent economy, or None until the game's money is
        priced at the economy (the economy's opening reprices it, see reprice_opening_money)."""
        if not self._sim.state.economy.money_from_economy or self._opening:
            return None
        agent = self._answering_agent()
        return None if agent is None else agent.unskilled_wage_per_hour()

    def agent_country(self, country):
        """What the agent economy answers for a partner country in it, or None (not in it, or no wage yet)."""
        agent = self._answering_agent()
        return None if agent is None else agent.country(country)

    def agent_land_rent_per_hectare(self):
        """Mean rent per hectare-year of the agent economy's land market, in coin; None while it opens."""
        agent = self._answering_agent()
        return None if agent is None else agent.land_rent_per_hectare()

    def agent_need_floor_costs(self):
        """What a person's floor of each need costs a year on the home tiles, in coin; None while the economy opens."""
        agent = self._answering_agent()
        return None if agent is None else agent.need_floor_costs_per_person_year() or None

    def agent_need_floor_costs_at(self, tile=None):
        """What a person's floor of each need costs a year on a tile (the acting one by default), in coin; None
        while the economy opens."""
        agent = self._answering_agent()
        return None if agent is None else agent.need_floor_costs_at_tile(self.acting_tile() if tile is None else tile) or None

    def agent_land_rent_at(self, tile):
        """Rent per hectare-year on a tile in coin; None while the economy opens."""
        agent = self._answering_agent()
        return None if agent is None else agent.land_rent_at_tile(tile)

    def agent_land_rent_paid_by_tile(self):
        """Rent paid on each let tile last year in coin; empty while the economy opens."""
        agent = self._answering_agent()
        return {} if agent is None else agent.land_rent_paid_by_tile()

    def agent_output_tonnes_by_tile(self):
        """Tonnes of each good made on each tile last year; empty while the economy opens."""
        agent = self._answering_agent()
        return {} if agent is None else agent.output_tonnes_by_tile()

    def agent_idle_hours_by_trade(self):
        """(hours offered and not hired, hours offered) of each trade last year; empty while the economy opens."""
        agent = self._answering_agent()
        return {} if agent is None else agent.idle_hours_by_trade()

    def agent_people_by_trade(self):
        """Working people by trade in the agent economy's labour core; None while it opens or has not yet
        opened (opening it is the wage quotes' business, and slow)."""
        agent = self.agent
        return None if agent is None or self._opening else agent.people_by_trade()

    def agent_rate(self):
        agent = self._answering_agent()
        return None if agent is None else agent.rate()

    def agent_credit_room(self, borrower_id):
        """(True, room) when the agent economy answers, with room None before lenders have met; (False, None)
        while it opens."""
        agent = self._answering_agent()
        return (False, None) if agent is None else (True, agent.credit_room(borrower_id))

    def agent_price_response(self, material, landed_tonnes, taken_tonnes, tile=None):
        """Factor on a material's home price once `landed_tonnes` more come to market and `taken_tonnes` more are
        bought, by the agent economy's own demand and supply: at the port's market when no tile is named, else on
        that tile's own market area. None while it opens or has no book for the good; infinite when more is taken
        than the sellers hold."""
        agent = self._answering_agent()
        return None if agent is None else agent.price_response(material, landed_tonnes, taken_tonnes, tile)

    def main_material_of(self, commodity):
        """The first priced material of a commodity (its main product), or None when none is priced."""
        for material in self.materials_in(commodity) + [commodity]:
            if self.trade_quote(material) is not None:
                return material
        return None

    def agent_market_record(self, commodity):
        """{sold, unsold, unmet} tonnes the agent economy's markets of the commodity's main material had last year
        (`sim.economy.api.market_record`); None while the economy opens or when the commodity has no priced material."""
        agent = self._answering_agent()
        material = self.main_material_of(commodity)
        if agent is None or material is None:
            return None
        return agent.market_record(material)

    def agent_producers_by_good(self):
        """{good: [(tile, recipe id)]} of the producers the agent economy runs; None while it opens."""
        agent = self._answering_agent()
        return None if agent is None else agent.producers_by_good()

    def agent_worker_years_by_recipe(self):
        """Worker-years a year the agent economy's producers put into each recipe; None while it opens."""
        agent = self._answering_agent()
        return None if agent is None else agent.worker_years_by_recipe()

    def agent_producer_capacity_tonnes(self, material):
        """Tonnes a year the agent economy's producers can make of a material; None while it opens."""
        agent = self._answering_agent()
        return None if agent is None else agent.producer_capacity_tonnes(material)

    def agent_cohort_incomes(self):
        """[(people, yearly money income)] of the agent economy's household cohorts, poorest per head first,
        or None while the economy opens."""
        agent = self._answering_agent()
        if agent is None:
            return None
        return agent.cohort_incomes()

    def agent_cohort_land_rents(self, tiles=None):
        """[(people, rent received in coin)] in the order of `agent_cohort_incomes`, or None while the economy opens."""
        agent = self._answering_agent()
        return None if agent is None else agent.cohort_land_rents(tiles)

    def note_actor_sale(self, seller, material, tonnes, from_concerns):
        """An actor's tonnes of a material for the agent economy's market this year."""
        self.agent.note_sale(seller, material, tonnes, from_concerns)

    def note_actor_purchase(self, buyer, commodity, tonnes, budget):
        """An actor's tonnes of a commodity it bids for in the agent economy's market this year, with its budget in coin."""
        self.agent.note_purchase(buyer, commodity, tonnes, budget)

    def actor_held_units(self, buyer, material):
        """Durable units owned by an actor after settled market purchases."""
        return self.agent.held_units(buyer, material)

    def fleet_goods(self, buyer):
        """Naval goods the country's available recipes make, with the buyer's durable stock."""
        agent = self._answering_agent()
        if agent is not None:
            return agent.fleet_goods(buyer)
        from .economy_port_setup import _load, allowed_entries
        from .prices import default_production_entries
        production = default_production_entries()
        lives = _load("world", "service_lives.json").get("years", {})
        allowed = allowed_entries(production, set(self._sim.state.projects.granted))
        return [{"material": good, "life": float(lives.get(good, {}).get("years", 0.0)),
                 "held": 0.0, "crew": production[good]["naval_crew"]}
                for good in allowed if production[good].get("naval_crew")]

    def agent_volume_baseline(self, country=None):
        """{good: units the agent economy cleared in the first year it cleared any}; None while it opens."""
        agent = self._answering_agent()
        return None if agent is None else agent.volume_baseline(country)

    def agent_traded_volumes(self, country=None):
        """{good: units the agent economy traded last year}; None while it opens."""
        agent = self._answering_agent()
        return None if agent is None else agent.traded_volumes(country)

    def agent_opening_basket(self, country=None):
        """({good: units a year households bought at the opening}, {good: opening price in labour hours}) of the
        agent economy; None while it opens."""
        agent = self._answering_agent()
        return None if agent is None else agent.opening_basket(country)

    def producers_stamp(self):
        """Changes whenever the agent economy's producers might (each year it runs, and when it gains recipes)."""
        return 0 if self._agent is None else self._agent.producers_stamp()

    def agent_trades_good(self, material):
        """Whether the agent economy has a market for the material (False while it opens)."""
        agent = self._answering_agent()
        return agent is not None and agent.trades_good(material)

    def forget_actor_orders(self, actor_id):
        """An actor's sales and purchases noted for this year's market end."""
        self.agent.forget_orders(actor_id)

    _opening = False

    def run_agent_year(self):
        """The agent economy's year."""
        self.open_agent()
        self.agent.run_year()

    def flush_record(self):
        """Bring the saved copy of the agent economy up to date; the game's save calls this."""
        if self._agent is not None:
            self._agent.flush_record()

    def health(self, metals=(), staple=None):
        """The agent economy's health figures over the years this game has played (economy_port_health.py);
        None while the economy opens."""
        agent = self.agent
        if agent is None:
            return None
        from .economy_port_health import health_report
        return health_report(agent, metals, staple)

    def spin_up_result(self):
        """How the opening's hidden first stage ended: {"settled": whether it met SPIN_UP_TOLERANCE, "years", "gap"};
        empty while the economy opens or when no spin-up ran. A game that opened unsettled opened wherever the
        cycle stood."""
        agent = self.agent
        return {} if agent is None else agent.spin_up_result()

    def open_agent(self):
        """Open the agent economy (with its hidden spin-up) on the engine's own opening figures, then count
        the game's money at the economy's wage."""
        agent = self.agent
        if agent is None:
            return
        priced = self._sim.state.economy.money_from_economy
        if priced and agent.opened():
            return
        before = None if priced else self._sim.labour.money_per_labour_hour()
        if not agent.opened():
            self._opening = True
            try:
                agent.economy()
            finally:
                self._opening = False
        if not priced:
            opening_money.reprice_opening_money(self._sim, before)

    # ---- goods and labour: the two market facades ------------------------------------------
    @property
    def goods(self):
        """The goods market every buyer and seller asks (goods_market_api.GoodsMarket)."""
        return self._sim.goods_market

    @property
    def labour(self):
        """The labour market every employer asks (labour_market_api.LabourMarket)."""
        return self._sim.labour.market

    def material_price(self, material):
        """Money for one tonne of a material at today's market quote; 0.0 when it has no price."""
        quote = self._sim.material_purchase_cost(material, 1.0)
        return 0.0 if quote is None else quote[0]

    def material_prices(self):
        """Every priced material's money price per unit of the material (a read-only table)."""
        return self._sim._material_prices()

    def commodity_of(self, material):
        """The market a material trades in (several material keys can share one)."""
        return self._sim._material_tag(material)[0]

    def materials_in(self, commodity):
        """The material keys that trade in one market, sorted."""
        materials = sorted(material for material, group in self._sim._material_commodity_map().items()
                           if group == commodity)
        if materials:
            return materials
        from .prices import default_production_entries
        return ([commodity] if any(commodity in entry.get("outputs", {})
                                   for entry in default_production_entries().values()) else [])

    def trade_quote(self, material):
        """The market's quote for a material (buy and sell terms), or None if it has no price."""
        return self._sim.material_trade_quote(material)


    def purchase_cost(self, material, tonnes, already=0.0):
        """(money, mean money per tonne) to buy `tonnes` more, given `already` bought this year;
        None when the material has no price."""
        return self._sim.material_purchase_cost(material, tonnes, already)

    # ---- money --------------------------------------------------------------------------------
    def cost_scale(self):
        """The civilisation's scale on money amounts the tree and constants state in book coin."""
        return self._sim.price_index

    def money_per_labour_hour(self):
        """Money one hour of unskilled work is worth now."""
        return self._sim.labour.money_per_labour_hour()


    def coin_stock_units(self):
        """Units of money this society holds."""
        return self._sim.home_coin_stock_units()

    def coin_stock_value(self):
        """Money's worth of the metal in the coin this society holds, from its coin standard, at the metal's price
        (the same one cargo and the partners' coin are counted at)."""
        coin = self._sim.civ["coin_standard"]
        return self.coin_stock_units() * coin["kg_per_unit"] * (self._sim.goods_market.home_unit_price(coin["material"]) or 0.0)

    # ---- credit -------------------------------------------------------------------------------
    def base_rate(self):
        """The yearly lending rate in the civilisation's loanable-funds market."""
        return self._sim.market_rate()

    def credit_room(self, borrower_id):
        """What lenders will advance this borrower beyond what others owe; None before they have met."""
        return self._sim.market_credit_room(borrower_id)

    # ---- concerns and projects ----------------------------------------------------------------
    def concern_takings(self, node_id, ramp):
        """Yearly takings of one concern at a given ramp, before the market's price is applied."""
        return self._sim.concern_takings(node_id, ramp)

    def output_value(self):
        """Money's worth of the society's yearly output at today's prices."""
        sim = self._sim
        return sim.real_output_hours() * sim.labour.money_per_labour_hour() * sim.state.economy.output_factor

    def concern_gross(self, node_id):
        """Yearly takings of a concern once ramped up, with the market's price for its goods applied."""
        sim = self._sim
        return sim.concern_takings(node_id, 1.0) * sim.node_output_market_factor(sim.nodes[node_id])

    def concern_upkeep(self, node_id, capacity=1.0, cost_scale=None):
        """Yearly upkeep of a concern at a given capacity, without its crew's pay: an actor that runs a concern
        hires the crew through the labour market and pays wages there."""
        node = self._sim.nodes[node_id]
        return node["up"] * node_upkeep.non_labour_share(node) * (self.cost_scale() if cost_scale is None else cost_scale) * capacity

    def project_cost(self, node_id):
        """What a project costs to carry out now."""
        return self._sim.project_cost(node_id)


class EconomyPortMixin:
    """Gives `Sim` its port as `sim.economy`. Not saved: it holds nothing but the simulation."""

    @property
    def economy(self):
        port = self.__dict__.get("_economy_port")
        if port is None:
            port = self.__dict__["_economy_port"] = EconomyPort(self)
        return port
