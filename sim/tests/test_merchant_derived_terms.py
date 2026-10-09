"""Complaints/379: the merchants' remaining terms are derived (crew as a choice, the markup from the
destination's price response, houses owning several carriers, selling time and the sailing season, the
class's capital from the capital market, retention from the merchants' own return, provisions restocked
rather than floored, routes chosen with provisions charged). Pure functions and stub engines only: no
game is built.
"""
QUICK_TOPIC = True

import math
import unittest

from sim.engine import foreign_route_choice, foreign_routes, foreign_traders
from sim.geography import freight_cost, provisions, sea_freight, transport
from sim.geography import api as geography
from sim.world import market, merchant_house, merchant_terms

CART = transport.draught_freight_physical_inputs(transport.OX, 2, transport.CART, transport.DIRT_TRACK)


class CrewChoiceTests(unittest.TestCase):

    def test_a_cargo_worth_nothing_buys_no_defenders(self):
        self.assertEqual(sea_freight.defenders_to_hire(12, 1.0, 0.0), 0)

    def test_a_dearer_cargo_hires_more_defenders(self):
        counts = [sea_freight.defenders_to_hire(12, 1.0, value) for value in (1.0e3, 1.0e5, 1.0e7, 1.0e9)]
        self.assertEqual(counts, sorted(counts))
        self.assertGreater(counts[-1], counts[0])

    def test_dearer_hands_hire_fewer_defenders(self):
        self.assertGreaterEqual(sea_freight.defenders_to_hire(12, 0.5, 1.0e7),
                                sea_freight.defenders_to_hire(12, 50.0, 1.0e7))

    def test_the_choice_never_costs_more_than_sailing_with_the_rig_crew_alone(self):
        rig, wage_per_day, value = 12, 2.0, 1.0e7
        extra = sea_freight.defenders_to_hire(rig, wage_per_day, value)
        self.assertGreater(extra, 0)

        def cost(defenders):
            return (defenders * wage_per_day * 1000.0 / sea_freight.ground_km_per_day()
                    + value * sea_freight.hull_loss_per_thousand_km(rig + defenders))
        self.assertLess(cost(extra), cost(0))

    def test_the_rig_crew_stays_the_floor_and_defenders_are_extra(self):
        crew = sea_freight.crew_to_sail(sea_freight.MERCHANT_HULL_CARGO_TONNES)
        extra = sea_freight.defenders_to_hire(crew, 0.1, 1.0e8)
        inputs = sea_freight.sailing_freight_physical_inputs(crew=crew + extra)
        self.assertEqual(inputs.carried_kg_per_day, provisions.person_provisions_kg_per_day(crew + extra))


class _Labour:
    def wage_per_hour(self, trade):
        return 2.0


class _Economy(foreign_routes.ForeignRoutesMixin):
    LAND_FREIGHT_TEAM_SIZE = 2.0
    FREIGHT_FEED_PRICE_MATERIAL = "wheat_kg"
    FREIGHT_DRIVER_WAGE_TRADE = "labourer"

    def __init__(self, grain_price=1.0):
        self.prices = {"wheat_kg": grain_price, "wood_kg": 0.5, "coal_kg": 0.4, "iron_bar_kg": 8.0,
                       "ox": 4000.0, "mule": 3000.0}
        self.labour = _Labour()
        self.world_map = geography.open_map()

    def _material_prices(self):
        return self.prices

    def _material_price_per_kg(self, tag):
        return self.prices.get(tag)

    def _land_freight_physical_inputs(self):
        return transport.draught_freight_physical_inputs(transport.OX, 2, transport.CART, transport.DIRT_TRACK)

    def market_rate(self):
        return 0.05


class EngineCrewTests(unittest.TestCase):

    def test_the_hull_is_crewed_beyond_its_rig_where_the_cargo_it_risks_is_dear(self):
        cheap, dear = _Economy(0.001), _Economy(100.0)
        rig = sea_freight.crew_to_sail(sea_freight.MERCHANT_HULL_CARGO_TONNES)
        self.assertGreaterEqual(cheap._sea_crew(), rig)
        self.assertGreater(dear._sea_crew(), cheap._sea_crew())

    def test_the_carrier_model_and_the_loss_rate_use_the_chosen_crew(self):
        economy = _Economy(100.0)
        inputs, _prices, _days, loss = economy._carrier_models()[foreign_routes.SEA_MODE]
        self.assertEqual(inputs.carried_kg_per_day, provisions.person_provisions_kg_per_day(economy._sea_crew()))
        self.assertEqual(loss, sea_freight.hull_loss_per_thousand_km(economy._sea_crew()))


