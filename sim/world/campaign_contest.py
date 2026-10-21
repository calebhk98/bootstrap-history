"""An army's days on a tile: it eats, wears down, and where an enemy stands it fights.

`camp` feeds an army from the tile it stands on and from a column, then takes its losses; a force shut in
by a siege is `camp`ed with no column, so it eats the tile's stores until they are gone. `engage` is one battle
between two armies on a tile. `march` says how far an army gets along a route in the days it has. Plain
functions of an `Army` and a `Site` (the readings of the tile); the engine builds the site from geography."""
from dataclasses import dataclass
from typing import Dict, List, Sequence, Tuple

from sim.constants import declare
from sim.world import battle, campaign_attrition, campaign_supply
from sim.world.army_record import Army


ASSAULT_MIN_CHANCE = declare(
    "ASSAULT_MIN_CHANCE", 0.5, kind="temporary_heuristic", unit="chance of winning",
    source=None, confidence="D",
    why="A besieger storms the place once its chance of winning reaches this; short of it, it waits for the "
        "defenders' stores to run out. A commander's choice with its own stakes would replace the single threshold.",
    retire="Complaints/486: commanders as actors with their own valuations")

RETREAT_BELOW_FED_SHARE = declare(
    "RETREAT_BELOW_FED_SHARE", 0.5, kind="temporary_heuristic", unit="share of the ration met",
    source=None, confidence="D",
    why="A besieger whose ration falls below this share lifts the siege and goes home. Engels (ch. 1) shows armies "
        "cannot be kept on half rations for long; the figure is not read from him.",
    retire="Complaints/486: commanders as actors with their own valuations")

SIEGE_TURN_DAYS = 30.0     # the span a siege is resolved in: the days between one look at the stores and the next


@dataclass
class Site:
    """What a tile gives an army that stands on it. `drawn_kcal` is what armies have already taken this year."""
    tile: str
    food_kcal_per_year: float
    drawn_kcal: float = 0.0
    disease_per_year: float = 0.0       # the tile's endemic loss of working-age people
    ruggedness: float = 0.0
    fortification: float = 0.0          # extra strength of the defender behind works, as a share


def camp(army: Army, days: float, site: Site, carried_kg_per_day: float, pay_owed_years: float) -> Dict[str, float]:
    """`army` spends `days` on `site`: it eats (the land first, then the column, then its own stock), its stock
    refills from any surplus, and hunger, disease and unpaid pay take their share of the men. Returns what it lost
    by cause and the share of its ration it got."""
    if army.soldiers <= 0.0 or days <= 0.0:
        return {"fed_share": army.supply_state, "hunger": 0.0, "disease": 0.0, "desertion": 0.0,
                "taken_carriage_kg": 0.0}
    forage = campaign_supply.tile_stock_kg(site.food_kcal_per_year, site.drawn_kcal)
    feeding = campaign_supply.feed(army.soldiers, days, army.food_kg, forage, carried_kg_per_day * days,
                                   campaign_supply.train_capacity_kg(army.animals))
    site.drawn_kcal += campaign_supply.kcal_of(feeding.taken_forage_kg)
    army.food_kg = feeding.stock_after_kg
    army.supply_state = feeding.fed_share
    lost = campaign_attrition.losses(army.soldiers, days, feeding.fed_share, site.disease_per_year, pay_owed_years)
    army.soldiers -= sum(lost.values())
    return dict(lost, fed_share=feeding.fed_share, taken_carriage_kg=feeding.taken_carriage_kg)


def strength_of(army: Army, reference_kg: float, terrain: float = 1.0) -> float:
    return battle.effective_strength(army.soldiers, army.equipment_kg, reference_kg, army.supply_state, terrain)


def engage(attacker: Army, defender: Army, site: Site, reference_kg: float, draw: float) -> battle.Outcome:
    """The attacker and the defender fight on `site`; both lose men, and the result says who won. The defender has the
    ground's advantage, and its works if the site has any."""
    outcome = battle.fight(strength_of(attacker, reference_kg),
                           strength_of(defender, reference_kg, battle.terrain_factor(site.ruggedness, site.fortification)),
                           attacker.soldiers, defender.soldiers, draw)
    attacker.soldiers = max(0.0, attacker.soldiers - outcome.attacker_lost)
    defender.soldiers = max(0.0, defender.soldiers - outcome.defender_lost)
    return outcome


