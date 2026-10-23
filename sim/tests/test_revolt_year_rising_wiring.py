"""Complaints 484 and 486: what the stability phase does with a rising's outcome (`RevoltYearMixin._rising`) and with a disputed
accession (`_disputed_accession`). The outcome rule (`revolt.resolve`) and the world-event writer are replaced by recorders; the mixin
runs on a stand-in game carrying only what it reads. The rules are in test_stability_rules."""

QUICK_TOPIC = True

from types import SimpleNamespace
from unittest import mock

from .harness import check

from sim.agents import revolt
from sim.engine import revolt_year
from sim.engine.revolt_year import RISINGS_KEPT, RevoltYearMixin


class Game(RevoltYearMixin):
    """The parts of a Sim that a rising touches, recording what it does to them."""

    def __init__(self):
        self.struck = []
        self.transferred = []
        self.fought = []

    def strike_from_force(self, owner, soldiers):
        self.struck.append((owner, soldiers))

    def transfer_tile(self, tile, new_owner, cause):
        self.transferred.append((tile, new_owner, cause))


def outcome(kind, rising_lost=3.0, garrison_lost=7.0, probability=0.6):
    return SimpleNamespace(kind=kind, rising_win_probability=probability, rising_lost=rising_lost, garrison_lost=garrison_lost)


def rising(kind, on_seat=False, cause="unrest", record=None):
    record = record or SimpleNamespace(risings=[], ruler_age=50, ruler_backer="", accession_due=False, succession_challenger="faction_a")
    world = SimpleNamespace(rng_for=lambda *key: SimpleNamespace(random=lambda: 0.25))
    game = Game()
    garrison = SimpleNamespace(soldiers=40.0)
    with mock.patch.object(revolt_year.revolt, "resolve", return_value=outcome(kind)) as resolve, \
            mock.patch.object(revolt_year.world_events, "record") as record_event:
        result = game._rising("rome", world, record, "tile_a", 12.4, 2.0, garrison, 3.0, on_seat, 100, cause)
    return game, record, resolve, record_event, result


game, record, resolve, record_event, result = rising(revolt.TILE_LOST)
check("the rule is given the rising's soldiers and strength, the garrison's, whether it is the seat, and the tile's draw",
      resolve.call_args.args == (12.4, 2.0, 40.0, 3.0, False, 0.25), resolve.call_args)
check("the outcome kind is returned", result == revolt.TILE_LOST, result)
check("the world event is a revolt of the owner on the tile, with the outcome, the odds and the dead",
      record_event.call_args.args[1:] == ("revolt",) and record_event.call_args.kwargs == {
          "actors": ["rome"], "tiles": ["tile_a"], "cause": "unrest", "outcome": revolt.TILE_LOST,
          "rising_win_probability": 0.6, "rising_lost": 3.0, "garrison_lost": 7.0}, record_event.call_args)
check("the rising is kept on the state's record with its year, tile, kind and rounded soldiers",
      record.risings == [{"year": 100, "tile": "tile_a", "kind": revolt.TILE_LOST, "soldiers": 12}], record.risings)
check("the garrison's dead come off the owner's force", game.struck == [("rome", 7.0)], game.struck)
check("a won rising off the seat takes the tile from every owner", game.transferred == [("tile_a", None, "revolt")], game.transferred)

game, record, *_ = rising(revolt.PUT_DOWN)
check("a rising put down changes no tile and no ruler",
      game.transferred == [] and not record.accession_due and record.ruler_age == 50, (game.transferred, record))

with mock.patch.object(revolt_year.ruler, "opening_age", return_value=21):
    game, record, *_ = rising(revolt.RULER_REPLACED, on_seat=True)
check("a won rising at the seat replaces the ruler, backed by the rising, and calls an accession",
      record.ruler_age == 21 and record.ruler_backer == "rising" and record.accession_due and game.transferred == [],
      (record, game.transferred))
with mock.patch.object(revolt_year.ruler, "opening_age", return_value=21):
    _game, record, *_ = rising(revolt.RULER_REPLACED, on_seat=True, cause="disputed_accession")
check("a disputed accession won puts the challenger on the throne", record.ruler_backer == "faction_a", record.ruler_backer)

crowded = SimpleNamespace(risings=[{"year": number} for number in range(RISINGS_KEPT)], ruler_age=50, ruler_backer="",
                          accession_due=False, succession_challenger="")
_game, crowded, *_ = rising(revolt.PUT_DOWN, record=crowded)
check("only the latest risings are kept", len(crowded.risings) == RISINGS_KEPT and crowded.risings[-1]["year"] == 100
      and crowded.risings[0]["year"] == 1, crowded.risings)


def accession(backing, challenger="faction_a", seat="seat"):
    record = SimpleNamespace(succession_challenger=challenger)
    world = SimpleNamespace(faction_backing=lambda: backing)
    game = Game()
    game.fought = []
    game._rising = lambda *arguments: game.fought.append(arguments)
    game._garrison_on = lambda owner, tile: None
    game.campaign_site = lambda tile: SimpleNamespace(ruggedness=0.0)
    game.tile_fortification = lambda tile: 0.0
    with mock.patch.object(revolt_year.battle, "terrain_factor", return_value=1.0), \
            mock.patch.object(revolt_year.unrest, "rising_soldiers", return_value=90.0) as soldiers, \
            mock.patch.object(revolt_year.unrest, "rising_strength", return_value=5.0):
        game._disputed_accession("rome", world, record, seat, {"seat": 1000.0}, 0.0, 1.0, 100)
    return game, record, soldiers


game, record, soldiers = accession({"faction_b": 1.0})
check("a challenger no faction backs raises no army and is dropped", game.fought == [] and record.succession_challenger == "")
game, record, soldiers = accession({"faction_a": 1.0}, seat=None)
check("with no seat there is no accession to fight", game.fought == [] and record.succession_challenger == "")
game, record, soldiers = accession({"faction_a": 1.0, "faction_b": 3.0})
check("a backed challenger fights at the seat with its share of the backing, and the dispute is closed",
      soldiers.call_args.args == (1000.0, 0.25) and len(game.fought) == 1 and game.fought[0][3] == "seat"
      and game.fought[0][-2:] == (100, "disputed_accession") and record.succession_challenger == "", (soldiers.call_args, game.fought))
