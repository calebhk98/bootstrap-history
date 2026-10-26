"""What mod effect operations hand to the normal rules (Complaint 496): money crosses a named edge through the ledger, goods through the
economy's book against a named edge, a death share cuts the home cohorts or a partner's strata and writes its event, a tile moves
through the game's own transfer with the cause, and the base game's hazards use kill_people. Each is called on a stand-in game with the
collaborator replaced by a recorder; the argument rules are test_mod_effects."""
from types import SimpleNamespace
from unittest import mock

from sim.agents.api import edges
from sim.engine import bridge_campaigns, mod_effects, world_hazards
from sim.engine.mod_effects import ModEffects
from sim.engine.mods import ModError
from sim.refusal import cause_of

from .bridge_send import attach_send
from .harness import *  # noqa: F401,F403

QUICK_TOPIC = True

ACME = "test_acme_k3f9"
effects = ModEffects(ACME)

# --- money through a named edge: payer to the edge, and the edge to the payee.
government, edge_account = object(), object()
money_game = SimpleNamespace(actors=SimpleNamespace(get=lambda actor_id: government if actor_id == "government:x" else None),
                             edge=lambda name: edge_account if name == edges.EDGE_OFFICIALS else None)
with mock.patch.object(mod_effects.agents_api.ledger, "transfer") as transfer:
    effects.pay_edge(money_game, "government:x", edges.EDGE_OFFICIALS, 10.0, "a bribe")
    effects.receive_from_edge(money_game, "government:x", edges.EDGE_OFFICIALS, 4.0, "returned")
check("pay_edge moves the amount from the actor to the named edge through the ledger, with its purpose",
      transfer.call_args_list[0].args == (government, edge_account, 10.0, "a bribe"), transfer.call_args_list)
check("receive_from_edge moves it the other way", transfer.call_args_list[1].args == (edge_account, government, 4.0, "returned"), transfer.call_args_list)
with mock.patch.object(mod_effects.agents_api.ledger, "transfer") as untouched:
    refused = []
    for edge, amount in ((edges.EDGE_OFFICIALS, -1.0), ("nowhere", 1.0)):
        try:
            effects.pay_edge(money_game, "government:x", edge, amount, "x")
        except ModError:
            refused.append(edge)
check("a negative amount or an undeclared edge is refused before the ledger is touched", refused == [edges.EDGE_OFFICIALS, "nowhere"] and not untouched.called)
with mock.patch.object(mod_effects.agents_api.ledger, "transfer") as own_edge:
    effects.pay_edge(SimpleNamespace(actors=money_game.actors, edge=lambda name: name), "government:x", "edge:%s:tithe" % ACME, 1.0, "own edge")
check("the mod's own namespaced edge is accepted", own_edge.call_args.args[1] == "edge:%s:tithe" % ACME)

# --- goods: a move from the named edge into the account (added) or from the account to the edge (removed), at a tile.
economy = object()
goods_game = SimpleNamespace(economy=SimpleNamespace(agent=SimpleNamespace(economy=lambda: economy)))
with mock.patch.object(mod_effects.economy_api, "move_goods") as move_goods:
    effects.add_goods(goods_game, "mod_account", "grain", "tile_a", 5.0, "a gift of grain")
    effects.remove_goods(goods_game, "mod_account", "grain", "tile_a", 2.0, "a fire")
added, removed = move_goods.call_args_list[0].args[1][0], move_goods.call_args_list[1].args[1][0]
check("add_goods books the economy's book with a move from the production edge into the account at the tile",
      move_goods.call_args_list[0].args[0] is economy and (added.giver, added.receiver, added.good, added.tile, added.quantity)
      == (mod_effects.economy_api.EDGE_PRODUCTION, "mod_account", "grain", "tile_a", 5.0), added)
check("remove_goods books a move from the account to the consumption edge",
      (removed.giver, removed.receiver, removed.quantity) == ("mod_account", mod_effects.economy_api.EDGE_CONSUMPTION, 2.0), removed)
with mock.patch.object(mod_effects.economy_api, "move_goods") as unmoved:
    try:
        effects.add_goods(goods_game, "mod_account", "grain", "tile_a", 1.0, "x", edge="somewhere")
    except ModError:
        pass
