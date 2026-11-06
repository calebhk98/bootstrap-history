"""The markets module's port over the agent economy.

The tree, the founder, projects, actors and screens ask this port about prices, wages, rates, money
and what a concern takes, and post their purchases, sales and hires through it. They do not read
the price tables, the coin stock or the market book directly, so the model behind the port can
change without them knowing. The port files (port*.py) are the only code that imports `sim.economy`;
the agent economy answers, and the engine's own opening figures answer
while it opens. The port reads the game through `PortWorld` (port_world.py).
"""
from sim.prices.api import prices as price_solver

from . import port_actors, port_goods_orders
from .port_setup import allowed_entries
from .commands import RepriceOpeningMoney


class EconomyPort:
    """Questions and transactions about the economy, for one simulation."""

    def __init__(self, sim):
        self._sim = sim
        self._parts = None

    @property
    def world(self):
        """What the port reads of the game (port_world.py)."""
        return self._sim

    # ---- the agent economy (port_parts.py), the game's one economy ---------------------------
    @property
    def parts(self):
        """The parts over the agent economy (port_parts.py); the economy opens when first asked, or at the game's start."""
        if self._parts is None:
            from .port_parts import AgentParts
            self._parts = AgentParts(self._sim)
        return self._parts

    @property
    def agent(self):
        """The live agent economy and its record (agent_economy.py)."""
        return self.parts.agent

    _opening = False

    @property
    def opening(self):
        """Whether the agent economy is opening now (its hidden spin-up runs on the engine's own opening figures)."""
        return self._opening

    def answering(self):
        """The parts over the agent economy, opened, when they should answer; None while it opens (the opening reads the
        engine's own figures). Every read that is None or empty while the economy opens asks this first."""
        if self._opening:
            return None
        self.open_agent()
        return self.parts

    def acting_tile(self):
        """The tile the acting seat buys and sells on: where its household operates from."""
        return self._sim.labour.base_tile()

    # ---- the reads the goods market makes (goods_market.py, goods_pricing.py, goods_offers.py) ------------------------
    def agent_prices_at(self, tile=None):
        """The agent economy's price of each good on a tile (the acting one by default) in coin, or None while it
        opens: what a buyer or seller there faces. A good the economy has no market for is absent."""
        parts = self.answering()
        return None if parts is None else parts.prices.prices_at(self.acting_tile() if tile is None else tile)

    def agent_price_kind(self, good):
        """What the agent economy's shown price of a good is (traded, a named quote or an estimate); None while it
        opens or when the economy shows none."""
        parts = self.answering()
        return None if parts is None else parts.prices.price_kind(good)

    def agent_offered_tonnes(self, material, tile=None):
        """Tonnes the sellers of a material in the tile's market area held at the last clearing; None while the
        economy opens or when the area has no book for it."""
        parts = self.answering()
        return None if parts is None else parts.prices.offered_tonnes(material, self.acting_tile() if tile is None else tile)

    def agent_prices(self):
        """The agent economy's prices by good in coin, or None to use the engine's."""
        parts = self.answering()
        return None if parts is None else parts.prices.answers(self._sim.scenario.acting_country())[0]

    def agent_need_floor_costs_at(self, tile=None):
        """What a person's floor of each need costs a year on a tile (the acting one by default), in coin; None
        while the economy opens."""
        parts = self.answering()
        return None if parts is None else parts.households.need_floor_costs_at_tile(self.acting_tile() if tile is None else tile) or None

    def agent_price_response(self, material, landed_tonnes, taken_tonnes, tile=None):
        """Factor on a material's home price once `landed_tonnes` more come to market and `taken_tonnes` more are
        bought, by the agent economy's own demand and supply: at the port's market when no tile is named, else on
        that tile's own market area. None while it opens or has no book for the good; infinite when more is taken
        than the sellers hold."""
        parts = self.answering()
        return None if parts is None else parts.prices.price_response(material, landed_tonnes, taken_tonnes, tile)

    def main_material_of(self, commodity):
        """The first priced material of a commodity (its main product), or None when none is priced."""
        for material in self.materials_in(commodity) + [commodity]:
            if self.goods.quote(material) is not None:
                return material
        return None

    def agent_market_record(self, commodity):
        """{sold, unsold, unmet} tonnes the agent economy's markets of the commodity's main material had last year
        (`sim.economy.api.market_record`); None while the economy opens or when the commodity has no priced material."""
        parts = self.answering()
        material = self.main_material_of(commodity)
        if parts is None or material is None:
            return None
        return parts.prices.market_record(material)

    def agent_good_market_record(self, good):
        """{sold, unsold, unmet} tonnes the agent economy's markets of a good the economy trades had last year; None
        while the economy opens or when it has no market for the good."""
        parts = self.answering()
        if parts is None or not parts.prices.trades_good(good):
            return None
        return parts.prices.market_record(good)

    def seat_committed_money(self, seat_id):
        """Money the seat's posted buy orders reserve, plus the staff funding the port will draw from it this year."""
        agent = self.agent
        committed = port_goods_orders.committed_money(port_goods_orders.posted_orders(agent.stored, seat_id))
        if not agent.opened():
            return committed
        return committed + port_goods_orders.staff_funding_coin(self._sim, agent.economy(), seat_id, agent.tile_in_economy)

    def fleet_goods(self, buyer):
        """Naval goods the country's available recipes make, with the buyer's durable stock."""
        parts = self.answering()
        if parts is not None:
            return parts.trade.fleet_goods(buyer)
        production = price_solver.default_production_entries()
        lives = self._sim.materials.service_life_years()
        allowed = allowed_entries(production, set(self._sim.production.techniques_granted()))
        return port_actors.fleet_goods(production, allowed, lambda good: lives.get(good, 0.0), lambda _good: 0.0)

    def materials_in(self, commodity):
        """The material keys that trade in one market, sorted."""
        materials = sorted(material for material, group in self._sim.materials.commodity_map().items()
                           if group == commodity)
        if materials:
            return materials
        return ([commodity] if any(commodity in entry.get("outputs", {})
                                   for entry in price_solver.default_production_entries().values()) else [])

    # ---- the economy's life ----------------------------------------------------------------------
    def flush_record(self):
        """Bring the saved copy of the agent economy up to date; the game's save calls this."""
        if self._parts is not None:
            self._parts.agent.flush_record()

    def open_agent(self):
        """Open the agent economy (with its hidden spin-up) on the engine's own opening figures, then count
        the game's money at the economy's wage."""
        agent = self.agent
        priced = self._sim.money_from_economy()
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
            self._sim.send(RepriceOpeningMoney(before))

    # ---- goods and labour: the two market facades ------------------------------------------
    @property
    def goods(self):
        """The goods market every buyer and seller asks (goods_market.GoodsMarket)."""
        return self._sim.goods_market

    @property
    def labour(self):
        """The labour market every employer asks (labour_market_api.LabourMarket)."""
        return self._sim.labour.market
