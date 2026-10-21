"""Rome's opening states the enslaved share as an initial condition: a bonded stratum held by the rich.
The rules are the founding of strata from the declared shares (strata_seed.seed_strata), the scaling that keeps their
proportions when the people counted change (follow_population) and the keep of the bonded (stratum_year.settle_keep),
each called on a registry of its own with a stand-in world. No game is built."""
QUICK_TOPIC = True

from .harness import *  # noqa: F401,F403

from sim.agents import ledger
from sim.agents.api import ActorsState, ActorRegistry, profile_from_civilisation, seed_strata, stratum_id
from sim.agents.strata_seed import follow_population
from sim.agents.stratum_year import settle_keep, true_up_keep, EDGE_ECONOMY

from .agents_fake_world import FakeWorld

civ = S.load_civ("rome_100ad")
declared = civ["cast"]["strata"]
check("Rome declares its strata", len(declared) >= 2, declared)
check("the declared shares add up to every person", abs(sum(entry["share"] for entry in declared) - 1.0) < 1e-9,
      sum(entry["share"] for entry in declared))
check("the enslaved share carries its source and confidence",
      civ["_internal"]["cast"]["source"] and civ["_internal"]["cast"]["confidence"] in "ABCD")
declared_bonded = [entry for entry in declared if entry.get("bonded")]
check("Rome declares exactly one bonded stratum", len(declared_bonded) == 1, declared_bonded)
check("the declared owner of the bonded is a declared stratum",
      declared_bonded[0]["owner"] in {entry["name"] for entry in declared}, declared_bonded)


class CostedWorld(FakeWorld):
    """A world that counts a fixed number of people and prices a person-year of keep."""

    def __init__(self, people, keep_cost):
        super().__init__()
        self.people = people
        self.keep_cost = keep_cost

    def population_total(self):
        return self.people

    def subsistence_cost_per_person_year(self):
        return self.keep_cost


def founded_registry(people):
    state = ActorsState()
    state.home_country = civ["id"]
    profile = profile_from_civilisation(civ)
    profile.population = people
    state.countries[civ["id"]] = profile
    registry = ActorRegistry(state)
    seed_strata(registry, CostedWorld(people, 1.0))
    return registry


def members_of(registry):
    return {actor.record.stratum: actor.record.members for actor in registry.of_kind("stratum")}


registry = founded_registry(1.0e6)
founded = [actor for actor in registry.of_kind("stratum") if actor.record.country is None]
bonded = [actor for actor in founded if actor.is_bonded()]
check("founding the strata makes exactly one bonded stratum", len(bonded) == 1, [actor.actor_id for actor in bonded])
slaves = bonded[0]
check("the bonded stratum is founded with the declared share of the people (initial condition)",
      abs(slaves.record.members - declared_bonded[0]["share"] * 1.0e6) < 1e-6, slaves.record.members)
check("every declared stratum is founded with its declared share of the people",
      all(abs(members_of(registry)[entry["name"]] - entry["share"] * 1.0e6) < 1e-6 for entry in declared))
check("the bonded are kept by a stratum that exists",
      registry.actors.get(slaves.neighbour_id(slaves.record.plan["owner"])) is not None, slaves.record.plan)

# the people counted change: the strata scale together and keep their proportions
world = CostedWorld(3.0e6, 1.0)
factor = follow_population(registry, world)
check("following the counted people scales every stratum by one factor", abs(factor - 3.0) < 1e-9, factor)
after = members_of(registry)
check("following the counted people keeps the bonded share",
      abs(after["slaves"] / sum(after.values()) - declared_bonded[0]["share"]) < 1e-9, after)

# the keep: the owner is paid the bonded's labour product and pays their food
owner = registry.actors[slaves.neighbour_id(slaves.record.plan["owner"])]
slaves.record.labour_product = 500.0
keep_cost = slaves.record.members * 2.0
settle_keep(registry, CostedWorld(3.0e6, 2.0))
check("the bonded eat from their owner's keep", slaves.record.income.get("keep of bonded", 0.0) == keep_cost,
      slaves.record.income)
check("the owner is paid the labour product and pays the keep: net is product less keep",
      abs(owner.money - (500.0 - keep_cost)) < 1e-6, (owner.money, 500.0, keep_cost))
check("the labour product is handed over once", slaves.record.labour_product == 0.0)
check("the keep is recorded as the bonded's allowance", abs(slaves.record.allowance - keep_cost) < 1e-6,
      slaves.record.allowance)

# Left out on purpose: whether a live game's bonded stratum still holds about the sourced share of the people after
# two years (Scheidel 2005: eight to fifteen per cent) is baseline validation (CLAUDE.md 4.2), not a unit rule. It
# belongs in an ensemble run over seeds that asserts the distribution of the share.


# The keep is made up to the year's prices before the year's turns. A bonded stratum with no keep yet (just founded) or
# a keep set at last year's lower prices would otherwise meet the year with part of its food unmet, and the famine
# rule would kill a share of the bonded in the first year.
fresh_registry = founded_registry(1.0e6)
fresh_slaves = [actor for actor in fresh_registry.of_kind("stratum") if actor.is_bonded()][0]
fresh_owner = fresh_registry.actors[fresh_slaves.neighbour_id(fresh_slaves.record.plan["owner"])]
check("a bonded stratum starts with no keep", fresh_slaves.record.allowance == 0.0)
true_up_keep(fresh_registry, CostedWorld(1.0e6, 2.0))
check("making up the keep feeds a newly founded bonded stratum its whole food at the year's price",
      abs(fresh_slaves.record.allowance - fresh_slaves.record.members * 2.0) < 1e-6, fresh_slaves.record.allowance)
check("the keeper paid it", abs(fresh_owner.money + fresh_slaves.record.allowance) < 1e-6, fresh_owner.money)
true_up_keep(fresh_registry, CostedWorld(1.0e6, 3.0))
check("when prices rise the keeper pays only the difference",
      abs(fresh_slaves.record.allowance - fresh_slaves.record.members * 3.0) < 1e-6, fresh_slaves.record.allowance)
check("and the keeper's purse fell by exactly the keep", abs(fresh_owner.money + fresh_slaves.record.allowance) < 1e-6)
paid_so_far = fresh_slaves.record.allowance
true_up_keep(fresh_registry, CostedWorld(1.0e6, 1.0))
check("when prices fall nothing is taken back", fresh_slaves.record.allowance == paid_so_far, fresh_slaves.record.allowance)
