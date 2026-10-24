"""Complaint 483: an owner map (tile -> owner and control level) seeded from the civilisation files, read by
`tiles_held`, `country_of` and the ways record, changed only by one transfer, with one owner per tile. Each rule is called on
an owner map and stand-ins the test builds; the colony and transfer wiring is test_tile_owner_wiring."""
import glob
import json
from types import SimpleNamespace

from .harness import *  # noqa: F401,F403
from sim.economy.api import EconomySetup
from sim.engine import invariants
from sim.geography.api import tile_owners, tiles_held

QUICK_TOPIC = True


class ControlStore:
    """The `control` tile store: a tile's control level, or None."""

    def __init__(self):
        self.levels = {}

    def set(self, tile, level):
        if level is None:
            self.levels.pop(tile, None)
        else:
            self.levels[tile] = level

    def get(self, tile):
        return self.levels.get(tile)


# ---- seeded owners match the civilisation files -------------------------------------------------------------
for path in sorted(glob.glob(os.path.join(ROOT, "data", "civilizations", "*_*.json"))):
    civ = json.load(open(path))
    if "id" not in civ:
        continue
    seeded, conflicts = tile_owners.seed({civ["id"]: tiles_held(civ)})
    check("%s: the seeded owners give back the tiles its file lists" % civ["id"],
          tiles_held(civ, owners=seeded) == tiles_held(civ) and not conflicts)

# ---- a double claim is caught ----------------------------------------------------------------------------------
seeded, conflicts = tile_owners.seed({"alpha": ["t1", "t2"], "beta": ["t2", "t3"]})
check("the first claimant keeps a tile two files claim and the second is reported",
      tile_owners.owner_of(seeded, "t2") == "alpha" and conflicts == [{"tile": "t2", "owner": "alpha", "claimant": "beta"}],
      (seeded, conflicts))
check("a tile listed by two actors is a problem",
      [found["cause"] for found in tile_owners.problems(seeded, {"alpha": ["t2"], "beta": ["t2"]})]
      == ["double_claim", "owned_by_other"])
try:
    tile_owners.transfer(seeded, "t1", "beta", "not_a_level")
    refused = False
except tile_owners.TileOwnerError:
    refused = True
check("a control level that the data does not list is refused", refused)
check("the control levels are data", {"core", "tributary", "enclave", "claimed", "ungoverned"} <= set(tile_owners.control_levels()))

# ---- transfer ----------------------------------------------------------------------------------------------------
owners, _conflicts = tile_owners.seed({"home": ["t1", "t2", "t3"]})
controls = ControlStore()
tile_owners.seed_controls(owners, controls)
check("seeding writes the seed level for every owned tile", set(controls.levels.values()) == {tile_owners.seed_level()}
      and set(controls.levels) == {"t1", "t2", "t3"})
setup = SimpleNamespace(tile_owners=owners, tiles={}, civ_id="home")
check("country_of reads the owner map", EconomySetup.country_of(setup, "t1") == "home")
previous = tile_owners.transfer(owners, "t1", "rival", "garrisoned", controls=controls)
check("a transfer moves the tile, keeps one owner and sets the level",
      previous == "home" and tile_owners.owner_of(owners, "t1") == "rival" and controls.get("t1") == "garrisoned"
      and tile_owners.tiles_of(owners, "home") == ["t2", "t3"] and tile_owners.tiles_of(owners, "rival") == ["t1"])
check("country_of follows the transfer", EconomySetup.country_of(setup, "t1") == "rival")
check("releasing a tile leaves it unowned and clears its level",
      tile_owners.transfer(owners, "t1", None, controls=controls) == "rival" and tile_owners.owner_of(owners, "t1") is None
      and controls.get("t1") is None)
tile_owners.transfer(owners, "t1", "rival", "garrisoned", controls=controls)
check("built ways take their owner from the tiles they stand on",
      tile_owners.way_owner(owners, "t1") == "rival" and tile_owners.way_owner(owners, "t1|t2") is None
      and tile_owners.way_owner(owners, "t2|t3") == "home")

# ---- the invariant -------------------------------------------------------------------------------------------------
def stand_in_game(colonies_by_seat):
    """A game of the pieces the invariant reads: the seats' colonies, the owner map and the control store."""
    seats = {seat: SimpleNamespace(holdings=SimpleNamespace(colonies=[{"tile": tile} for tile in tiles]))
             for seat, tiles in colonies_by_seat.items()}
    return SimpleNamespace(state=SimpleNamespace(seats=seats, economy=SimpleNamespace(tile_owners=owners)),
                           world_map=None, stores=SimpleNamespace(view=lambda _name: controls))


def fails(game):
    try:
        invariants.check_tile_owner_invariants(game)
    except AssertionError:
        return True
    return False


tile_owners.transfer(owners, "t1", "home", "garrisoned", controls=controls)
check("the invariant holds when no colony stands on another's tile", invariants.check_tile_owner_invariants(stand_in_game({"home": []})))
check("the invariant fails when a colony stands on a tile another actor owns", fails(stand_in_game({"other": ["t1"]})))
check("the invariant holds when the colony's seat owns its tile", not fails(stand_in_game({"home": ["t1"]})))
check("the invariant fails when two seats' colonies stand on one tile", fails(stand_in_game({"home": ["t1"], "other": ["t1"]})))
