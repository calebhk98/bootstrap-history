"""Complaint 190: works repeated across the land. A disease benefit that holds only while the doors are open is not
called permanent, the typed `rollout` lines read, and a hungry nation that is handed food loses fewer people, each on
inputs built here. Coverage, rollouts, clinics against the disease burden, the working day and the schooling flow are
test_public_works_wiring on stand-ins."""
QUICK_TOPIC = True

from .harness import *  # noqa: F401,F403

from sim.engine.core import TECH_EFFECTS, demography

CLINICS = "ben_district_clinics"

# a benefit that holds only while the doors are open and for the share reached is not promised as permanent
from sim.projects.permanent_benefit import permanent_parts

check("a knowledge node's disease benefit is permanent", any("disease" in part for part in permanent_parts(
      NODES["germ_theory"], TECH_EFFECTS["germ_theory"])), permanent_parts(NODES["germ_theory"], TECH_EFFECTS["germ_theory"]))
check("clinics' disease benefit is not called permanent", not any("disease" in part for part in permanent_parts(
      NODES[CLINICS], TECH_EFFECTS[CLINICS])), permanent_parts(NODES[CLINICS], TECH_EFFECTS[CLINICS]))

from sim.ui.proto.typed import parse_typed

check("the typed line `rollout <id> 50` reads",
      parse_typed("rollout %s 50" % CLINICS)[0] == {"cmd": "rollout", "id": CLINICS, "share": 50.0}, parse_typed("rollout %s 50" % CLINICS))
check("the typed line `rollout` alone lists", parse_typed("rollout")[0] == {"cmd": "rollout"})

population_step = demography.Population.step   # the function under test, called by name
people = demography.Population.stationary(1.0e6)
hungry_food = 0.6 * people._subsistence_food()
flows_without = population_step(people.copy(), hungry_food, jitter=False)
flows_with = population_step(people.copy(), hungry_food + 0.2 * people._subsistence_food(), jitter=False)
check("a hungry nation that is handed food loses fewer people", flows_with.deaths < flows_without.deaths,
      (flows_with.deaths, flows_without.deaths))