def march(legs: Sequence[Tuple[str, float]], progress_days: float,
          days_available: float) -> Tuple[List[Tuple[str, float]], float, float]:
    """An army on a route of legs [(tile reached, days)], with `progress_days` already marched on the first and
    `days_available` left. Returns ([(tile, days marched on it)] for the legs it finishes, days into the next leg,
    days used)."""
    finished: List[Tuple[str, float]] = []
    used, progress = 0.0, max(0.0, progress_days)
    for tile, leg_days in legs:
        need = max(0.0, leg_days - progress)
        if used + need > days_available + 1e-9:
            return finished, progress + (days_available - used), days_available
        used += need
        finished.append((tile, need))
        progress = 0.0
    return finished, 0.0, used


def combine(armies: Sequence[Army]) -> Army:
    """The armies on one tile on one side as a single force: numbers, food and animals added, equipment and supply
    state averaged by head."""
    total = sum(army.soldiers for army in armies)
    weight = (lambda value: sum(value(army) * army.soldiers for army in armies) / total) if total > 0.0 else (lambda value: 0.0)
    first = armies[0]
    return Army("combined", first.owner, first.tile, total, weight(lambda army: army.equipment_kg),
                sum(army.food_kg for army in armies), sum(army.animals for army in armies),
                weight(lambda army: army.supply_state), 0.0)


def share_out(armies: Sequence[Army], before: float, combined: Army) -> None:
    """Hand a combined force's end state back to the armies it was made of: each keeps its share of the men now left
    and of the food now held, and the supply state the force had."""
    ratio = combined.soldiers / before if before > 0.0 else 0.0
    stock = sum(army.food_kg for army in armies)
    for army in armies:
        army.food_kg = army.food_kg / stock * combined.food_kg if stock > 0.0 else 0.0
        army.soldiers *= ratio
        army.supply_state = combined.supply_state


def legs_of(route: Dict) -> List[Tuple[str, float]]:
    """[(tile reached, days)] along a route as geography's `route` returns it: one entry per tile, a leg's days
    being its own march plus any handling or waiting before it."""
    return [(leg["to"], float(leg["days"]) + float(leg.get("handling_days", 0.0)) + float(leg.get("wait_days", 0.0)))
            for leg in route["legs"]]


def siege_turn(attacker: Army, defender: Army, site: Site, carried_kg_per_day: float, reference_kg: float,
               draw: float, days: float = SIEGE_TURN_DAYS, attacker_pay_owed_years: float = 0.0) -> Dict:
    """One turn of an attacker besieging a defender (all the defending armies on the tile, `combine`d) on `site`.
    The defender, shut in, eats the tile's stores with no column; the attacker eats what is left and what its
    column brings. Then the attacker storms if its chance is good enough, withdraws if its ration has failed, or
    waits. `result` is one of "continues", "attacker_withdraws", "attacker_destroyed", "defenders_gone",
    "attacker_won" or "attacker_lost"."""
    camp(defender, days, site, 0.0, 0.0)
    ours = camp(attacker, days, site, carried_kg_per_day, attacker_pay_owed_years)
    report = {"attacker_fed": attacker.supply_state, "defender_fed": defender.supply_state, "outcome": None,
              "carriage_taken_kg": ours["taken_carriage_kg"]}
    terrain = battle.terrain_factor(site.ruggedness, site.fortification)
    if attacker.soldiers < 1.0:
        return dict(report, result="attacker_destroyed")
    if defender.soldiers < 1.0:
        return dict(report, result="defenders_gone")
    if attacker.supply_state < RETREAT_BELOW_FED_SHARE:
        return dict(report, result="attacker_withdraws")
    chance = battle.attacker_win_probability(strength_of(attacker, reference_kg), strength_of(defender, reference_kg, terrain))
    if chance < ASSAULT_MIN_CHANCE:
        return dict(report, result="continues")
    outcome = engage(attacker, defender, site, reference_kg, draw)
    return dict(report, outcome=outcome, result="attacker_won" if outcome.attacker_won else "attacker_lost")
