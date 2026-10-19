"""An actor whose class sets `lends_from_purse` is offered to borrowers by the credit market, and a civilisation
that names a `variant_of` base does not play beside it as a partner.

Slow topic: it builds a whole game (not in the quick tier)."""
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
GAME = S.Sim(NODES, list(ORDER), random.Random(1), events=False, manual=True, civ=civ)
GAME.refresh_lender_offers()
offers = GAME.actors.state.purses.offers
check("a purse-lending actor is offered to borrowers", LENDER_ID in offers, sorted(offers))
PURSES = GAME.actors.state.purses
check("its offer is its purse and its deposit in the pool, as a firm's is",
      abs(offers.get(LENDER_ID, 0.0) - PURSES.purse(LENDER_ID) - PURSES.deposit(LENDER_ID)) < 1e-6, offers.get(LENDER_ID))
check("a church, which does not set the flag, is not offered", "church:home" not in offers, sorted(offers))

PARTNER = "han_china_100ad"
plain = S.Sim(NODES, list(ORDER), random.Random(1), events=False, manual=True, civ=S.load_civ("rome_100ad"))
check("the base case has the partner", PARTNER in plain.partner_countries(), plain.partner_countries())
variant = dict(S.load_civ("rome_100ad"), variant_of=PARTNER)
stand_in = S.Sim(NODES, list(ORDER), random.Random(1), events=False, manual=True, civ=variant)
check("a variant of the partner's civilisation is not played beside it", PARTNER not in stand_in.partner_countries(), stand_in.partner_countries())
