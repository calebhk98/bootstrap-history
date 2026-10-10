"""A long-run price repays the plant at the market rate, so a concern selling at it earns a return.

The solver charges each production entry's plant its build bill over its service life; Complaints/319
found that left a concern priced at cost earning its staff and nothing above. The charge now repays the
build bill with interest at the civilisation's market rate (`capital_recovery_factor`), so a concern
selling at the solved price earns its wages plus that return."""

QUICK_TOPIC = True

import unittest
from unittest import mock

from sim.engine import solve_prices
from sim.engine import data, energy_prices, incumbent_prices, node_output, node_revenue, prices
from sim.world import capital_market
from sim.labour.labour_market import production_data

# Entries that state a plant and gate a node, whose inputs at solved prices cost more than what they
# make: a technique dearer than the one that sets the price, so it adds nothing a staff could be paid from.
INPUTS_DEARER_THAN_PRODUCT = {"mechanical_mj_motor"}

WAGES = {"labourer": 1.0}
BUILD_LABOUR_HOURS = 20000.0
LIFE_YEARS = 20.0
PLANT_OUTPUT_PER_YEAR = 1000.0


def works_entry():
    return {"outputs": {"widget_kg": 10.0}, "inputs": {"ore_kg": 10.0}, "labour_hours": {"labourer": 5.0},
            "requires_node": "widget_works", "operated_by": ["widget_works"],
            "capital": [{"good": "pan", "build_labour_hours": {"labourer": BUILD_LABOUR_HOURS},
                         "service_life_years": LIFE_YEARS, "annual_output_at_basis": PLANT_OUTPUT_PER_YEAR}]}


def unit_price(rate):
    _cost, prices = solve_prices.recipe_cost_and_allocation(
        "widget_kg", works_entry(), {"ore_kg": 1.0}, WAGES, interest_rate=rate)
    return prices["widget_kg"]


class CapitalRecoveryFactor(unittest.TestCase):

    def test_a_nil_rate_is_depreciation_alone(self):
        self.assertAlmostEqual(capital_market.capital_recovery_factor(0.0, 20.0), 1.0 / 20.0)

    def test_the_yearly_share_repays_the_bill_with_interest_on_what_is_unpaid(self):
        rate, life = 0.12, 25.0
        share = capital_market.capital_recovery_factor(rate, life)
        owed = 1.0
        for _year in range(int(life)):
            owed = owed * (1.0 + rate) - share
        self.assertAlmostEqual(owed, 0.0, places=9)

    def test_a_dearer_rate_asks_more_of_the_same_plant(self):
        self.assertGreater(capital_market.capital_recovery_factor(0.2, 20.0),
                           capital_market.capital_recovery_factor(0.1, 20.0))


class SolvedPriceCarriesTheReturn(unittest.TestCase):

    def test_the_price_covers_materials_labour_and_the_plants_repayment_at_the_market_rate(self):
        rate = 0.12
        share = capital_market.capital_recovery_factor(rate, LIFE_YEARS)
        batch_cost = 10.0 * 1.0 + 5.0 * 1.0
        plant_per_unit = BUILD_LABOUR_HOURS * share / PLANT_OUTPUT_PER_YEAR
        self.assertAlmostEqual(unit_price(rate), batch_cost / 10.0 + plant_per_unit)

    def test_a_dearer_market_rate_raises_the_price_of_what_a_plant_makes(self):
        self.assertGreater(unit_price(0.2), unit_price(0.1))
        self.assertGreater(unit_price(0.1), unit_price(0.0))

    def test_an_entry_with_no_plant_is_unmoved_by_the_rate(self):
        entry = works_entry()
        entry["capital"] = []
        prices = [solve_prices.recipe_cost_and_allocation("widget_kg", entry, {"ore_kg": 1.0}, WAGES,
                                                          interest_rate=rate)[1]["widget_kg"]
                  for rate in (0.0, 0.3)]
        self.assertAlmostEqual(prices[0], prices[1])


