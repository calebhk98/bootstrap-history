"""Complaints 528 and 510: the scan reads one plant of each concern the society holds and the plants its owners run, each row with its owner.
`held_concerns`, `held_business`, `running_businesses` and `scan_game` run on a stand-in game with a fake world; the pay rule, the cost sum and the
summary are test_concerns_that_pay."""

QUICK_TOPIC = True

from types import SimpleNamespace

from .harness import check

from sim.agents.api import Business
from sim.engine import concern_scan_run

FIELDS = {"node", "owner", "size", "sells", "takings", "upkeep", "wages", "carried", "costs", "margin", "pays"}


class FakeWorld:
    """One plant per unit of size: takings 10, upkeep 2, wages 3, rent 1; only "pays" sells in the book."""
    year = 0
    hours_per_person_year = 1.0

    def __init__(self, game=None):
        pass

    def entry_gross(self, node_id, rivals, entrants):
        return 10.0 if node_id == "pays" else 4.0

    def plant_costs(self, node_id):
        return 2.0, 3.0

    def site_rent(self, node_id, capacity=1.0, tile=None):
        return 1.0 * capacity

    def concern_staff(self, node_id):
        return {}

    def sells_on_book(self, node_id):
        return node_id == "pays"


def game(done=("pays", "loses", "knowledge"), seats=(("founder", ["pays"]),), actors=(("firm:1", ["loses"]),)):
    cast = SimpleNamespace(actors={actor_id: SimpleNamespace(record=SimpleNamespace(business=Business.running(plants))) for actor_id, plants in actors},
                           state=SimpleNamespace(home_country=None))
    return SimpleNamespace(
        view=lambda name: (lambda: cast) if name == "cast" else FakeWorld, done=set(done),
        is_concern_node=lambda node_id: node_id != "knowledge",
        state=SimpleNamespace(seats={seat_id: SimpleNamespace(projects=SimpleNamespace(business=Business.running(plants))) for seat_id, plants in seats}),
        actors=cast)


stand_in = game()
check("the concerns held are the finished nodes that describe a going concern, in sorted order", concern_scan_run.held_concerns(stand_in) == ["loses", "pays"], None)
held = concern_scan_run.held_business(stand_in)
check("the held business runs one plant of each concern and belongs to no one",
      sorted(held.operating()) == ["loses", "pays"] and held.owner_id == concern_scan_run.HELD_BUSINESS_ID, None)
order = [owner for owner, _business in concern_scan_run.running_businesses(game(seats=(("second", []), ("founder", [])), actors=(("firm:2", []), ("firm:1", []))))]
check("every owner's business is read, seats first and then actors, each in id order", order == ["founder", "second", "firm:1", "firm:2"], order)

result = concern_scan_run.scan_game(stand_in)
check("the scan covers every concern the society holds, each row carrying the fields", result["count"] == 2
      and all(set(row) == FIELDS for row in result["pay"] + result["losers"]), result)
running = result["running"]
check("the plants the owners run are scanned too, each with its owner", running["count"] == 2
      and {row["owner"] for row in running["pay"] + running["losers"]} == {"founder", "firm:1"}, running)
nothing = concern_scan_run.scan_game(game(done=(), seats=(("founder", []),), actors=()))
check("a society holding nothing and running nothing scans zero", nothing["count"] == 0 and nothing["running"]["count"] == 0, nothing)