class RestockingTests(unittest.TestCase):

    def test_a_leg_within_a_stage_is_provisioned_as_before(self):
        km = 3.0 * CART.distance_per_day_km
        self.assertEqual(provisions.restocked_share(CART, km, 10.0), provisions.delivered_share(CART, km))

    def test_beyond_a_stage_the_share_stays_where_a_stage_leaves_it(self):
        stage = provisions.restocked_share(CART, 1.0e5, provisions.RESTOCK_INTERVAL_DAYS)
        self.assertGreater(stage, 0.0)
        self.assertEqual(stage, provisions.restocked_share(CART, 1.0e6, provisions.RESTOCK_INTERVAL_DAYS))

    def test_without_restocking_the_whole_leg_is_one_stage(self):
        self.assertEqual(provisions.restocked_share(CART, 200.0, None), provisions.delivered_share(CART, 200.0))

    def test_an_overlong_leg_is_priced_finite_without_a_floor(self):
        cost = freight_cost.leg_money_per_tonne(1.0, CART, 1.0e6, restock_days=provisions.RESTOCK_INTERVAL_DAYS)
        self.assertLess(cost, float("inf"))
        self.assertGreater(cost, 1.0e6)

    def test_a_stage_the_carrier_cannot_provision_is_impassable(self):
        self.assertEqual(freight_cost.leg_money_per_tonne(1.0, CART, 1.0e6, restock_days=1.0e4), float("inf"))

    def test_grain_still_travels_only_a_few_hundred_km_by_land_when_the_carrier_restocks(self):
        grain_per_tonne = 0.3 * 1000.0
        rate = freight_cost.freight_money_per_tonne_km(
            CART, 0.3, 0.12, freight_cost.CarrierPrices(vehicle=200.0, animals=3000.0), 0.08,
            freight_cost.LAND_WORKING_DAYS_PER_YEAR, 1.0, 0.0)
        reach = grain_per_tonne / rate
        self.assertLess(reach, 400.0)
        self.assertLess(freight_cost.leg_money_per_tonne(rate, CART, 0.5 * reach,
                                                         restock_days=provisions.RESTOCK_INTERVAL_DAYS),
                        grain_per_tonne)
        self.assertGreater(freight_cost.leg_money_per_tonne(rate, CART, 2.0 * reach,
                                                            restock_days=provisions.RESTOCK_INTERVAL_DAYS),
                           grain_per_tonne)

    def test_a_hull_is_not_restocked_at_sea(self):
        economy = _Economy()
        fee = economy._freight_handling_costs()["sail"]
        legs = (foreign_routes.Leg("a", "b", "sail", 1000.0, 1000.0, 9.0),)
        priced = economy._with_carried_provisions(foreign_routes.Route(legs))
        share = provisions.delivered_share(economy._carrier_models()["sail"][0], 1000.0)
        self.assertAlmostEqual(priced.legs[0].cost_per_tonne, fee + (1000.0 - fee) / share, places=6)

    def test_a_land_leg_of_any_length_keeps_a_positive_share(self):
        legs = (foreign_routes.Leg("a", "b", "cart", 1.0e5, 1.0e5, 9.0),)
        priced = _Economy()._with_carried_provisions(foreign_routes.Route(legs))
        self.assertLess(priced.legs[0].cost_per_tonne, float("inf"))


class RouteChoiceTests(unittest.TestCase):
    """A route is chosen on rates that already carry the provisions."""

    def test_the_mode_with_the_lower_rate_per_km_loses_when_its_provisions_eat_the_lift(self):
        base = {"pack": 1.0, "cart": 1.2}

        def search(rates):
            return "pack" if rates["pack"] < rates["cart"] else "cart"

        def price(route):
            return {"pack": 1.0 / 0.5, "cart": 1.2 / 0.95}[route]

        def share_of(mode, route):
            return {"pack": 0.5, "cart": 0.95}[mode]
        self.assertEqual(search(base), "pack")
        self.assertEqual(foreign_route_choice.choose_route(search, price, base, share_of), "cart")

    def test_the_cheaper_priced_route_of_those_tried_is_kept(self):
        calls = []

        def search(rates):
            calls.append(dict(rates))
            return "far" if len(calls) == 1 else "near"
        prices = {"far": 5.0, "near": 9.0}
        chosen = foreign_route_choice.choose_route(
            search, prices.get, {"a": 1.0}, lambda mode, route: 0.5 if route is None else 0.25)
        self.assertEqual(len(calls), 2)
        self.assertEqual(chosen, "far")

    def test_no_route_is_none(self):
        self.assertIsNone(foreign_route_choice.choose_route(lambda rates: None, lambda route: 0.0, {"a": 1.0},
                                                            lambda mode, route: 1.0))

    def test_the_rates_searched_are_divided_by_the_share_delivered(self):
        seen = []

        def search(rates):
            seen.append(dict(rates))
            return "route"
        foreign_route_choice.choose_route(search, lambda route: 1.0, {"a": 2.0}, lambda mode, route: 0.5)
        self.assertAlmostEqual(seen[0]["a"], 4.0)

    def test_an_impassable_mode_is_not_searched_as_cheap(self):
        seen = []

        def search(rates):
            seen.append(dict(rates))
            return "route"
        foreign_route_choice.choose_route(search, lambda route: 1.0, {"a": 2.0}, lambda mode, route: 0.0)
        self.assertEqual(seen[0]["a"], float("inf"))