class ConcernEarnsItsReturn(unittest.TestCase):

    def earnings(self, rate):
        """(revenue less staff, build hours of its plant) of a concern selling at its solved price."""
        node = {"id": "widget_works", "kind": "ENGINEERING", "sch": 0.0,
                "art": 0.0, "annual_output_t": 0.0, "lab": {}, "cap_hours": 0.0, "_material_hours": 0.0}
        goods = {"ore_kg": 1.0, "widget_kg": unit_price(rate)}
        table = {"widget_works_entry": works_entry()}
        with mock.patch("sim.labour.api.production_data", return_value=table):
            node_revenue.apply_revenue([node], goods, WAGES, 1.0, energy_prices.pool_only(goods))
        self.assertEqual(node["_revenue_basis"], "output")
        staff = node["_upkeep_hours_parts"]["staff"]
        return node["rev_hours"] - staff, node["_upkeep_hours_parts"]["plant_build_hours"]

    def test_a_concern_priced_at_its_solved_cost_earns_wages_plus_a_return_on_its_plant(self):
        rate = 0.12
        # no staff is held, so the plant bounds the output: the whole plant runs
        surplus, build_hours = self.earnings(rate)
        self.assertGreaterEqual(surplus, build_hours * rate * (1 - 1e-9))

    def test_with_no_return_charged_a_concern_earns_less_than_with_it(self):
        self.assertLess(self.earnings(0.0)[0], self.earnings(0.12)[0])

    def test_the_surplus_repays_what_the_plant_wears_and_then_some(self):
        surplus, build_hours = self.earnings(0.12)
        self.assertGreater(surplus, build_hours / LIFE_YEARS)


class MakersWithAStatedPlant(unittest.TestCase):

    def test_a_maker_with_a_stated_plant_adds_its_staff_cost_at_its_solved_price(self):
        _tree, document, _nodes, wages, goods = data.load()
        civ = data.load_civ()
        energy = energy_prices.graded(civ["starting_techs"], document, goods, civ["id"])
        short = set()
        for key, entry in production_data().items():
            if not (entry.get("requires_node") and entry.get("capital") and entry.get("outputs")):
                continue
            if any(material not in goods for material in entry["outputs"]):
                continue
            staff = sum(wages.get(trade, 0.0) * hours for trade, hours in (entry.get("labour_hours") or {}).items())
            if node_output._net_per_batch(entry, goods, energy) < staff * (1 - 1e-9):
                short.add(key)
        self.assertLessEqual(short, INPUTS_DEARER_THAN_PRODUCT, "adds less than its staff: %s" % sorted(short))
        self.assertFalse(INPUTS_DEARER_THAN_PRODUCT - short,
                         "now adds its staff cost, remove from the list: %s" % sorted(INPUTS_DEARER_THAN_PRODUCT - short))


# Extraction streams: a deposit or a parent stream sets their output, so no plant of their own is stated.
def is_extraction_stream(entry):
    return bool(entry.get("extracted_from")) and not entry.get("inputs")


class OutputEarningEntriesStateAPlant(unittest.TestCase):
    """A node earns only from the entries that name it in `operated_by`; an entry with no plant leaves it
    earning its staff's wages and nothing above (Complaints/319), so each such entry states one."""

    def operated_entries(self):
        return {key: entry for key, entry in production_data().items()
                if entry.get("operated_by") and not is_extraction_stream(entry)}

    def test_every_entry_run_by_an_output_earning_node_states_a_plant(self):
        bare = sorted(key for key, entry in self.operated_entries().items() if not entry.get("capital"))
        self.assertEqual(bare, [], "operated_by entries with no capital: %s" % bare)

    def test_every_plant_item_states_its_bill_life_capacity_and_basis(self):
        for key, entry in self.operated_entries().items():
            for item in entry.get("capital") or []:
                where = "%s / %s" % (key, item.get("good"))
                self.assertTrue(item.get("build_materials") or item.get("build_labour_hours"), where)
                self.assertGreater(float(item.get("service_life_years") or 0.0), 0.0, where)
                self.assertGreater(float(item.get("annual_output_at_basis") or 0.0), 0.0, where)
                self.assertGreaterEqual(len(item.get("capital_basis") or ""), 50, where)
                self.assertIn(item.get("conf"), ("A", "B", "C", "D"), where)


