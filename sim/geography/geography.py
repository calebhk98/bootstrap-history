"""Where things are, and what that costs to reach: one simulation's geography (`sim.geography`).

It reads the civilisation, its population scale, the technologies it holds and the ways it has built
through the world it is given (an engine-side adapter, sim/engine/geography_port.py). A region's reach is
the fewest days of travel from the tiles the civilisation holds (`reach_bands.py`); mineral access and
located-material costs follow from it.
"""

import json
from typing import Any, Dict, NotRequired, Tuple, TypedDict

from sim.geography import located_places, mineral_shares, queries, reach_bands, routes_modes, tile_holdings
from sim.geography.queries import deposit_records
from sim.geography.distance import haversine_km
from sim.geography.parameters import parameter as parameter_value


JSONDict = Dict[str, Any]


class RegionRecord(TypedDict):
    """One entry of the geography data's `regions` block: a label over tiles. Land figures and the
    anchor point are not stored: they are derived from the region's tiles (sim/world/land.py,
    sim/geography/regions.py). `note` is the only key absent on some regions."""
    name: str
    note: NotRequired[str]


class Geography:
    """The geography of one simulation, opened once from the geography file."""

    geo: JSONDict
    _regions: Dict[str, RegionRecord]
    _mat_unlock: Dict[str, str]
    _shares_by_tile: Dict[str, Dict[str, float]]
    _material_tiles: Dict[str, Tuple[str, ...]]
    _table: Dict[str, Any]

    def __init__(self, world: Any) -> None:
        self._world = world
        self._table = {"key": None}

    def _inputs_key(self) -> Tuple[Any, ...]:
        """What the reach table depends on: the tiles held, the technologies held and the ways built."""
        civ = self._world.civ
        return (tuple(civ.get("home_regions") or ()), tuple(civ.get("home_tiles") or ()),
                frozenset(self._world.held_nodes), json.dumps(self._world.improvements, sort_keys=True))

    def _reach_table(self) -> Dict[str, Any]:
        """{levels: {region: reach level}, tile_levels: {tile: reach level}, scale: {mineral: scale}},
        rebuilt when its inputs change."""
        key = self._inputs_key()
        if self._table["key"] != key:
            world_map = self._world.world_map
            held = tile_holdings.tiles_held(self._world.civ, world_map)
            levels = reach_bands.region_levels(world_map, held, self._world.held_nodes, self._world.improvements)
            tile_levels = reach_bands.tile_levels(world_map, held, self._world.held_nodes, self._world.improvements)
            self._table = {"key": key, "levels": levels, "tile_levels": tile_levels, "reference": {}, "scale": {}}
            self._table["scale"] = {material: self._compute_mineral_scale(material)
                                    for material in sorted(self._shares_by_tile)}
        return self._table

    def tile_reach(self, tile_id: str) -> int:
        """How hard `tile_id` is to reach, FOR THIS CIVILIZATION, on the same levels as `region_reach`:
        0 for a tile held, the farthest level for a tile no route joins."""
        return self._reach_table()["tile_levels"].get(tile_id, reach_bands.farthest_level(self._world.world_map))

    def region_reach(self, region_id: str) -> int:
        """How hard `region_id` is to reach, FOR THIS CIVILIZATION, 0 to the map's farthest level.

        0 is a region the civilisation holds a tile of. Otherwise it is the fewest days of travel from
        a held tile over the modes its technologies open and the ways it has built, banded by
        `reach_bands`; a region no route joins is the farthest level.
        """
        farthest = reach_bands.farthest_level(self._world.world_map)
        if region_id not in self._regions:
            return farthest
        return self._reach_table()["levels"].get(region_id, farthest)

    def route_km_to(self, tile_ids: Any) -> Any:
        """Kilometres of the cheapest haul from the tiles held to the nearest of these tiles (0.0 when one
        is held), over the modes held and the ways built; the great-circle distance between the nearest
        pair of tiles when no mode joins them, None when there is no tile."""
        targets = tuple(sorted(set(tile_ids)))
        kept = self._reach_table().setdefault("route_km", {})
        if targets not in kept:
            kept[targets] = self._route_km(targets)
        return kept[targets]

    def _route_km(self, targets: Tuple[str, ...]) -> Any:
        world_map = self._world.world_map
        held = tile_holdings.tiles_held(self._world.civ, world_map)
        if not targets or not held:
            return None
        if set(targets) & set(held):
            return 0.0
        nodes = frozenset(self._world.held_nodes)
        found = queries.route(held, targets, routes_modes.usable_modes(world_map, [nodes]),
                              self._world.improvements, held_nodes=nodes, world_map=world_map)
        if found is not None:
            return found["km"]
        return min(haversine_km(*tile_holdings.tile_centre(a, world_map), *tile_holdings.tile_centre(b, world_map))
                   for a in held for b in targets)

    def _reference_levels(self, civilisation_id: str) -> Dict[str, int]:
        """Tile levels of the civilisation the located-material costs were authored for, at its start."""
        reference = self._reach_table()["reference"]
        if civilisation_id not in reference:
            record = self._world.civilisation(civilisation_id)
            world_map = self._world.world_map
            reference[civilisation_id] = (
                reach_bands.tile_levels(world_map, tile_holdings.tiles_held(record, world_map),
                                        record.get("starting_techs") or ()) if record else {})
        return reference[civilisation_id]

    # How much of a region's output reaches your market by ordinary trade
    # when you do NOT hold the region yourself, fading with reach rather
    # than cutting off: nothing in this model is a wall, only a price.
    TRADE_ACCESS_BY_REACH = {0: 1.0, 1: 0.5, 2: 0.3, 3: 0.15, 4: 0.08, 5: 0.04, 6: 0.02}

    def material_reach(self, material_key: str) -> Tuple[int, float]:
        """Reach and cost multiplier for `material_key`, FOR THIS CIVILIZATION.

        Looks the material up in the geography data's located_materials, picks
        whichever of its places (each a tile) is EASIEST for this civ to reach (a
        rational buyer sources from the nearest one), and turns that tile's reach
        into a cost multiplier.

        The published cost_multiplier was authored for one civilisation (the map parameter
        `located_material_reference_civilisation`). At civ_reach 0 (you hold the place) the
        multiplier is 1; at the reach the reference civilisation has at its start it reproduces
        the published number; nearer it comes out cheaper, farther dearer. Power, not a straight
        line, so it is smooth at both ends and never goes negative or hits zero.
        """
        materials = self.geo.get("located_materials") or {}
        material_entry = materials.get(material_key)
        if not material_entry:
            return 0, 1.0
        base_mult = float(material_entry.get("cost_multiplier", 1.0))
        best = None
        for tile_id in self._material_tiles.get(material_key, ()):
            civ_r = self.tile_reach(tile_id)
            if best is None or civ_r < best[0]:
                reference = self._reference_levels(parameter_value(
                    self._world.world_map, "located_material_reference_civilisation"))
                best = (civ_r, max(1, reference.get(tile_id, civ_r)))
        if best is None:
            return 0, base_mult
        civ_r, reference_level = best
        if civ_r <= 0:
            return 0, 1.0      # it is, in effect, home ground for this civilization
        raw = base_mult ** (civ_r / reference_level)
        # Cap it. The exponent could reach x235 for gutta percha and x468 for
        # rubber, and a several-hundred-fold cost is not an expense, it is the
        # abolished "unobtainable" category wearing a price tag. The ceiling is
        # argued from the Roman evidence rather than chosen for feel: pepper
        # carried roughly a tenfold to twentyfold markup and silk about a
        # hundredfold, both RETAIL across a chain of middlemen. This node buys
        # your OWN supply, which should cost less per unit than retail, not
        # more. 60 is therefore generous rather than punitive, which is the
        # right way to be wrong here.
        # Compress rather than clamp: a hard ceiling would flatten the very
        # distinction this function exists to draw. If Rome's 235 and Han
        # China's 60 both hit a cap of 60, they come out identical, and the
        # geography fix stops doing anything. Raising to a fractional power
        # keeps the ORDERING intact while pulling the magnitudes back to
        # something defensible, and the ceiling stays only as a backstop.
        return civ_r, min(raw ** 0.6, 45.0)

    def material_cost_factor(self, node_id: str) -> float:
        """Cost multiplier a located-material tech node picks up from
        geography, for the civilization in play.

        Only applies to nodes the geography data actually names (via
        located_materials.*.unlocks, e.g. mat_gutta_percha, mat_natural_rubber):
        everything else returns 1.0 and is untouched. the geography data's
        cost_multiplier field has to be read here, or gutta percha costs
        exactly the same (nothing extra) whether you are playing Rome or
        Han China, and the entire India-and-east trade advantage a
        China-based civilization actually has is invisible to the model.
        """
        material_key = self._mat_unlock.get(node_id)
        if not material_key:
            return 1.0
        _, mult = self.material_reach(material_key)
        return mult

    def _compute_mineral_scale(self, material: str) -> float:
        """Fraction of a mined mineral's reference output this civilization
        can draw on: geology and reach, not population.

        Scaling this by self._world.pop_scale - "how much coal can you buy" tied
        to HOW MANY PEOPLE YOU HAVE - would be backwards twice over: Norse
        Scandinavia would get 2.3% of Rome's coal because it has 2.3% of
        the people, while England in 1300, precisely where the coal
        actually is, would get only 7%. A coalfield does not care how many
        people live near it.

        Each named deposit carries a share of a material's total output
        (sim/geography/mineral_shares.py), normalised so ROME'S OWN deposits sum
        to about 1.0 -- which is what reproduces resources.json's Roman
        totals for a Rome-based civ. For any other civilization: deposits on
        tiles it actually HOLDS (reach 0) count in full, and every other
        deposit contributes a SHRINKING but never-zero share as its tile
        fades with reach (TRADE_ACCESS_BY_REACH), because a civilization
        with no local ore can still buy imported metal, just less of it.
        Floored well above zero so this is a price, never a wall.
        """
        total = 0.0
        for tile_id, share in self._shares_by_tile.get(material, {}).items():
            total += share * self.TRADE_ACCESS_BY_REACH.get(self.tile_reach(tile_id), 0.02)
        return max(0.05, total)

    def tracked_materials(self) -> Tuple[str, ...]:
        """The materials whose output the deposits share out over tiles."""
        return tuple(sorted(self._shares_by_tile))

    def held_share(self, tile_ids: Any, material: str) -> float:
        """Share of `material`'s output from the deposits on these tiles (zero for an untracked material)."""
        held = set(tile_ids)
        return sum(share for tile_id, share in self._shares_by_tile.get(material, {}).items() if tile_id in held)

    def source_tiles(self, material: str) -> Tuple[str, ...]:
        """The tiles whose deposits produce `material` (empty for a material no deposit shares out)."""
        return tuple(sorted(self._shares_by_tile.get(material, {})))

    def mineral_scale(self, material: str) -> float:
        """Fraction of a mineral's reference output this civilisation can draw on, kept until the tiles
        held, the technologies held or the ways built change."""
        return self._reach_table()["scale"].get(material, self._world.pop_scale)

    def open(self, geo: JSONDict) -> None:
        """The region labels and located materials; reach and mineral access are worked out from the tiles
        held when first asked, and again whenever what they depend on changes."""
        self.geo = geo
        from sim.geography import regions as region_tables  # here: regions -> sim.world -> this package's api
        self._regions = region_tables.region_records(self.geo)
        rows = deposit_records(world_map=self._world.world_map)
        self._shares_by_tile = mineral_shares.deposit_shares_by_tile(self.geo, rows)
        self._material_tiles = {}
        self._table = {"key": None}
        # node id -> located_materials key, so a location-gated tech node finds its geography entry
        # without the tech tree knowing anything about geography.
        self._mat_unlock = {}
        for material_key, material_data in (self.geo.get("located_materials") or {}).items():
            if material_key.startswith("_"):
                continue
            self._material_tiles[material_key] = located_places.tiles(material_data, self.geo, rows)
            for nid in (material_data.get("unlocks") or []):
                self._mat_unlock[nid] = material_key

    @property
    def data(self) -> JSONDict:
        """The raw geography file's contents."""
        return self.geo

    @property
    def regions(self) -> Dict[str, RegionRecord]:
        """Every region's record, by region id."""
        return self._regions
