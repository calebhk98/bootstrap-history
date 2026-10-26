"""One-line forwarders from the old `Sim` names of land to the land module, for callers not yet in a module.

The screens, the economy's setup and the engine's mixins still say `sim.world_map`, `sim.geography`, `sim.tile_owner_map()` or
`sim.found_colony(tile)`; each line goes when its last caller reads the view (`sim.view(name)`) or sends the command itself."""
from sim.land.api import FoundColony
from sim.refusal import Refusal


class ForwardLandMixin:

    @property
    def world_map(self):
        """The base map with every installed mod's map overlay merged, in the mods' load order."""
        return self.view("legacy_world_map")()

    @property
    def geography(self):
        return self.view("legacy_geography")()

    def tile_owner_map(self):
        return self.view("tile_owner_map")()

    def tiles_owned_by(self, actor_id):
        return self.view("tiles_owned_by")[actor_id]

    def settlement_spec(self, by_sea=False):
        return self.view("settlement_spec")(by_sea=by_sea)

    def settlement_candidates(self, by_sea=False):
        return self.view("settlement_candidates")(by_sea)

    def settlement_outfit_cost(self, spec, tile_id=None):
        return self.view("settlement_outfit_cost")(spec, tile_id)

    def colony_rows(self):
        return self.view("colonies")()

    def found_colony(self, tile_id):
        """(ok, text): found a colony on `tile_id`."""
        answer = self.send(FoundColony(tile_id))
        if isinstance(answer, Refusal):
            return False, answer
        return True, answer["text"]
