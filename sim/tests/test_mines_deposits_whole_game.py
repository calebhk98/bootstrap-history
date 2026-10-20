"""Complaint 416 (415): the ore sites are tested on stub deposits below; the whole-game checks are scenarios: a mine names
a deposit the seat has found, and what the agent economy's ore firms raise is drawn from the found deposits.
Builds games, so it is not a quick topic."""
import types

from .harness import *  # noqa: F401,F403
from sim.refusal import cause_of

from sim.engine import economy_port_sites

# --- scenarios: a whole game on purpose.
bare = sim(surveyed=())
check("a game that has found no coal deposit opens no coal mine, and says to prospect",
      bare.open_mine("coal", 10.0) == 0.0 and cause_of(bare.mine_refusal) == "no_deposit_found", bare.mine_refusal)
check("the known mines of the held tiles are already found",
      bool(bare.found_deposits("iron")), bare.found_deposits("iron"))

game = sim()
tile = next(row["tile_id"] for row in game.found_deposits("iron"))
before = sum(row["remaining_tonnes"] for row in game.found_deposits("iron") if row["tile_id"] == tile)
game.economy.agent.economy()
game.step()
after = sum(row["remaining_tonnes"] for row in game.found_deposits("iron") if row["tile_id"] == tile)
check("a year of the agent economy's ore extraction draws on the tile's deposits", after <= before, (before, after))


# --- the sites of the ore recipes, from deposits stated here (no game): the seat's found deposits plus the
# partner economies' tiles, one limit a tile in runs of ore a year.
def deposit_row(deposit_id, tile_id, room_tonnes, grade_kg_per_tonne=500.0, remaining_tonnes=1000.0):
    return {"id": deposit_id, "tile_id": tile_id, "room_tonnes_per_year": room_tonnes,
            "grade_kg_per_tonne": grade_kg_per_tonne, "remaining_tonnes": remaining_tonnes}


class StubSim:
    """Just what the site rule asks of a seat: the catalogue's ore goods, its found and its partner deposits."""
    world_map = types.SimpleNamespace(catalogue=lambda name: {"iron": {"ore_goods": {"iron_ore_kg": ["smelt"]}}})

    state = types.SimpleNamespace(economy=None)   # no forest to regrow

    def __init__(self, found, partner):
        self.found, self.partner, self.drawn = found, partner, []

    def found_deposits(self, resource_id):
        return list(self.found) if resource_id == "iron" else []

    def partner_deposits(self, resource_id, tile_ids):
        return [row for row in self.partner if row["tile_id"] in tile_ids] if resource_id == "iron" else []

    def draw_deposit(self, deposit_id, tonnes):
        self.drawn.append((deposit_id, tonnes))


ORE_KG_PER_RUN = 50.0
outputs = {"iron_ore_kg": {"iron_ore_kg": ORE_KG_PER_RUN}, "wheat_kg": {"wheat_kg": 1.0}}
stub = StubSim(found=[deposit_row("a1", "tile_a", 10.0), deposit_row("a2", "tile_a", 5.0), deposit_row("w", "tile_w", 0.0)],
               partner=[deposit_row("p1", "tile_p", 20.0, grade_kg_per_tonne=250.0), deposit_row("q1", "tile_q", 99.0)])
all_limits = economy_port_sites.site_limits(stub, outputs, ("tile_p",))
limits = {limit.tile: limit for limit in all_limits}
check("the ore recipe is sited on the seat's found tiles and the economy's partner tiles, and nowhere else",
      set(limits) == {"tile_a", "tile_w", "tile_p"} and all(limit.recipe_id == "iron_ore_kg" for limit in all_limits),
      sorted(limits))
check("a tile's limit is the runs a year its deposits' room allows: room times ore per tonne of resource, over the run's ore",
      abs(limits["tile_a"].capacity_runs_per_year - (10.0 + 5.0) * 2.0 * 1000.0 / ORE_KG_PER_RUN) < 1e-9
      and abs(limits["tile_p"].capacity_runs_per_year - 20.0 * 4.0 * 1000.0 / ORE_KG_PER_RUN) < 1e-9
      and limits["tile_a"].yield_factor == 1.0, limits)
check("a tile whose deposits are worked out keeps a limit of nothing, so the recipe does not run anywhere it likes",
      limits["tile_w"].capacity_runs_per_year == 0.0, limits["tile_w"])

# --- what the firms raised is drawn from the tile's deposits, the one with most left first.
drawing = StubSim(found=[deposit_row("small", "tile_a", 1.0, remaining_tonnes=10.0),
                         deposit_row("big", "tile_a", 1.0, remaining_tonnes=500.0)], partner=[])
economy_port_sites.deplete(drawing, {("iron_ore_kg", "tile_a"): 4000.0}, outputs)
raised_ore_tonnes = 4000.0 * ORE_KG_PER_RUN / 1000.0
check("firms' ore is drawn from the tile's deposit with most left first, in tonnes of the resource",
      drawing.drawn == [("big", raised_ore_tonnes / 2.0)], drawing.drawn)
drawing.drawn.clear()
economy_port_sites.deplete(drawing, {("iron_ore_kg", "tile_a"): 40000.0}, outputs)
check("when the first deposit is emptied the next is drawn, and no deposit is drawn below nothing",
      drawing.drawn == [("big", 500.0), ("small", 10.0)], drawing.drawn)
