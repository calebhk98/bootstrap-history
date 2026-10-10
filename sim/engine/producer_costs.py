"""What a producer's goods cost it to make: the reservation price it takes to the market.

Each producer (a firm's or the founder's concern, the incumbents) makes a good by the production entry it
runs. Its cost is that entry's unit cost at the prices of its inputs (entry_cost.py), over the incumbents'
cost of the same good, so the market (sim/world/market.py) receives only a ratio. A producer that holds
several entries for a good runs the cheapest. A producer whose plant is built (every concern that
exists) offers at its running cost, the entry's cost without the plant's repayment; the full cost, with
the repayment, stays the incumbents' reference and what a decision to build is judged against.

TEMPORARY HEURISTIC (CLAUDE.md 4.4): the entries a concern holds are its node's own and those of any node
some producer runs that make the same products (concern_volume.py); a producer-by-producer technique set
would replace it. Inputs are priced at the incumbents' cost, not at what each buyer was charged.
"""
from typing import Any, Dict, FrozenSet, List

from sim.world.producer_market import Offer

from . import entry_cost
from . import prices as price_solver
from .material_units import tonnes_per_unit


# (production table, {gate node: keys of the entries it gates}, {outputs: keys of entries making them}); the
# table is kept so a hit is confirmed with `is`
_INDEX: List[Any] = [None, None, None]


def _indexes(production):
    if _INDEX[0] is not production:
        by_gate: Dict[str, List[str]] = {}
        by_outputs: Dict[FrozenSet[str], List[str]] = {}
        for key in sorted(production):
            entry = production[key]
            if entry.get("requires_node"):
                by_gate.setdefault(entry["requires_node"], []).append(key)
            if entry.get("outputs"):
                by_outputs.setdefault(frozenset(entry["outputs"]), []).append(key)
        _INDEX[:] = [production, by_gate, by_outputs]
    return _INDEX[1], _INDEX[2]


def entry_keys_held_for(node_id, production, held):
    """Keys of the node's own entries and of every entry a held node gates that makes one of its lines."""
    by_gate, by_outputs = _indexes(production)
    own = by_gate.get(node_id, [])
    keys = list(own)
    for line in sorted({frozenset(production[key]["outputs"]) for key in own if production[key].get("outputs")},
                       key=sorted):
        for key in by_outputs.get(line, []):
            if production[key].get("requires_node") in held and key not in own:
                keys.append(key)
    return keys


class ProducerCostsMixin:

    def _opening_wage_document(self):
        """The wage document the price tables are in (the opening's ratios)."""
        from .data import schedule_of_civilisation
        return schedule_of_civilisation(self.civ).document()

    def _reference_entry(self, material):
        """The entry the incumbents make `material` by (the solver's cheapest in their techniques); for a
        good they do not make, the cheapest in the techniques now run."""
        document = self._opening_wage_document()
        for held in (frozenset(self.state.projects.granted), self.techniques_in_use()):
            chosen = price_solver.solved_prices(held, document, civilization=self.civ).chosen_recipe_by_material
            if material in chosen:
                return chosen[material]
        return None

    def _cost_book(self):
        """What entries are costed against: the incumbents' prices, remembered while that table stands."""
        hours = self._price_tables()[0]
        cache = getattr(self, "_cost_book_cache", None)
        if cache is None or cache[0] is not hours:
            cache = self._cost_book_cache = (hours, entry_cost.CostBook(
                hours, self._opening_wage_document(), self.civ, self.techniques_in_use()), {})
        return cache

    def entry_cost_ratio(self, entry_key, material, running=False):
        """A unit of `material` made by this entry over the same made by the incumbents' entry, both at the
        prices the incumbents face; one where either cannot be costed. `running` leaves the entry's plant
        repayment out (a producer whose plant is built), the incumbents' cost staying the full one."""
        _hours, book, ratios = self._cost_book()
        key = (entry_key, material, running)
        if key not in ratios:
            reference_key = self._reference_entry(material)
            own = (book.running_unit_cost_hours if running else book.unit_cost_hours)(entry_key, material)
            reference = book.unit_cost_hours(reference_key, material) if reference_key else None
            ratios[key] = own / reference if own is not None and reference else 1.0
        return ratios[key]

    def commodity_floor_ratio(self, commodity):
        """The share of the incumbents' cost that is running cost, for the entries they make the commodity's
        materials by: the lowest price their built plant still sells at. None where no entry can be split."""
        _hours, book, ratios = self._cost_book()
        key = ("floor", commodity)
        if key not in ratios:
            shares = []
            for material in self.materials_of_commodity(commodity):
                reference_key = self._reference_entry(material)
                share = book.running_share(reference_key, material) if reference_key else None
                if share is not None:
                    shares.append(share)
            ratios[key] = sum(shares) / len(shares) if shares else None
        return ratios[key]

    def materials_of_commodity(self, commodity):
        """The material keys that trade as one commodity, sorted."""
        return sorted(material for material, group in self._material_commodity_map().items()
                      if group == commodity)

    def concern_cost_ratio(self, node_id, material):
        """The running cost ratio of the cheapest entry a concern on this node holds that makes `material`:
        a concern that exists has sunk its plant, so it offers at what running it costs."""
        production = price_solver.default_production_entries()
        held = self.techniques_in_use()
        ratios = [self.entry_cost_ratio(key, material, running=True)
                  for key in entry_keys_held_for(node_id, production, held)
                  if material in (production[key].get("outputs") or {})]
        return min(ratios) if ratios else 1.0


    def founder_concern_offers(self, commodity):
        """What the founder's own running concerns put on the market in `commodity`, each at its cost;
        remembered while what is built and run is unchanged, per year (the ramp-up moves with it)."""
        return self._done_memo("founder_offers", (commodity, self.state.scenario.year),
                               lambda: self._founder_concern_offers(commodity))

    def _founder_concern_offers(self, commodity):
        projects = self.state.projects
        offers = []
        for node_id in sorted(projects.operating):
            if node_id in projects.granted or not self.is_venture(node_id):
                continue
            baskets = self.concern_baskets_now(node_id)
            if baskets is None:
                continue
            ramp = self.venture_ramp(node_id)
            for material, units in sorted(baskets.outputs.items()):
                if units > 0.0 and self._material_tag(material)[0] == commodity:
                    offers.append(Offer(units * tonnes_per_unit(material) * ramp,
                                        self.concern_cost_ratio(node_id, material)))
        return tuple(offers)
