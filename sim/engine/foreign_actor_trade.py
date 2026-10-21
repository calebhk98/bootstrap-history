"""Trade that actors (the traders) carry between this society and a partner, as the partner's market sees it.

A cargo sold to a partner is extra supply in that partner's book, and a cargo bought there is extra
demand, so the gap the traders serve narrows over the years. Actors tally the year's cargo here
(`note_actor_trade`); the partner's books close on it at the year's end (`close_partner_books`). A good
the actors carry in a direction this year is theirs: the engine's aggregate foreign flow and the agent
economy's stand-in external orders leave that direction alone (`actors_carry`).
"""
from sim.world import market

from .material_units import tonnes_per_unit

LANDED = "landed_tonnes"   # carried into the home market
TAKEN = "taken_tonnes"     # carried out of the home market
SOLD = "sold_tonnes"       # carried to the partner
BOUGHT = "bought_tonnes"   # carried from the partner
LANDED_COST = "landed_cost_money"   # what the tonnes carried to the partner cost the carriers there: purchase, carriage, dues, margin


class ForeignActorTradeMixin:

    def note_actor_trade(self, partner, material, tonnes, to_partner, landed_cost=0.0):
        """Tally a cargo of `material` an actor carried to (or from) a partner this year; `landed_cost` is what
        a cargo to the partner cost its carrier to land (home money)."""
        by_material = self.state.economy.foreign_actor_trade.setdefault(partner, {})
        flow = by_material.setdefault(material, {SOLD: 0.0, BOUGHT: 0.0})
        flow[SOLD if to_partner else BOUGHT] += tonnes
        if to_partner:
            before = flow[SOLD] - tonnes
            if tonnes < 0.0 and before > 0.0 and not landed_cost:
                landed_cost = flow.get(LANDED_COST, 0.0) * tonnes / before   # a part of the cargo is taken back: its cost with it
            flow[LANDED_COST] = max(0.0, flow.get(LANDED_COST, 0.0) + landed_cost)

    def landed_cost(self, paid, carriage):
        """What a cargo costs its carrier on landing: the purchase, a year's return on it (the carrier's margin)
        and the carriage with its dues."""
        return paid * (1.0 + self.market_rate()) + carriage

    def note_actor_home_trade(self, material, tonnes, landing):
        """Tally a cargo of `material` that actors landed in the home market (or took out of it) this year, so the
        price a further cargo would meet at home is quoted on top of it (`actor_home_trade`)."""
        flow = self.state.economy.home_actor_trade.setdefault(material, {LANDED: 0.0, TAKEN: 0.0})
        flow[LANDED if landing else TAKEN] += tonnes

    def actor_home_trade(self, material):
        """(tonnes landed in the home market, tonnes taken out of it) by actors so far this year."""
        flow = self.state.economy.home_actor_trade.get(material, {})
        return flow.get(LANDED, 0.0), flow.get(TAKEN, 0.0)

    def actors_carry(self, material, to_partner, partner=None):
        """Whether actors have carried the material this year toward (or from) a partner, any partner by default."""
        key = SOLD if to_partner else BOUGHT
        tally = self.state.economy.foreign_actor_trade
        return any(flows.get(material, {}).get(key, 0.0) > 0.0
                   for named, flows in tally.items() if partner is None or named == partner)


    def partner_price_per_unit(self, partner, material):
        """A partner's price of a material in home money: its solved cost, at its coin's price level and
        the price its own market has reached; None when the partner prices nothing of it."""
        price = self._foreign_economy_facts(partner)["prices_in_home_money"].get(material)
        if not price:
            return None
        entry = self.state.economy.foreign_market_book.get(partner, {}).get(self._material_tag(material)[0])
        ratio = entry["price_ratio"] if entry else 1.0
        return price * self.partner_price_level(partner) * ratio

    def _import_offers(self, partner, cargo_by_material):
        """The cargo landed at a partner as offers at its landed cost, a ratio to the partner's long-run cost of
        the material; cargo with no landed cost noted is a price taker (returned as plain tonnes)."""
        facts = self._foreign_economy_facts(partner)
        offers, price_taking = {}, {}
        for material, flow in cargo_by_material.items():
            commodity = self._material_tag(material)[0]
            tonnes_each = tonnes_per_unit(material)
            base = facts["prices_in_home_money"].get(material)
            base = base / tonnes_each if base and tonnes_each else None   # per tonne, as the cargo is costed
            tonnes = flow[SOLD]
            if base and tonnes > 0.0 and flow.get(LANDED_COST, 0.0) > 0.0:
                ratio = flow[LANDED_COST] / tonnes / (base * self.partner_price_level(partner))
                offers.setdefault(commodity, []).append(market.Offer(tonnes, ratio))
            else:
                price_taking[commodity] = price_taking.get(commodity, 0.0) + tonnes
        return offers, price_taking

    def _partner_outcome(self, entry, commodity, sold, bought, imports=()):
        """The partner's market for a commodity cleared on `sold` tonnes landed there at no ask, `imports` landed
        at their landed cost, and `bought` taken from it."""
        record = self._commodity_ledger().commodities.get(commodity) or {}
        return market.clear_market(market.MarketConditions(
            household_demand_at_anchor_tonnes=entry["reference_tonnes"], committed_demand_tonnes=0.0,
            society_capacity_tonnes=entry["capacity_tonnes"], actor_supply_tonnes=sold,
            founder_sales_tonnes=0.0, stock_tonnes=entry["stock_tonnes"], actor_demand_tonnes=bought, imports=tuple(imports),
            floor_ratio=self._floor_ratio(commodity),
            ceiling_ratio=float(record.get("price_ceiling_factor", market.DEFAULT_CEILING_RATIO))))

    def partner_price_response(self, partner, material, tonnes, landing):
        """Factor on a partner's price of a material once `tonnes` more are landed there (`landing`) or taken
        from it, on top of the year's cargo so far; one where the partner has no book for it."""
        commodity = self._material_tag(material)[0]
        entry = self._foreign_entry(partner, commodity, self._foreign_economy_facts(partner))
        if entry is None or not entry["price_ratio"] > 0.0:
            return 1.0
        flow = self.state.economy.foreign_actor_trade.get(partner, {}).get(material, {SOLD: 0.0, BOUGHT: 0.0})
        sold, bought = flow[SOLD] + (tonnes if landing else 0.0), flow[BOUGHT] + (0.0 if landing else tonnes)
        return self._partner_outcome(entry, commodity, sold, bought).price_ratio / entry["price_ratio"]

    def close_partner_books(self):
        """Clear each commodity in each partner's book on the year's actor cargo (none for most), so the
        partner's capacity follows its price and the price follows the cargo; then clear the tally."""
        tally = self.state.economy.foreign_actor_trade
        book = self.state.economy.foreign_market_book
        self.state.economy.home_actor_trade.clear()
        for partner in sorted(set(tally) | set(book)):
            facts = self._foreign_economy_facts(partner)
            cargo = {}
            imports, price_taking = self._import_offers(partner, tally.get(partner, {}))
            for material, flow in tally.get(partner, {}).items():
                sold_bought = cargo.setdefault(self._material_tag(material)[0], [0.0, 0.0])
                sold_bought[0] += flow[SOLD]
                sold_bought[1] += flow[BOUGHT]
            for commodity in sorted(set(book.get(partner, {})) | set(cargo)):
                entry = self._foreign_entry(partner, commodity, facts)
                if entry is None:
                    continue
                sold, bought = cargo.get(commodity, (0.0, 0.0))
                outcome = self._partner_outcome(entry, commodity, price_taking.get(commodity, 0.0), bought,
                                                imports.get(commodity, ()))
                entry["capacity_tonnes"] = market.adjusted_capacity(entry["capacity_tonnes"], outcome.price_ratio)
                entry["stock_tonnes"] = market.stock_after_year(outcome)
                entry["price_ratio"] = outcome.price_ratio
                entry["trade_tonnes"] = sold - bought
        tally.clear()
