"""Scenario for COMMODITIES.md section 0/7.1 in a whole game: a copper_wire_kg demand far beyond the copper market binds
`resource_throttle` on copper, where before the key was not tracked at all. No realistic combination of real nodes' wire
draws (the largest, el2_ring_main_distribution, is 8,000 kg over 4 years) reaches the hundreds of tonnes a year it takes to
outrun Rome's copper market, so the demand is set directly; this proves the WIRING, not a claim about ordinary play.
The rules are in test_commodities_wired_in."""
from .harness import *  # noqa: F401,F403

game = unopened_sim(capital=1e9)
game._material_demand_cache = {"copper_wire_kg": 100000.0}
game.annual_material_demand = lambda: game._material_demand_cache
throttle = game.resource_throttle()
check("scenario: a copper_wire_kg demand far beyond the copper market binds resource_throttle on copper",
      throttle < 0.95 and game.binding == "copper", (throttle, game.binding))
