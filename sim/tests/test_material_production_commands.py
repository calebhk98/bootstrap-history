"""`build nitre`: the one command that lets a player manually produce a
material rather than only buy it, and the shortage-remedy messages that
point at commands like it.

Regrouped from test_round8_fixes.py - see CLAUDE.md's test-file
reorganisation note. Checks moved verbatim; each one's own comment explains
the break it guards.
"""
from .harness import *  # noqa: F401,F403


# SPLIT-SUITE NOTE (not a content change, see this split's own report): the
# original monolithic file left a module-level `s` bound to an unrelated Sim
# from many hundreds of lines earlier (test_literacy_market_pricing.py's own
# `s = sim(civ="rome_100ad", capital=1e9)`), and the check just below reads
# `s.NITRE_COST_PER_M2` - a class constant (economy.py), not instance state -
# rather than `s_ni`, the Sim it actually builds two lines down. Almost
# certainly a copy-paste slip in the original; left exactly as found rather
# than silently fixed. Reproduced here (instead of a stray NameError) so the
# split changes nothing about what this check verifies.
_sim_class = S.Sim

# --- BREAK: `buy nitre`. Saltpetre is made, not mined, and there was no
# command that made any: only step(), which took 5% of a MANUAL player's
# capital every year they were short, silently.
s_ni = sim(capital=100000.0)
_laid = s_ni.build_nitre(20000)
check("nitre beds can be laid by hand, and cost what the quote says",
      _laid == 20000 and abs(s_ni.capital
                             - (100000.0 - 20000 * _sim_class.NITRE_COST_PER_M2
                                * s_ni.price_index)) < 1e-6,
      (_laid, s_ni.capital))
check("...and they actually supply saltpetre",
      s_ni._own_material_supply("nitre") > 0, s_ni._own_material_supply("nitre"))
s_ni2 = sim(capital=10.0)
check("...and one you cannot afford changes nothing at all",
      s_ni2.build_nitre(20000) == 0.0 and s_ni2.nitre_bed_m2 == 0.0
      and s_ni2.capital == 10.0,
      (s_ni2.nitre_bed_m2, s_ni2.capital))
_r_ni, _, _ = proto([{"cmd": "quote", "what": "nitre", "n": 20000},
                     {"cmd": "buy", "what": "nitre", "n": 20000},
                     {"cmd": "buy", "what": "nitre", "n": -1}])
check("the nitre quote and the nitre purchase agree on the price",
      _r_ni[0].get("to_lay_it") is not None
      and _r_ni[1].get("ok") is False,        # 400 denarii cannot buy 40,000
      (_r_ni[0].get("to_lay_it"), _r_ni[1].get("error")))
check("a negative nitre order is refused, not credited",
      _r_ni[2].get("ok") is False, _r_ni[2])

# --- BREAK: a MANUAL player's capital was spent on nitre beds by step().
s_mn = sim(capital=100000.0, manual=True)
s_mn.binding = "saltpetre"
_cap_before = s_mn.capital
s_mn.policy["auto_mine"] = False
for _ in range(3):
    s_mn.step()
check("with the automatic policies off, nothing lays a nitre bed but you",
      s_mn.nitre_bed_m2 == 0.0, s_mn.nitre_bed_m2)

# --- BREAK: "SHORT OF SALTPETRE: work at 5% of plan" for thirty years, with
# no way to find out what saltpetre was for or what would fix it.
s_rm = sim(capital=100000.0)
for _b in ("charcoal", "saltpetre", "iron"):
    _msg = s_rm.shortage_remedy(_b)
    check("a %s shortage names a command that would end it" % _b,
          "buy " in _msg or "quote " in _msg, _msg[:80])
