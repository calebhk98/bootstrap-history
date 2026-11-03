"""What a producer's goods cost it to make: the reservation price it takes to the market.

Each producer (a firm's or the founder's concern, the incumbents) makes a good by the production entry it runs. Its cost is
that entry's unit cost at the economy's prices, wages, rate and rent, over the incumbents' cost of the same good, so the
market receives only a ratio. A producer that holds several entries for a good runs the cheapest. A producer whose plant is
built (every concern that exists) offers at its running cost, the entry's cost without the plant's repayment; the full
cost, with the repayment, stays the incumbents' reference and what a decision to build is judged against.

TEMPORARY HEURISTIC (CLAUDE.md 4.4): the entries a concern holds are its node's own and those of any node some producer
runs that make the same products; a producer-by-producer technique set would replace it. Inputs are priced at the
economy's price on the acting tile (the long-run cost where it has no market for the good), not at what each buyer was
charged. retire: ONE_PRICE_OWNER_PLAN.md stage 5."""
from typing import Any, Dict, Optional, Tuple

from sim.assembly.api import Part

from . import rules
from .entry_cost import CostBook
from .making_cost import LAND_MATERIAL

RATE_DECIMALS = 4


class CostBooks(Part):

    def __init__(self, module):
        super().__init__(module)
        self._cost_book_cache: Optional[Tuple] = None        # (stamp, cost book, {ratios})

    def economy_cost_book(self) -> CostBook:
        """A `CostBook` at the economy's prices, wages, lending rate and land rent as they stand. Ore carries no rent here:
        the mine's own cost is the recipe that digs it."""
        prices = self.needs.household_prices()
        land_rent = self.needs.agent_land_rent() or 0.0
        wages: Dict[str, float] = {}

        def input_price_of(material: str) -> Optional[float]:
            if material == LAND_MATERIAL:
                return None     # land is charged its rent (rent_of), not a price in the table
            price = prices.get(material)
            return price if price is not None and price > 0.0 else None

        def wage_of(trade: str) -> float:
            if trade not in wages:
                wage = self.needs.agent_wage[trade]
                wages[trade] = wage if wage else self.needs.labour_quote(trade)
            return wages[trade]

        def rent_of(key: str) -> float:
            return land_rent if key == LAND_MATERIAL else 0.0

        return CostBook(input_price_of, wage_of, float(self.needs.market_rate()), rent_of=rent_of,
                        civilization=self.needs.civilisation(), production=None)

    def cost_book(self) -> Tuple[Any, CostBook, Dict[Any, Any]]:
        """What entries are costed against: the economy's prices, wages, rate and rent, remembered while the economy's
        prices and the techniques in use stand. (stamp, book, {ratios})."""
        prices = self.needs.household_prices()
        stamp = (prices, round(self.needs.market_rate(), RATE_DECIMALS), self.needs.year(), self.needs.techniques_in_use())
        cache = self._cost_book_cache
        if (cache is None or cache[0][0] is not prices or cache[0][1:3] != stamp[1:3]
                or cache[0][3] is not stamp[3]):
            cache = self._cost_book_cache = (stamp, self.economy_cost_book(), {})
        return cache

    def reference_entry(self, material: str) -> Optional[str]:
        """The entry the incumbents make `material` by (the cheapest in their techniques at the economy's prices); for a
        good they do not make, the cheapest in the techniques now run."""
        book = self.cost_book()[1]
        for held in (frozenset(self.needs.techniques_granted()), self.needs.techniques_in_use()):
            chosen = book.cheapest_entry(material, held)
            if chosen is not None:
                return chosen
        return None

    def entry_cost_ratio(self, entry_key: str, material: str, running: bool = False) -> Optional[float]:
        """A unit of `material` made by this entry over the same made by the incumbents' entry, both at the economy's
        prices; None where either cannot be costed. `running` leaves the entry's plant repayment out (a producer whose plant
        is built), the incumbents' cost staying the full one."""
        _stamp, book, ratios = self.cost_book()
        key = (entry_key, material, running)
        if key not in ratios:
            reference_key = self.reference_entry(material)
            own = (book.running_unit_cost if running else book.unit_cost)(entry_key, material)
            reference = book.unit_cost(reference_key, material) if reference_key else None
            ratios[key] = rules.cost_ratio(own, reference)
        return ratios[key]
