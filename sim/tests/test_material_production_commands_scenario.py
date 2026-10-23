"""Scenario (Complaint 640 audit): `build nitre` in a whole game. The cost, refusal and remedy rules are tests in
test_material_production_commands; here the beds a player lays supply saltpetre, and with the automatic policies off a
year's step lays none."""
from .harness import *  # noqa: F401,F403


s_ni = unopened_sim(capital=hours_money(2020000))
s_ni.build_nitre(20000)
check("nitre beds that were laid actually supply saltpetre",
      s_ni._own_material_supply("nitre") > 0, s_ni._own_material_supply("nitre"))

# A MANUAL player's capital was once spent on nitre beds by step().
s_ni.capital = 100000.0
s_ni.binding = "saltpetre"
s_ni.policy["auto_mine"] = False
_beds_before = s_ni.nitre_bed_m2
s_ni.step()
check("with the automatic policies off, nothing lays a nitre bed but you",
      s_ni.nitre_bed_m2 == _beds_before, (_beds_before, s_ni.nitre_bed_m2))
