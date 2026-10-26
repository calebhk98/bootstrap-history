"""Where pathogens come from: the outside sources the civilisation names, the routes that reach them and the draw of
who arrives."""
from sim.geography.api import reach, usable_modes

from . import nation, nation_tuning as tuning, metapopulation as spread
from .technology_effects import technology_scales


class Contact:

    def contact_sources(self):
        """The outside sources the civilisation says the pathogens come from (see `nation.contact_sources`)."""
        return nation.contact_sources(self.needs.civilisation().get("disease_exposure"))

    def seed_text(self):
        return "disease:%s:%d" % (self.needs.civilisation().get("id"), self.needs.weather_seed(0, "disease"))

    def endemic_pathogens(self):
        """The pathogens the civilisation's people already carry at the start (initial conditions)."""
        return tuple(sorted((self.needs.civilisation().get("disease_exposure") or {}).get("endemic", ())))

    def entry(self, source):
        """{held tile: fewest days} from the nearest of the source's tiles, over the modes the nation's
        technologies open plus those the outsiders bring; empty when no route joins them. Kept until the tiles
        held or the modes change."""
        held = tuple(self.held_tiles())
        world_map = self.needs.legacy_world_map()
        modes = tuple(sorted(set(usable_modes([self.needs.held_techniques(True)], world_map)) | set(source["carrier_modes"])))
        cache = self._entry_cache
        key = (held, modes, source["tiles"])
        if key not in cache:
            if len(cache) > 32:
                cache.clear()
            days = reach(source["tiles"], modes, 1.0e9, world_map=world_map) if held and source["tiles"] else {}
            cache[key] = {tile: days[tile] for tile in held if tile in days}
        return cache[key]

    def travel_days(self, source):
        reached = self.entry(source)
        return min(reached.values()) if reached else None

    def contact_weight(self, source):
        """The share of the source's contact the routes let through; one for a source that names no tiles."""
        return nation.contact_weight(self.travel_days(source)) if source["tiles"] else 1.0

    def entry_tiles(self, arrivals, year, people_by_tile, contacts):
        """{arriving pathogen: [tiles it enters at]}: of the open sources, the one with the most contact; the
        populated held tile its routes reach first in each group of tiles the traffic joins, so long as the group
        is within one travel-decay distance of the soonest reached (a source naming no tiles enters at the most
        populous tile)."""
        populated = {tile for tile, bands in people_by_tile.items() if sum(bands.values()) > 0.0}
        busiest = max(sorted(people_by_tile), key=lambda tile: sum(people_by_tile[tile].values()), default=None)
        groups = [[tile for tile in group if tile in populated] for group in spread.components(contacts, set(people_by_tile))]
        entered = {}
        for pathogen_id in arrivals:
            best = None
            for source in self.contact_sources():
                if pathogen_id not in source["pathogens"] or (
                        source["first_year"] is not None and not source["first_year"] <= year <= source["last_year"]):
                    continue
                weight = self.contact_weight(source)
                days = {tile: days for tile, days in self.entry(source).items() if tile in populated}
                tiles = spread.entry_tiles(days, groups, tuning.DISEASE_TRAVEL_DECAY_DAYS) if source["tiles"] else [busiest]
                if weight > 0.0 and tiles and (best is None or weight > best[0]):
                    best = (weight, tiles)
            entered[pathogen_id] = best[1] if best else [busiest]
        return entered

    def introductions(self, records, year):
        """Pathogens that arrive this year: reachable from an open source, absent from the nation, and drawn."""
        chances = nation.arrival_chances(self.contact_sources(), year, self.contact_weight)
        return [pathogen_id for pathogen_id in nation.introductions({}, chances, year, self.seed_text())
                if not spread.is_circulating(records, pathogen_id)]

    def technology_scales(self, pathogen_ids):
        """({pathogen id: multiplier on case fatality}, {pathogen id: multiplier on transmission}) from the
        `disease_effects` of the technologies the nation has taken up (the share of the country that holds
        a node scales how much of its relief applies)."""
        return technology_scales(
            pathogen_ids, [(spec, self.needs.civ_diffusion[node_id]) for node_id, spec in self.needs.effect_terms("disease_effects")])