class MarkupTests(unittest.TestCase):

    def test_the_stated_monopoly_markup_is_gone(self):
        self.assertFalse(hasattr(merchant_terms, "MONOPOLY_MARKUP_SHARE"))

    def test_flexibility_is_read_back_from_a_constant_elasticity_response(self):
        flexibility = 0.6
        landed_share = 0.1
        factor = (1.0 + landed_share) ** -flexibility
        self.assertAlmostEqual(merchant_terms.price_flexibility(factor, landed_share), flexibility, places=9)

    def test_a_market_whose_price_does_not_move_has_no_flexibility(self):
        self.assertEqual(merchant_terms.price_flexibility(1.0, 0.1), 0.0)
        self.assertEqual(merchant_terms.price_flexibility(1.2, 0.1), 0.0)
        self.assertEqual(merchant_terms.price_flexibility(0.5, 0.0), 0.0)

    def test_a_lone_merchant_marks_up_more_where_the_price_falls_faster_with_the_cargo(self):
        shares = [merchant_terms.monopoly_markup_share(flexibility) for flexibility in (0.0, 0.2, 1.0, 10.0)]
        self.assertEqual(shares[0], 0.0)
        self.assertEqual(shares, sorted(shares))
        self.assertLess(shares[-1], 1.0)

    def test_the_lone_markup_is_the_linear_demand_optimum(self):
        # price = a - b q, cost c: the monopolist's markup over price is (a - c) / (a + c); the
        # competitive point's price flexibility is (a - c) / c.
        a, c = 10.0, 4.0
        self.assertAlmostEqual(merchant_terms.monopoly_markup_share((a - c) / c), (a - c) / (a + c))

    def test_competition_shrinks_the_markup_and_it_follows_the_response(self):
        flexibility = 0.8
        self.assertEqual(merchant_terms.competition_markup_share(1, flexibility),
                         merchant_terms.monopoly_markup_share(flexibility))
        self.assertGreater(merchant_terms.competition_markup_share(1, flexibility),
                           merchant_terms.competition_markup_share(5, flexibility))
        self.assertGreater(merchant_terms.competition_markup_share(3, 2.0),
                           merchant_terms.competition_markup_share(3, 0.2))

    def test_an_unknown_response_falls_back_to_the_markets_default_elasticity(self):
        from sim.world import market
        self.assertAlmostEqual(merchant_terms.price_flexibility_or_default(None),
                               1.0 / market.DEFAULT_DEMAND_PRICE_ELASTICITY)
        self.assertEqual(merchant_terms.price_flexibility_or_default(0.3), 0.3)


class HouseTests(unittest.TestCase):

    def test_the_agents_declared_per_carrier_are_gone(self):
        self.assertFalse(hasattr(merchant_terms, "AGENTS_PER_CARRIER"))

    def test_a_house_owns_as_many_carriers_as_its_capital_buys(self):
        small = merchant_house.carriers_per_house(100.0, 100.0)
        large = merchant_house.carriers_per_house(1000.0, 100.0)
        self.assertEqual(small, 1.0)
        self.assertEqual(large, 10.0)

    def test_a_house_owns_at_least_one_carrier_however_poor(self):
        self.assertEqual(merchant_house.carriers_per_house(1.0, 100.0), 1.0)
        self.assertEqual(merchant_house.carriers_per_house(0.0, 0.0), 1.0)

    def test_agents_are_a_factor_at_each_end_shared_by_the_houses_carriers(self):
        one = merchant_house.agents_per_carrier(1.0)
        ten = merchant_house.agents_per_carrier(10.0)
        self.assertGreater(one, 0.0)
        self.assertAlmostEqual(ten, one / 10.0)

    def test_houses_number_carriers_over_carriers_per_house(self):
        self.assertEqual(merchant_house.houses_on_route(40.0, 4.0, math.inf), 10.0)

    def test_the_labour_market_caps_the_houses_it_can_staff(self):
        staff = merchant_house.people_per_house()
        capped = merchant_house.houses_on_route(40.0, 4.0, 3.0 * staff)
        self.assertAlmostEqual(capped, 3.0)

    def test_a_route_of_no_legs_has_endless_houses(self):
        self.assertEqual(merchant_house.houses_on_route(math.inf, 1.0, 10.0), math.inf)

    def test_more_carriers_per_house_lowers_the_agent_cost_per_tonne(self):
        small = merchant_terms.agent_cost_per_tonne(0.01, 2000.0, 3.0, merchant_house.agents_per_carrier(1.0))
        large = merchant_terms.agent_cost_per_tonne(0.01, 2000.0, 3.0, merchant_house.agents_per_carrier(8.0))
        self.assertGreater(small, large)
        self.assertEqual(merchant_terms.agent_cost_per_tonne(None, 2000.0, 3.0, 2.0), 0.0)


