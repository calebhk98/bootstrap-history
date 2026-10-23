"""SCENARIO (Complaint 658): in the home game, officials left unpaid shrink the state's reach, authority follows it, the agents'
view of the state reads authority, and a partner's reach is a share. Each reader's rule is in test_state_reach_readers."""
from .harness import *  # noqa: F401,F403

sim = unopened_sim

from sim.engine.agents_port import SimWorld
from sim.agents import budget


def starve(game, unpaid_share=0.999):
    """Leave `unpaid_share` of the administration line unpaid."""
    world = SimWorld(game)
    need = budget.officials_kept(world) * world.pay_per_person_year("scribe")
    world.government().record.unfunded = {"administration": unpaid_share * need}


fed, starved = sim(civ="rome_100ad"), sim(civ="rome_100ad")
starve(starved)

check("the reach is a share", 0.0 <= starved.state_reach() <= fed.state_reach() <= 1.0,
      (starved.state_reach(), fed.state_reach()))
check("officials left unpaid shrink the reach of the home state", starved.state_reach() < fed.state_reach(),
      (starved.state_reach(), fed.state_reach()))
check("authority is the reach worn by consent, so it follows the reach",
      starved.state_authority() < fed.state_authority(), (starved.state_authority(), fed.state_authority()))
check("the agents' view of the state reads authority", SimWorld(fed).state_reach() == fed.state_authority())
check("a partner's reach is a share read from its own country's view",
      0.0 <= fed.partner_state_reach("han_china_100ad") <= 1.0, fed.partner_state_reach("han_china_100ad"))
