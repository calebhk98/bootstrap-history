"""The plain Python of the stability phase's per-tile arithmetic, chained from the rule functions the kernel reproduces
(`sim/campaigns/stability_kernels.py`): one tile at a time, as the phase read it before the kernel."""
from sim.agents import authority, liability, unrest
from sim.world import battle


def plain_tile(people, registered, land_taken, eaten_over_need, garrison_soldiers, garrison_equipment, garrison_supply,
               ruggedness, fortification, felt, collective, rate, organised, reference_kg):
    """(unrest share, rising soldiers, rising strength, garrison strength, hold, rises) of one tile."""
    rule = liability.COLLECTIVE if collective else liability.INDIVIDUAL
    burden = unrest.liability_burden(rule, rate, registered, people)
    share = unrest.unrest(felt + land_taken, unrest.hunger(eaten_over_need), burden)
    soldiers = unrest.rising_soldiers(people, share, organised)
    strength = unrest.rising_strength(soldiers, reference_kg)
    against = 0.0
    if garrison_soldiers > 0.0:
        terrain = battle.terrain_factor(ruggedness, fortification)
        against = battle.effective_strength(garrison_soldiers, garrison_equipment, reference_kg, garrison_supply, terrain)
    return share, soldiers, strength, against, authority.hold(against, strength), unrest.rises(strength, against)