class WaitTests(unittest.TestCase):

    def test_a_cargo_sells_slower_into_a_thinner_market_and_among_more_houses(self):
        base = merchant_terms.selling_years(100.0, 1000.0, 1.0)
        self.assertGreater(merchant_terms.selling_years(100.0, 500.0, 1.0), base)
        self.assertGreater(merchant_terms.selling_years(100.0, 1000.0, 4.0), base)
        self.assertEqual(merchant_terms.selling_years(100.0, math.inf, 4.0), 0.0)
        self.assertEqual(merchant_terms.selling_years(100.0, 0.0, 1.0), math.inf)

    def test_a_cargo_sells_over_half_the_time_the_market_takes_for_all_of_it(self):
        self.assertAlmostEqual(merchant_terms.selling_years(100.0, 1000.0, 1.0), 0.05)

    def test_a_shorter_sailing_season_lengthens_the_wait_for_it_to_open(self):
        waits = [merchant_terms.season_wait_years(share) for share in (1.0, 0.8, 0.5, 0.2)]
        self.assertEqual(waits[0], 0.0)
        self.assertEqual(waits, sorted(waits))
        self.assertAlmostEqual(merchant_terms.season_wait_years(0.5), 0.125)


class _Traders(foreign_traders.ForeignTradersMixin):
    """The cycle of a route as the engine reads it, with its fleet and its market given."""

    def __init__(self, carriers=10.0):
        self.carriers = carriers

    def _route_carriers(self, civilization_id, route):
        return self.carriers

    def _route_houses(self, civilization_id, route):
        return self.carriers

    def _route_cargo_tonnes(self, route):
        return 100.0


class CycleTests(unittest.TestCase):

    def test_a_route_with_sea_legs_waits_for_the_season_and_one_without_does_not(self):
        sea = foreign_routes.Route((foreign_routes.Leg("a", "b", "sail", 1000.0, 1.0, 10.0),))
        land = foreign_routes.Route((foreign_routes.Leg("a", "b", "cart", 1000.0, 1.0, 10.0),))
        traders = _Traders(1.0e9)
        self.assertGreater(traders._trader_cycle_years(sea), traders._trader_cycle_years(land))
        self.assertAlmostEqual(traders._trader_cycle_years(land), 10.0 / 365.0, places=6)

    def test_selling_into_a_thin_market_lengthens_the_cycle(self):
        land = foreign_routes.Route((foreign_routes.Leg("a", "b", "cart", 1000.0, 1.0, 10.0),))
        traders = _Traders(1.0e9)
        thick = traders._trader_cycle_years(land, destination_demand_tonnes=1.0e9)
        thin = traders._trader_cycle_years(land, destination_demand_tonnes=100.0)
        self.assertGreater(thin, thick)


class CapitalTests(unittest.TestCase):

    def test_merchants_hold_the_share_of_household_funds_their_incomes_make(self):
        funds = 1000.0
        own = merchant_house.class_own_capital(funds, merchants=10.0, merchant_wage=3.0,
                                               working_people=1000.0, labourer_wage=1.0)
        self.assertAlmostEqual(own, funds * 10.0 * 3.0 / 1000.0)

    def test_no_merchants_hold_nothing_and_no_one_to_compare_with_holds_nothing(self):
        self.assertEqual(merchant_house.class_own_capital(1000.0, 0.0, 3.0, 1000.0, 1.0), 0.0)
        self.assertEqual(merchant_house.class_own_capital(1000.0, 10.0, 3.0, 0.0, 1.0), 0.0)

    def test_the_class_cannot_hold_more_than_the_funds(self):
        self.assertEqual(merchant_house.class_own_capital(100.0, 1.0e6, 3.0, 1000.0, 1.0), 100.0)

    def test_what_merchants_use_beyond_their_own_is_borrowed(self):
        self.assertEqual(merchant_house.borrowing(250.0, 100.0), 150.0)
        self.assertEqual(merchant_house.borrowing(50.0, 100.0), 0.0)


def conditions(demand=1000.0, capacity=500.0):
    return market.MarketConditions(
        household_demand_at_anchor_tonnes=demand, committed_demand_tonnes=0.0,
        society_capacity_tonnes=capacity, actor_supply_tonnes=0.0, founder_sales_tonnes=0.0, stock_tonnes=0.0)


if __name__ == "__main__":
    unittest.main()
