"""The one door between the engine and the economy.

The tree, the founder, projects, actors and screens ask this port about prices, wages, rates, money
and what a concern takes, and post their purchases, sales and hires through it. They do not read
the price tables, the coin stock or the market book directly, so the model behind the port can
change without them knowing. This is the only engine module that may import `sim.economy`
(sim/tests/test_economy_imports.py); today every answer still comes from the engine's own mixins.
"""


class EconomyPort:
    """Questions and transactions about the economy, for one simulation."""

    def __init__(self, sim):
        self._sim = sim

    # ---- goods and labour: the two market facades ------------------------------------------
    @property
    def goods(self):
        """The goods market every buyer and seller asks (goods_market_api.GoodsMarket)."""
        return self._sim.goods_market

    @property
    def labour(self):
        """The labour market every employer asks (labour_market_api.LabourMarket)."""
        return self._sim.labour_market

    def material_price(self, material):
        """Money for one tonne of a material at today's market quote; 0.0 when it has no price."""
        quote = self._sim.material_purchase_cost(material, 1.0)
        return 0.0 if quote is None else quote[0]

    def material_prices(self):
        """Every priced material's money price per unit of the material (a read-only table)."""
        return self._sim._material_prices()

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
        return self._sim.money_per_labour_hour()

    def book_money(self, amount):
        """A book-coin amount in this civilisation's money now."""
        return self._sim.book_money(amount)

    def price_level(self):
        """The level of money prices against the opening year (1.0 at the opening)."""
        return self._sim.home_price_level()

    def wage_pressure(self):
        """How far wages stand above their opening level from a shortage of people."""
        return self._sim.wage_index

    def coin_stock_units(self):
        """Units of money this society holds."""
        return self._sim.home_coin_stock_units()

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
