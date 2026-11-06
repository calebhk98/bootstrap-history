"""Each seat's running concerns sell in the agent economy's market. Part of the port (it imports `sim.economy.api`).

A seat's output is handed over from the engine through the legacy edge (the engine's purse is not yet an account in the book:
Complaint 382) and offered at what the concern costs to make it at the economy's own prices and wages; what it fetched goes
to the seat's ledger after the clearing (port_seats.py). What a seat offered and what its inputs cost live from `orders` to
`settle` within one year's run and are passed between them, not kept."""
import math
from typing import Optional

from sim.economy import api as economy_api
from sim.economy.api import (EDGE_LEGACY, AgentOrders, GoodsMove, Offer, Producer, expected_output_prices,
                             live_input_prices, live_wages, variable_cost_per_run)
from sim.prices.api import prices as price_solver, rules as price_rules

from . import port_seats


class SeatConcerns:

    def __init__(self, world, agent):
        self._world = world
        self._agent = agent

    def orders(self):
        """(the orders of every seat's running concerns' output for the year, one agent per seat named by its seat id;
        {seat: (tile, {material: quantity offered})}; {seat: what its concerns' inputs cost})."""
        world = self._world
        orders, offered, inputs = {}, {}, {}
        for seat_id in world.state.seats_playing():
            with world.scenario.act_as(seat_id):
                orders.update(self._acting_orders(seat_id, offered, inputs))
        return orders, offered, inputs

    def _acting_orders(self, seat_id, offered_by_seat, inputs):
        """The acting seat's running concerns' output for the year, offered at what the concern costs to make it."""
        world, agent = self._world, self._agent
        economy = agent.economy()
        area_map = economy.area_map
        tile = agent.tile_in_economy(world.labour.base_tile())
        view = economy.view()
        moves, offers = [], []
        offered = offered_by_seat.setdefault(seat_id, (tile, {}))[1]
        for node_id in sorted(world.production.operating()):
            quantities = world.production.concern_book_offer(node_id)
            if not quantities:
                continue
            inputs[seat_id] = inputs.get(seat_id, 0.0) + world.production.concern_book_inputs_cost(node_id)
            for material, quantity in sorted(quantities.items()):
                offered[material] = offered.get(material, 0.0) + quantity
                moves.append(GoodsMove(EDGE_LEGACY, seat_id, material, tile, quantity, "concern output"))
                cost = self.reservation(node_id, material, tile, view, seat_id)
                offers.append(Offer(seat_id, material, area_map.area_of(material, tile), tile, quantity,
                                    0.0 if cost is None else cost))     # no cost known: no floor
        economy_api.move_goods(economy, moves)
        return {seat_id: AgentOrders(offers=tuple(offers))} if offers else {}

    def reservation(self, node_id, material, tile, view, agent_id) -> Optional[float]:
        """The least the seller takes for a unit of a concern's output: the unit's share, by value, of
        the variable cost of the cheapest technique the concern holds that the economy knows, at the
        economy's live prices and wages. None with no such technique: no cost is known."""
        recipes = economy_api.recipes_of(self._agent.economy())
        keys = price_rules.entry_keys_held_for(node_id, price_solver.default_production_entries(), self._world.production.techniques_spread())
        best = None
        for key in sorted(keys):
            recipe = recipes.get(key)
            if recipe is None or material not in recipe.outputs:
                continue
            probe = Producer(agent_id, agent_id, key, tile, 1.0)
            prices = expected_output_prices(probe, recipe, view) or {}
            if any(prices.get(good) is None for good in recipe.outputs):
                continue    # the cost cannot be shared by value among outputs when one has no price
            revenue = sum(recipe.outputs[good] * prices[good] for good in recipe.outputs)
            cost = variable_cost_per_run(recipe, live_input_prices(probe, recipe, view),
                                         live_wages(probe, recipe, view))
            if revenue > 0.0 and math.isfinite(cost) and prices.get(material):
                per_unit = cost * prices[material] / revenue
                best = per_unit if best is None else min(best, per_unit)
        return best

    def settle(self, offered, inputs):
        """What each seat's goods fetched goes to its ledger, less what its concerns' inputs cost; what did not sell goes
        back to the engine (port_seats.settle_seats)."""
        stored = self._agent.stored
        sold = port_seats.settle_seats(self._world, self._agent.economy(), offered, inputs, EDGE_LEGACY)
        stored["seat_sales"] = {**stored.get("seat_sales", {}), **sold}

    def sale_outlook(self, seat_id, material, quantity):
        """What the seat may count as sold of `quantity` units of a material it makes: its last clearing's share and
        price, else what the market's buyers took last year (concern_sales.outlook); None when the economy is not open."""
        if not self._agent.opened():
            return None
        return port_seats.outlook(self._agent.economy(), self._agent.stored.get("seat_sales", {}), seat_id, material, quantity)

    def seat_tiles(self):
        """The tiles the playing seats buy and sell on, whose markets' books the economy keeps."""
        world = self._world
        tiles = set()
        for seat_id in world.state.seats_playing():
            with world.scenario.act_as(seat_id):
                tiles.add(self._agent.tile_in_economy(world.labour.base_tile()))
        return tiles
