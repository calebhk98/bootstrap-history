"""Colony rules as plain functions: what stops a founding, and one year of a colony's people (Complaint 190)."""
from sim.disease import api as disease

# a country must hold this many working-age people per settler sent
WORKING_AGE_PER_SETTLER = 10.0


def founding_refusal(tile_held, reachable_by_land, reachable_by_sea, has_settlement_work,
                     working_age, settlers, outfit_cost, spendable):
    """The cause a colony cannot be founded, or None: tile_held, unreachable, no_settlement_work, too_few_people,
    cannot_afford. `has_settlement_work` is for the route the tile needs (land, or sea when it is not reachable by land)."""
    if tile_held:
        return "tile_held"
    if not reachable_by_land and not reachable_by_sea:
        return "unreachable"
    if not has_settlement_work:
        return "no_settlement_work"
    if working_age < WORKING_AGE_PER_SETTLER * settlers:
        return "too_few_people"
    if outfit_cost > spendable:
        return "cannot_afford"
    return None


def advance_colony(colony, kcal_per_day_for, population_class, disease_burden):
    """One year of a colony's people, in place. `kcal_per_day_for(working_age)` is the food its hands raise from the
    tile; `population_class(children, working_age, elderly)` has `step` and `total`. True when the people have died out."""
    people = population_class(colony["children"], colony["working_age"], colony["elderly"])
    people.step(kcal_per_day_for(people.working_age), jitter=False, disease_burden=disease_burden)
    colony.update(children=people.children, working_age=people.working_age, elderly=people.elderly)
    return people.total < 1.0


def best_settlement_work(known, by_sea):
    """(node id, spec) of the work that sends the most settlers (ties by id) among `known` (node id, spec) pairs, over a
    voyage by sea only by works whose spec says `by_sea`; None when none fits."""
    fit = [(node_id, spec) for node_id, spec in known if spec.get("by_sea") or not by_sea]
    return max(fit, key=lambda item: (item[1]["settlers"], item[0]), default=None)


def outfit_cost(spec, money_per_labour_hour, disease_loss=0.0):
    """What outfitting the settlers costs: the hours each is given, at the society's money per hour of labour,
    for as many more as the place's yearly disease loss (a share) will take before the stated number is settled."""
    return (spec["settlers"] * spec["outfit_hours_per_settler"] * money_per_labour_hour
            * disease.nation.provisioning_factor(disease_loss))


def colony_people(colony):
    """Everyone in a colony: its three cohorts."""
    return colony["children"] + colony["working_age"] + colony["elderly"]
