"""Complaint 185: the state assesses every actor by one rule. Tested between actors built here with a stand-in for the
world's levy rule; the labour pool, the wage, the market and the shared category are the named scenarios in
test_actor_firms_compete_scenario."""

QUICK_TOPIC = True
from types import SimpleNamespace

from .harness import *  # noqa: F401,F403

from sim.agents.api import ActorRegistry, ActorsState
from sim.engine.state import ActorRecord

# ---- one rule assesses every actor (actors built here; the world answers the levy rule)
registry = ActorRegistry(ActorsState(home_country="home"))
state_actor = registry.ensure_government("home")
scales = {}
SCALE_LINE = 0.5


def levy_world():
    return SimpleNamespace(
        visible_scale_of=lambda payer: scales[payer.actor_id],
        levy_shares=lambda scale, protection: (0.10 * scale, 0.05 * scale) if scale > SCALE_LINE else (0.0, 0.0))


def taxpayer(actor_id, scale):
    scales[actor_id] = scale
    return registry.add(actor_id, ActorRecord(kind="firm", money=1.0e6))


rich = taxpayer("firm:rich", 0.8)
twin = taxpayer("firm:twin", 0.8)
small = taxpayer("firm:small", 0.1)
levy_of = lambda payer, taxable=1.0e6: state_actor.assess(payer, taxable, levy_world())
check("two taxpayers of equal visible scale are assessed equally, and by the levy rule of that scale",
      levy_of(rich) == levy_of(twin) and levy_of(rich)[0] > 0.0
      and abs(levy_of(rich)[0] - (0.10 + 0.05) * 0.8 * 1.0e6) < 1e-6, levy_of(rich))
check("a taxpayer the state has not noticed pays nothing", levy_of(small)[0] == 0.0, levy_of(small))
check("a levy is by purpose: requisition and office, each a share of the taxable income",
      abs(levy_of(rich)[1]["requisition"] - 0.08 * 1.0e6) < 1e-6 and abs(levy_of(rich)[1]["office"] - 0.04 * 1.0e6) < 1e-6
      and levy_of(rich, -5.0)[0] == 0.0, levy_of(rich))
treasury_before = state_actor.money
payer_before = rich.money
collected = state_actor.collect(rich, 1.0e6, levy_world())
check("collecting a levy moves exactly what it took from the payer to the treasury, booked by purpose",
      collected > 0.0 and abs((payer_before - rich.money) - collected) < 1e-6
      and abs((state_actor.money - treasury_before) - collected) < 1e-6
      and abs(sum(rich.record.outlays.values()) - collected) < 1e-6, (collected, rich.record.outlays))

