"""What mod effect operations hand to the normal rules (Complaint 496): money crosses a named edge through the ledger, goods through the
economy's book against a named edge, a death share is sent to the demography owner, a tile moves
through the game's own transfer with the cause, and the base game's hazards use kill_people. Each is called on a stand-in game with the
collaborator replaced by a recorder; the argument rules are test_mod_effects."""
from types import SimpleNamespace
from unittest import mock

from sim.agents.api import edges
from sim.demography.api import KillPeople
from sim.engine import mod_effects
from sim.tests import hazards_host, module_harness
from sim.engine.mod_effects import ModEffects
from sim.engine.mods import ModError
from sim.land.api import TransferTile
from sim.refusal import cause_of

from .bridge_send import attach_send
from .harness import *  # noqa: F401,F403
from sim.tests import event_stand_in

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

# --- killing people: the demography owner is sent the death share (it cuts the cohorts or the strata, and writes the event).
def _death_game():
    sent = []
    return SimpleNamespace(send=lambda command: sent.append(command) or {"kind": command.kind}, sent=sent)


killing = _death_game()
entry = effects.kill_people(killing, "partner", 0.25, "a curse", tiles=["tile_a"], flood=3)
check("a death share is sent to the demography owner with the mod's own kind, the country, the cause, the tiles and the facts",
      killing.sent == [KillPeople("partner", 0.25, "a curse", kind=ACME + ":deaths", tiles=("tile_a",), facts={"flood": 3})]
      and entry == {"kind": ACME + ":deaths"}, killing.sent)
refused_shares, untouched = [], []
for share, cause in ((0.1, ""), (1.5, "too many")):
    refusing = _death_game()
    try:
        effects.kill_people(refusing, "partner", share, cause)
    except ModError:
        refused_shares.append(share)
    untouched.append(refusing.sent == [])
check("a missing cause or a share above one is refused before anyone is sent a death", refused_shares == [0.1, 1.5] and all(untouched))

# --- a tile transfer is a TransferTile command with the cause.
transfers = []
tile_game = SimpleNamespace(send=lambda command: transfers.append(command) or command.to_actor)
effects.transfer_tile(tile_game, "tile_a", "partner", "a treaty", control="garrisoned")
check("transfer_tile sends the tile, the new holder, the control and the cause to the owner of the tiles", transfers == [TransferTile("tile_a", "partner", "a treaty", "garrisoned")], transfers)
try:
    effects.transfer_tile(tile_game, "tile_a", "home", " ")
except ModError:
    transfers.append("refused")
check("a transfer with no cause is refused and the owner is not asked", transfers[-1] == "refused" and len(transfers) == 2, transfers)

# --- the base game's hazards use the same operation, with their kind and loss, and tell every playing seat.
hazard_module = hazards_host.build(seat_list={"joined": ["seat"], "playing": ["seat"]},
                                   answers={KillPeople: lambda command: {"year": 100, "facts": {"died": 321.0}}})
hazard_module.hit_country("partner", {"kind": "flood", "cause": "a flood", "population_loss": 0.1})
killed, told = module_harness.sent(hazard_module)
check("a hazard's hit is a KillPeople command with the hazard's loss, cause and kind",
      (killed.country, killed.share, killed.cause, killed.kind, killed.facts) == ("partner", 0.1, "a flood", "flood", {"population_loss": 0.1}), killed)
check("each playing seat gets a world_hazard line stating the hazard, country and the number who died",
      told.seat == "seat" and told.kind == "world_hazard" and told.facts == {"hazard": "flood", "country": "partner", "died": 321.0}, told)
