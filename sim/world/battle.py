"""A battle as a rule on two forces' effective strength, with losses on both sides and a probabilistic outcome.

Effective strength is numbers times the quality of the equipment each soldier is supplied with, times the supply
state of the force, times the terrain it fights on. The chance the attacker wins rises with its share of the
total strength; a draw decides it, so no side is typed the winner and a weaker force sometimes wins. Both sides
lose men in proportion to the other's share of the strength, the loser more. Plain functions of numbers: the
engine reads the tiles, the equipment and the supply and hands them in."""
from typing import NamedTuple

from sim.constants import declare

EQUIPMENT_QUALITY_EXPONENT = declare(
    "EQUIPMENT_QUALITY_EXPONENT", 0.5, kind="temporary_heuristic", unit="exponent",
    source=None, confidence="D",
    why="How fast fighting quality rises with the iron and ammunition a soldier is supplied with, against the "
        "reference soldier's. A weapon-by-weapon exchange model (range, rate of fire, protection) would replace "
        "it; until then an equipment burden ten times the reference counts a little over three times.",
    retire="a combat model by weapon and protection")

BATTLE_DECISIVENESS = declare(
    "BATTLE_DECISIVENESS", 2.0, kind="temporary_heuristic", unit="exponent on the strength ratio",
    source=None, confidence="D",
    why="How sharply the larger effective strength wins. Lanchester's square law gives two for aimed fire; the "
        "work is not read here, so the figure is a labelled placeholder.",
    retire="a combat model by weapon and protection")

CASUALTY_SCALE = declare(
    "CASUALTY_SCALE", 0.08, kind="temporary_heuristic", unit="share of a force lost in a battle between equals",
    source=None, confidence="D",
    why="Casualties in one battle between forces of equal strength. No source read; a record of battles by arms "
        "and ground would give it.",
    retire="a combat model by weapon and protection")

LOSER_CASUALTY_FACTOR = declare(
    "LOSER_CASUALTY_FACTOR", 2.5, kind="temporary_heuristic", unit="ratio of the loser's losses to the winner's",
    source=None, confidence="D",
    why="The beaten side loses more, most of it in the rout. No source read.",
    retire="a combat model by weapon and protection")

TERRAIN_DEFENCE_MAX = declare(
    "TERRAIN_DEFENCE_MAX", 0.5, kind="temporary_heuristic", unit="extra strength of a defender on the roughest ground",
    source=None, confidence="D",
    why="A defender's gain from broken ground, up to this share of its strength, rising with the tile's ruggedness "
        "index toward it. Slope, cover and the ground's own measures would replace the single index.",
    retire="a combat model by weapon and protection")

RUGGEDNESS_HALF_EFFECT = declare(
    "RUGGEDNESS_HALF_EFFECT", 150.0, kind="temporary_heuristic", unit="ruggedness index (map layer)",
    source=None, confidence="D",
    why="The ruggedness at which a defender has half of the greatest terrain gain.",
    retire="a combat model by weapon and protection")


class Outcome(NamedTuple):
    attacker_won: bool
    attacker_win_probability: float
    attacker_lost: float
    defender_lost: float


def equipment_quality(equipment_kg: float, reference_kg: float) -> float:
    """Fighting quality of a soldier supplied with `equipment_kg` a year, against the reference soldier's."""
    if reference_kg <= 0.0:
        raise ValueError("the reference equipment burden must be positive: %r" % (reference_kg,))
    return (max(0.0, equipment_kg) / reference_kg) ** EQUIPMENT_QUALITY_EXPONENT


def terrain_factor(ruggedness: float, fortification: float = 0.0) -> float:
    """What the ground and any works on it add to a defender's strength: 1 on flat open ground."""
    rugged = max(0.0, ruggedness)
    return (1.0 + TERRAIN_DEFENCE_MAX * rugged / (rugged + RUGGEDNESS_HALF_EFFECT)) * (1.0 + max(0.0, fortification))


def effective_strength(soldiers: float, equipment_kg: float, reference_kg: float, supply_state: float,
                       terrain: float = 1.0) -> float:
    """Numbers times equipment quality times supply state (share of its ration met, 0 to 1) times terrain."""
    return (max(0.0, soldiers) * equipment_quality(equipment_kg, reference_kg)
            * max(0.0, min(1.0, supply_state)) * max(0.0, terrain))


def attacker_win_probability(attacker: float, defender: float) -> float:
    if attacker <= 0.0:
        return 0.0
    if defender <= 0.0:
        return 1.0
    weight = attacker ** BATTLE_DECISIVENESS
    return weight / (weight + defender ** BATTLE_DECISIVENESS)


def fight(attacker: float, defender: float, attacker_soldiers: float, defender_soldiers: float,
          draw: float) -> Outcome:
    """One battle between forces of the given effective strengths and numbers. `draw` is a uniform number in
    [0, 1) from the caller's seeded stream; the attacker wins when it falls below its chance."""
    chance = attacker_win_probability(attacker, defender)
    attacker_won = draw < chance
    total = attacker + defender
    attacker_share = attacker / total if total > 0.0 else 0.5
    attacker_rate = CASUALTY_SCALE * 2.0 * (1.0 - attacker_share)
    defender_rate = CASUALTY_SCALE * 2.0 * attacker_share
    if attacker_won:
        defender_rate *= LOSER_CASUALTY_FACTOR
    else:
        attacker_rate *= LOSER_CASUALTY_FACTOR
    return Outcome(attacker_won, chance, attacker_soldiers * min(1.0, attacker_rate),
                   defender_soldiers * min(1.0, defender_rate))
