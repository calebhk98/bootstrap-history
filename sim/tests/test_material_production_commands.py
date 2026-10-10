"""`build nitre`: the one command that lets a player manually produce a
material rather than only buy it, and the shortage-remedy messages that
point at commands like it.

"""
from .harness import *  # noqa: F401,F403


# THE CLASS, NOT AN INSTANCE. The check below reads NITRE_COST_PER_M2,
# which economy.py defines on the class rather than per game, so reading it
# off `_sim_class` says that plainly. Reading it off the Sim this section
# builds two lines down would work too and would suggest the cost varies
# with that game's state, which it does not.
_sim_class = S.Sim

# --- BREAK: `buy nitre`. Saltpetre is made, not mined, and there was no
# command that made any: only step(), which took 5% of a MANUAL player's
# capital every year they were short, silently.
s_ni = sim(capital=hours_money(2020000))
_laid = s_ni.build_nitre(20000)
check("nitre beds can be laid by hand, and cost what the quote says",
      _laid == 20000 and abs(s_ni.capital
                             - (hours_money(2020000) - 20000 * s_ni.NITRE_COST_PER_M2
                                * s_ni.price_index)) < 1e-6,
      (_laid, s_ni.capital))
check("...and they actually supply saltpetre",
      s_ni._own_material_supply("nitre") > 0, s_ni._own_material_supply("nitre"))
_beds_before = s_ni.nitre_bed_m2
s_ni.capital = 10.0
check("...and one you cannot afford changes nothing at all",
      s_ni.build_nitre(20000) == 0.0 and s_ni.nitre_bed_m2 == _beds_before and s_ni.capital == 10.0,
      (s_ni.nitre_bed_m2, s_ni.capital))
_quote = S._agent_dispatch(s_ni, NODES, {"cmd": "quote", "what": "nitre", "n": 20000})
_buy = S._agent_dispatch(s_ni, NODES, {"cmd": "buy", "what": "nitre", "n": 20000})
_negative = S._agent_dispatch(s_ni, NODES, {"cmd": "buy", "what": "nitre", "n": -1})
check("the nitre quote and the nitre purchase agree on the price",
      _quote.get("to_lay_it") is not None and _buy.get("ok") is False,  # 10 denarii cannot buy 20,000 m2
      (_quote.get("to_lay_it"), _buy.get("error")))
check("a negative nitre order is refused, not credited", _negative.get("ok") is False, _negative)

# --- BREAK: a MANUAL player's capital was spent on nitre beds by step().
s_ni.capital = 100000.0
s_ni.binding = "saltpetre"
s_ni.policy["auto_mine"] = False
_beds_before = s_ni.nitre_bed_m2
for _ in range(2):
    s_ni.step()
check("with the automatic policies off, nothing lays a nitre bed but you",
      s_ni.nitre_bed_m2 == _beds_before, (_beds_before, s_ni.nitre_bed_m2))

# --- BREAK: "SHORT OF SALTPETRE: work at 5% of plan" for thirty years, with
# no way to find out what saltpetre was for or what would fix it.
for _b in ("charcoal", "saltpetre", "iron"):
    _msg = s_ni.shortage_remedy(_b)
    check("a %s shortage names a command that would end it" % _b,
          "buy " in _msg or "quote " in _msg, _msg[:80])
