"""Complaint 658: what a state enforces, steals back, ceilings, diffuses and answers follows its reach, the share its
paid officials collect over its roads (620), not a typed capacity. Each reader is called on a built game, once with
the officials paid and once with their pay left unpaid; it moves the way its rule says."""
from .harness import *  # noqa: F401,F403

sim = unopened_sim

from sim.engine.agents_port import SimWorld
from sim.engine.data import load_civ
from sim.agents import budget, enforcement


def starve(game, unpaid_share=0.999):
    """Leave `unpaid_share` of the administration line unpaid."""
    world = SimWorld(game)
    need = budget.officials_kept(world) * world.pay_per_person_year("scribe")
    world.government().record.unfunded = {"administration": unpaid_share * need}


class Patents(SimWorld):
    """A world with one patent held by someone else."""

    def patent_entry(self, node_id):
        return {"holder": "holder", "licensees": []}


fed, starved = sim(civ="rome_100ad"), sim(civ="rome_100ad")
starve(starved)

# ---- the reach itself --------------------------------------------------------------------------------
check("no civilisation record carries a typed state capacity",
      all("state_capacity" not in load_civ(civ_id)
          for civ_id in ("rome_100ad", "norse_900ad", "han_china_100ad", "england_1300", "mexica_1500")))
check("the reach is a share", 0.0 <= starved.state_reach() <= fed.state_reach() <= 1.0,
      (starved.state_reach(), fed.state_reach()))
check("officials left unpaid shrink the reach of the home state", starved.state_reach() < fed.state_reach(),
      (starved.state_reach(), fed.state_reach()))
check("authority is the reach worn by consent, so it follows the reach",
      starved.state_authority() < fed.state_authority(), (starved.state_authority(), fed.state_authority()))
check("the agents' view of the state reads authority", SimWorld(fed).state_reach() == fed.state_authority())

# ---- (a) the same thing as collection: enforcement, standing, demands, notice, diffusion ----------------------
check("a patent is enforced less often where the state reaches less",
      enforcement.expected_damages(Patents(starved), "infringer", "node", 100.0)
      < enforcement.expected_damages(Patents(fed), "infringer", "node", 100.0))
check("lenders trust a state as far as it reaches",
      SimWorld(starved).government().credit_standing(SimWorld(starved))
      < SimWorld(fed).government().credit_standing(SimWorld(fed)))
check("a state that reaches less notices a household less", starved.state_notice() < fed.state_notice(),
      (starved.state_notice(), fed.state_notice()))
for each in (fed, starved):
    each.medical_diffusion_index = lambda: 1.0
check("public-health guidance is followed less where the state reaches less",
      starved.medical_diffusion_relief() < fed.medical_diffusion_relief(),
      (starved.medical_diffusion_relief(), fed.medical_diffusion_relief()))

# ---- (b) needs specific staff: mines, order and woods are in test_state_guards_and_inspectors.py

# ---- the partner's reach is its own country's, from its own officials and roads --------------------------------------
partner = "han_china_100ad"
check("a partner's reach is a share read from its own country's view",
      0.0 <= fed.partner_state_reach(partner) <= 1.0, fed.partner_state_reach(partner))
