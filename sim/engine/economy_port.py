"""The one door between the engine and the economy.

The tree, the founder, projects, actors and screens ask this port about prices, wages, rates, money
and what a concern takes, and post their purchases, sales and hires through it. They do not read
the price tables, the coin stock or the market book directly, so the model behind the port can
change without them knowing. This is the only engine module that may import `sim.economy`
(sim/tests/test_economy_imports.py); today every answer still comes from the engine's own mixins.
"""


def switch_requested(cfg):
    """True unless a new game opts out of the agent economy (config `agent_economy` False); the
    environment variable named in economy_port_year.SWITCH_ENVIRONMENT overrides, for comparing runs."""
    from .economy_port_year import switch_requested as requested
    return requested(cfg)


class EconomyPort:
    """Questions and transactions about the economy, for one simulation."""

    def __init__(self, sim):
        self._sim = sim
        self._agent = None

    # ---- the agent economy (economy_port_year.py), when the game runs on it ---------------------
    @property
    def agent(self):
        """The agent economy when this game runs on it and it has opened; else None."""
        if not self._sim.state.economy.agent_economy.get("on") or not self._has_territory():
            return None
        if self._agent is None:
            from .economy_port_year import AgentEconomy
            self._agent = AgentEconomy(self._sim)
        return self._agent

    def _has_territory(self):
        """A civilisation that holds no tiles has no markets to run; it stays on the engine's economy."""
        homes = (tuple(self._sim.civ.get("home_regions") or ()), tuple(self._sim.civ.get("home_tiles") or ()))
        cached = self.__dict__.get("_territory")
        if cached is None or cached[0] != homes:
            from .economy_port_setup import civilisation_tiles
            cached = self.__dict__["_territory"] = (homes, bool(civilisation_tiles(self._sim.civ, self._sim.world_map)[0]))
        return cached[1]

    def _answering_agent(self):
        """The agent economy, opened, when it should answer; None while off or while it opens (the
        opening reads the engine's own figures)."""
        agent = self.agent
        if agent is None or self._opening:
            return None
        self.open_agent()
        return agent

    def agent_price_ratio(self, materials):
        """The agent economy's price over the engine's own cost for a market, or None to use the engine's."""
        agent = self._answering_agent()
        return None if agent is None else agent.price_ratio(materials, self._sim._material_prices())

    def agent_wage_per_hour(self, trade):
        agent = self._answering_agent()
        return None if agent is None else agent.wage_per_hour(trade)

    def agent_land_rent_per_hectare(self):
        """Mean rent per hectare-year of the agent economy's land market, in coin; None while it is off."""
        agent = self._answering_agent()
        return None if agent is None else agent.land_rent_per_hectare()

    def agent_land_rent_paid_by_tile(self):
        """Rent paid on each let tile last year in coin; empty while the agent economy is off."""
        agent = self._answering_agent()
        return {} if agent is None else agent.land_rent_paid_by_tile()

    def agent_people_by_trade(self):
        """Working people by trade in the agent economy's labour core; None while it is off or not yet
        opened (opening it is the wage quotes' business, and slow)."""
        agent = self.agent
        return None if agent is None or self._opening else agent.people_by_trade()

    def agent_rate(self):
        agent = self._answering_agent()
        return None if agent is None else agent.rate()

    def agent_credit_room(self, borrower_id):
        """(True, room) when the agent economy answers, with room None before lenders have met; (False, None)
        while it is off."""
        agent = self._answering_agent()
        return (False, None) if agent is None else (True, agent.credit_room(borrower_id))

    def agent_price_response(self, material, landed_tonnes, taken_tonnes):
        """Factor on a material's home price once `landed_tonnes` more come to market and `taken_tonnes` more are
        bought, by the agent economy's own demand and supply; None while it is off or has no book for the good."""
        agent = self._answering_agent()
        return None if agent is None else agent.price_response(material, landed_tonnes, taken_tonnes)

    def agent_cohort_incomes(self):
        """[(people, yearly money income)] of the agent economy's household cohorts, poorest per head first,
        or None while the agent economy is off."""
        agent = self._answering_agent()
        if agent is None:
            return None
        return agent.cohort_incomes()

    def runs_agent_economy(self):
        return self.agent is not None

    _opening = False

    def run_agent_year(self):
        """The agent economy's year, in place of the engine's own clearing; False when the switch is off."""
        agent = self.agent
        if agent is None:
            return False
        self.open_agent()
        agent.run_year()
        return True

    def health(self, metals=(), staple=None):
        """The agent economy's health figures over the years this game has played (economy_port_health.py);
        None while the agent economy is off."""
        agent = self.agent
        if agent is None:
            return None
        from .economy_port_health import health_report
        return health_report(agent, metals, staple)

    def open_agent(self):
        """Open the agent economy (with its hidden spin-up) on the engine's own opening figures."""
        agent = self.agent
        if agent is None or agent.opened():
            return
        self._opening = True
        try:
            agent.economy()
        finally:
            self._opening = False

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
        return sorted(material for material, group in self._sim._material_commodity_map().items()
                      if group == commodity)

    def trade_quote(self, material):
        """The market's quote for a material (buy and sell terms), or None if it has no price."""
        return self._sim.material_trade_quote(material)

    def offer_sale(self, seller_id, material, tonnes, from_concerns=None):
        """An actor puts `tonnes` on the market this year; one whose own concerns made it, given as
        [(node id, tonnes)], will not sell below what they cost it to make."""
        sim = self._sim
        reservation = sim.concerns_reservation_ratio(from_concerns, material) if from_concerns else None
        sim.goods_market.note_sale(seller_id, self.commodity_of(material), tonnes, reservation)

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

    def wage_pressure(self):
        """How far wages stand above their opening level from a shortage of people."""
        return self._sim.wage_index

    def coin_stock_units(self):
        """Units of money this society holds."""
        return self._sim.home_coin_stock_units()

    def coin_stock_value(self):
        """Money's worth of the metal in the coin this society holds, from its coin standard."""
        coin = self._sim.civ["coin_standard"]
        return self.coin_stock_units() * coin["kg_per_unit"] * self.material_prices().get(coin["material"], 0.0)

    # ---- credit -------------------------------------------------------------------------------
    def base_rate(self):
        """The yearly lending rate in the civilisation's loanable-funds market."""
        return self._sim.market_rate()

    def credit_room(self, borrower_id):
        """What lenders will advance this borrower beyond what others owe; None before they have met."""
        return self._sim.market_credit_room(borrower_id)

    def report_interest_paid(self, amount):
        """Interest a borrower paid this year, shared among lenders at the year's close."""
        self._sim.note_interest_paid(amount)

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
        return (sim.concern_takings(node_id, 1.0) * sim.goods_market_factor(node_id)
                * sim.node_output_market_factor(sim.nodes[node_id]))

    def concern_upkeep(self, node_id, capacity=1.0):
        """Yearly upkeep of a concern at a given capacity."""
        return self._sim.nodes[node_id]["up"] * self.cost_scale() * capacity

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
