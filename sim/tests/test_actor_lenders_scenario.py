"""SCENARIO: in a game an actor of a kind that sets `lends_from_purse` is in the credit market's offers beside the firms,
and one that does not is not (Complaint 636). The rules are in `test_actor_lenders`."""
import random

from .harness import *  # noqa: F401,F403

from sim.agents.api import DeclaredKind, register_actor_kind

KIND = "test_lend_k3f9:abbey"
LENDER_ID = "abbey:one"
register_actor_kind(KIND, type("Abbey", (DeclaredKind,), {
    "kind": KIND, "lends_from_purse": True,
    "declaration": {"needs": {"food": 1.0}, "birth_rate": 0.0, "death_rate": 0.0, "famine_death_rate": 0.0}}))

civ = dict(S.load_civ("rome_100ad"))
civ["cast"] = dict(civ.get("cast") or {}, actors=list((civ.get("cast") or {}).get("actors") or ()) + [
    {"actor_id": LENDER_ID, "kind": KIND, "name": "abbey", "money": 5000.0, "params": {"members": 10.0}}])
GAME = build_unopened(lambda: S.Sim(NODES, list(ORDER), random.Random(1), events=False, manual=True, civ=civ))
GAME.refresh_lender_offers()
offers = GAME.actors.state.purses.offers
purses = GAME.actors.state.purses
check("a purse-lending actor is offered to borrowers", LENDER_ID in offers, sorted(offers))
check("its offer is its purse and its deposit, as a firm's is",
      abs(offers.get(LENDER_ID, 0.0) - purses.purse(LENDER_ID) - purses.deposit(LENDER_ID)) < 1e-6, offers.get(LENDER_ID))
check("a church, which does not set the flag, is not offered", "church:home" not in offers, sorted(offers))