class InventoryAndLiveRate(unittest.TestCase):
    """Stock carried costs the market rate (Complaints/337), and the solver is keyed on a band of the live rate."""

    def price(self, rate, holding_years):
        entry = works_entry()
        entry["capital"] = []
        entry["holding_years"] = holding_years
        return solve_prices.recipe_cost_and_allocation(
            "widget_kg", entry, {"ore_kg": 1.0}, WAGES, interest_rate=rate)[1]["widget_kg"]

    def test_inputs_held_for_a_year_cost_the_rate_on_what_was_laid_out(self):
        inputs_per_unit = 10.0 * 1.0 / 10.0
        self.assertAlmostEqual(self.price(0.1, 1.0) - self.price(0.1, 0.0), inputs_per_unit * 0.1)

    def test_nothing_is_held_unless_the_entry_says_so(self):
        self.assertAlmostEqual(self.price(0.3, 0.0), self.price(0.0, 0.0))

    def test_a_longer_hold_or_a_dearer_rate_costs_more(self):
        self.assertGreater(self.price(0.1, 2.0), self.price(0.1, 1.0))
        self.assertGreater(self.price(0.2, 1.0), self.price(0.1, 1.0))

    def test_ripening_and_curing_entries_state_how_long_the_stock_is_held(self):
        held = {key for key, entry in production_data().items() if entry.get("holding_years")}
        self.assertLessEqual({"leather_kg", "nitre_kg"}, held)

    def test_the_starting_rate_is_its_own_band(self):
        self.assertEqual(prices.band_interest_rate(0.05, 0.05), 0.05)

    def test_rates_within_a_band_share_it_and_a_far_rate_does_not(self):
        start = 0.05
        near = prices.band_interest_rate(start + prices.INTEREST_RATE_BAND * 0.3, start)
        self.assertEqual(near, start)
        far = prices.band_interest_rate(start + prices.INTEREST_RATE_BAND * 3.2, start)
        self.assertGreater(far, start)
        self.assertEqual(far, prices.band_interest_rate(far + prices.INTEREST_RATE_BAND * 0.2, start))

    def test_a_negative_rate_is_not_charged(self):
        self.assertEqual(prices.band_interest_rate(-0.5, 0.05), 0.0)


class IncumbentTablesFollowTheLiveRate(unittest.TestCase):

    def sim(self, rates):
        class Stub(incumbent_prices.IncumbentPricesMixin):
            civ = {"id": "x", "starting_interest_rate": 0.05}
            state = mock.Mock(projects=mock.Mock(granted=frozenset({"a"})))
            farm_land = mock.Mock(hectares=100.0)

            def techniques_in_use(self):
                return self.state.projects.granted

            def market_rate(self):
                return rates[0]
        return Stub()

    def test_the_solve_takes_the_banded_live_rate_and_repeats_only_when_a_band_moves(self):
        rates = [0.05]
        stub = self.sim(rates)
        with mock.patch("sim.engine.data.calculated_goods_table", return_value=({}, {})) as solve:
            stub._price_tables()
            rates[0] = 0.05 + prices.INTEREST_RATE_BAND * 0.2
            stub._price_tables()
            self.assertEqual(solve.call_count, 1)
            rates[0] = 0.05 + prices.INTEREST_RATE_BAND * 4
            stub._price_tables()
            self.assertEqual(solve.call_count, 2)
            self.assertAlmostEqual(solve.call_args.kwargs["interest_rate"], 0.09)

    def test_a_market_rate_that_needs_the_prices_answers_the_starting_rate_instead_of_recursing(self):
        stub = self.sim([0.2])
        stub.market_rate = lambda: stub._banded_market_rate() + 0.2
        self.assertAlmostEqual(stub._banded_market_rate(), 0.25)


if __name__ == "__main__":
    unittest.main()