check("goods from an undeclared edge are refused before the book is touched", not unmoved.called)

# --- killing people: the home society by its cohorts, a partner by its strata; the event carries what died.
def _death_game(home_total=1000.0):
    shocks = []
    strata = [SimpleNamespace(record=SimpleNamespace(members=400.0, country="partner")), SimpleNamespace(record=SimpleNamespace(members=100.0, country="partner")),
              SimpleNamespace(record=SimpleNamespace(members=7.0, country="other"))]
    game = SimpleNamespace(civ={"id": "home"}, population=SimpleNamespace(total=home_total), shocks=shocks,
                           actors=SimpleNamespace(of_kind=lambda kind: strata), strata=strata)
    game._apply_population_mortality_shock = shocks.append
    return attach_send(game)


with mock.patch.object(bridge_campaigns.world_events, "record", side_effect=lambda game, kind, **fields: dict(kind=kind, **fields)) as recorded:
    partner_game = _death_game()
    entry = effects.kill_people(partner_game, "partner", 0.25, "a curse")
    home_game = _death_game()
    effects.kill_people(home_game, "home", 0.1, "a curse")
check("a death share cuts each of a partner's strata by that share and leaves another country's alone",
      [stratum.record.members for stratum in partner_game.strata] == [300.0, 75.0, 7.0] and partner_game.shocks == [], partner_game.strata)
check("the event is the mod's kind, names the country and the cause, and states how many died",
      entry["kind"] == ACME + ":deaths" and entry["actors"] == ["partner"] and entry["cause"] == "a curse" and abs(entry["died"] - 125.0) < 1e-9, entry)
check("a death share in the home society is applied to its cohorts as a mortality shock and not to the strata", home_game.shocks == [0.1]
      and [stratum.record.members for stratum in home_game.strata] == [400.0, 100.0, 7.0], home_game.shocks)
with mock.patch.object(bridge_campaigns.world_events, "record") as unrecorded:
    refused_shares = []
    for share, cause in ((0.1, ""), (1.5, "too many")):
        try:
            effects.kill_people(_death_game(), "partner", share, cause)
        except ModError:
            refused_shares.append(share)
check("a missing cause or a share above one is refused before anyone dies or any event is written", refused_shares == [0.1, 1.5] and not unrecorded.called)

# --- a tile transfer goes through the game's own transfer with the cause.
transfers = []
tile_game = attach_send(SimpleNamespace(transfer_tile=lambda tile, to_actor, control, cause=None: transfers.append((tile, to_actor, control, cause)) or to_actor))
effects.transfer_tile(tile_game, "tile_a", "partner", "a treaty", control="garrisoned")
check("transfer_tile hands the tile, the new holder, the control and the cause to the game's own transfer", transfers == [("tile_a", "partner", "garrisoned", "a treaty")], transfers)
try:
    effects.transfer_tile(tile_game, "tile_a", "home", " ")
except ModError:
    transfers.append("refused")
check("a transfer with no cause is refused and the game is not asked", transfers[-1] == "refused" and len(transfers) == 2, transfers)

# --- the base game's hazards use the same operation, with their kind and loss, and tell every playing seat.
seat_log = []
hazard_game = SimpleNamespace(playing_seats=lambda: ["seat"], state=SimpleNamespace(seats={"seat": SimpleNamespace(household=SimpleNamespace(log=seat_log))}))
with mock.patch.object(mod_effects.BASE_EFFECTS, "kill_people", return_value={"year": 100, "facts": {"died": 321.0}}) as kill:
    world_hazards.hit(hazard_game, "partner", {"kind": "flood", "cause": "a flood", "population_loss": 0.1})
check("a hazard's hit is a kill_people call by the base game with the hazard's loss, cause and kind",
      kill.call_args.args == (hazard_game, "partner", 0.1, "a flood") and kill.call_args.kwargs["kind"] == "flood" and kill.call_args.kwargs["population_loss"] == 0.1, kill.call_args)
check("each playing seat gets a world_hazard line stating the hazard, country and the number who died",
      len(seat_log) == 1 and cause_of(seat_log[0][1]) == "world_hazard" and seat_log[0][1].facts == {"hazard": "flood", "country": "partner", "died": 321.0}, seat_log)
