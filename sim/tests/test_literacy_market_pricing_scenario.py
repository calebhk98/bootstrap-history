"""literacy_market_pricing scenario (Complaint 640 audit): literacy bounds hiring, and materials and hires respond to
demand, through a game. The labour price pressure and the commodity ledger are tests in test_literacy_market_pricing."""
import collections

from .harness import *  # noqa: F401,F403
from sim.refusal import cause_of

# =============================================================================
# FINDINGS_ROUND2 section Q: literacy bounds who you can hire.
# =============================================================================

# --- Q: a low-literacy society genuinely cannot hire scribes a high-literacy
# one can, at any price. This is the exact case the finding asked for: "if
# only 0.001% of the population can read... you can only hire 0.001%".
s_hi = unopened_sim(civ="rome_100ad", capital=1e9)
s_lo = unopened_sim(civ="norse_900ad", capital=1e9)
check("a low-literacy society's literate-trade pool is smaller than a "
      "high-literacy one's",
      s_lo.labour.literate_capacity("scribe") < s_hi.labour.literate_capacity("scribe"),
      "norse=%.2f rome=%.2f" % (s_lo.labour.literate_capacity("scribe"),
                                s_hi.labour.literate_capacity("scribe")))
ok_hi, why_hi = s_hi.labour.hire("scribe", 3)
ok_lo, why_lo = s_lo.labour.hire("scribe", 3)
check("money alone cannot hire scribes a low-literacy society has nobody to "
      "supply, at any price",
      ok_hi and not ok_lo and cause_of(why_lo) == "literacy_wall",
      "rome ok=%s / norse ok=%s (%s)" % (ok_hi, ok_lo, why_lo))

# --- Q: the same wall applies to TEACHING a trade into existence, the only
# way engineer/chemist/machinist/optician can ever exist at all (hire()
# refuses them outright until train() has made them real).
ok_lo, why_lo = s_lo.labour.train("machinist", 2)
check("a society that cannot read cannot be taught machinists into "
      "existence either",
      not ok_lo and cause_of(why_lo) == "literacy_wall", why_lo)
ok_hi, why_hi = s_hi.labour.train("machinist", 2)
check("the same teaching succeeds where enough people can read",
      ok_hi, why_hi)

# --- Q: the institutional scholar ceiling (staff_capacity, which is what
# auto_hire actually grows) is bounded by literacy_elite too, not only the
# named `scholar`/`scribe` trades hired one at a time.
run_it(s_hi, "school_founded")
run_it(s_lo, "school_founded")
sc_hi, sc_lo = s_hi.labour.staff_capacity()[0], s_lo.labour.staff_capacity()[0]
check("a school trains fewer scholars where fewer of the propertied class "
      "can read",
      sc_lo < sc_hi, "norse sc=%.2f rome sc=%.2f" % (sc_lo, sc_hi))

# --- Q: printing, schools and libraries WIDEN the pool -- the whole point --
# rather than raising a number nothing reads. Played out on Norse, where
# there is room for it to move; Rome starts at this file's own reference
# literacy and is not expected to move much.
s = unopened_sim(civ="norse_900ad", capital=1e9)
cap0 = s.labour.literate_capacity("scribe")
s.apply_tech_effects("rag_paper")
s.apply_tech_effects("printing_press")
cap1 = s.labour.literate_capacity("scribe")
# THRESHOLD CHANGED, deliberately, and the reason belongs here rather than in
# a commit message. This asserted cap1 > cap0 * 2, which was true of the
# original implementation because the pool was purely multiplicative: Norse
# elite literacy is a sixth of Rome's, so the ceiling came out at 0.2 people
# and printing multiplied a very small number. 0.2 people means "there is no
# such person in Scandinavia, at any price, ever", which is false about a
# society with rune-carvers who cut inscriptions for hire and, from the tenth
# century, priests who read Latin. The pool is now 1.5 findable people plus a
# literacy-scaled body on top, and no floor large enough to fix that falsehood
# can also leave room for a doubling. So the pair below pins both properties
# the mechanism actually needs, which is more than the single ratio did.
check("printing and paper widen the literate-trade hiring pool",
      cap1 > cap0 * 1.4, "before=%.2f after=%.2f" % (cap0, cap1))
check("a literate person can always be found, even before any teaching",
      cap0 >= 1.0, "norse scribe ceiling before teaching = %.2f" % cap0)

# =============================================================================
# FINDINGS_ROUND2 section R: the market responds to demand, and to supply.
# =============================================================================

# --- R, end to end: hiring the same trade repeatedly through `hire` really
# does cost more each time, not only in the internal factor.
s = unopened_sim(civ="rome_100ad", capital=1e9)
run_it(s, "workshop_first", "school_founded", "academy_network", "patron_imperial")
fees = []
for _ in range(3):
    before = s.capital
    ok, msg = s.labour.hire("millwright", 10)
    if not ok:
        break
    fees.append(before - s.capital)
check("hire's own fee rises the more of a trade you have taken on recently",
      len(fees) == 3 and fees[-1] > fees[0] * 1.15, fees)

# --- R: materials respond to demand too -- MARKET_SHARE (economy.py) was a
# supply ceiling with no price response, so buying up to it cost the same
# per tonne as buying one kilogram. Saltpetre (MARKET_SHARE 0.0: no open
# market for it at all without a trade route) makes the effect dramatic;
# gunpowder is the cheapest node that needs it.
s = unopened_sim(civ="rome_100ad", capital=1e9)
s.active["gunpowder"] = {}
# only gunpowder's inputs press on the market here, so what binds is its own; the rest of a fresh Rome's demand
# (alum, say, which nothing in reach makes) would otherwise be what the throttle names
_all_demand = s.annual_material_demand
s.annual_material_demand = lambda: collections.Counter(
    {material: tonnes for material, tonnes in _all_demand().items() if material in NODES["gunpowder"]["mat"]})
f_no_beds = s.material_price_factor("saltpetre")
cost_no_beds = s.project_cost("gunpowder")
throttle_no_beds = s.resource_throttle()
binding_no_beds = s.state.holdings.binding
_mms = s.material_market_summary()
_money_mat = S._agent_dispatch(s, NODES, {"cmd": "money"})
s.nitre_bed_m2 = 2_000_000.0
f_with_beds = s.material_price_factor("saltpetre")
cost_with_beds = s.project_cost("gunpowder")
throttle_with_beds = s.resource_throttle()
binding_with_beds = s.state.holdings.binding
check("demand for a material the market barely sells costs a real premium "
      "over the flat catalogue price",
      f_no_beds > 1.5, "%.3f" % f_no_beds)
check("owning enough of your own supply (nitre beds) relieves the premium "
      "-- this is 'opening a mine lowers what iron costs you', generalised",
      f_with_beds < f_no_beds, "no beds=%.3f with beds=%.3f" % (f_no_beds, f_with_beds))
check("project_cost itself falls once your own supply covers the demand",
      cost_with_beds < cost_no_beds * 0.7,
      "no beds=%.0f with beds=%.0f" % (cost_no_beds, cost_with_beds))
check("resource_throttle still throttles a material the market will not "
      "sell you at all",
      throttle_no_beds < 1.0 and binding_no_beds == "saltpetre", (throttle_no_beds, binding_no_beds))
check("...and saltpetre stops binding once your own supply covers the need",
      binding_with_beds != "saltpetre", (throttle_with_beds, binding_with_beds))
check("material_market_summary names a material trading above book price",
      bool(_mms) and "saltpetre" in _mms, _mms)
check("...and `money` itself carries the same line",
      bool(_money_mat.get("materials_costing_you_a_premium")), _money_mat)

# =============================================================================
# GENERALISED PRICING: data/review/COMMODITY_DYNAMISM.md's central
# finding, verified against a live Sim. 149 of the tree's 162 distinct
# material keys had a price read once from prices.json and never revisited,
# because MATERIAL_CHECKS/MARKET_SHARE above only ever named 13. The user's
# own test: "if I make an iron mine and flood the market, does the price
# update? What if I make aluminium via electricity? Same for foods, coffee,
# silk, whatever." Aluminium is the audit's worked failure - "no mine, no
# supply lever of any kind... nothing in economy.py even contains the string
# aluminium" - and is tested here BY NAME, on purpose, alongside silk, a
# second material nothing in this file has ever special-cased, to show the
# mechanism is general rather than a rule written for one commodity.
# =============================================================================

for _mat in ("aluminium_kg", "silk_kg"):
    s = unopened_sim(civ="rome_100ad", capital=1e9)
    # Demand is pinned at the market's own reachable tonnage, so the test
    # holds whatever level the solved price puts the fitted market at.
    # (a material nothing in reach makes has no market tonnage, so demand is pinned at a stated tonnage)
    _pinned_demand = 1000.0
    f_none = s.material_price_factor(_mat)
    check("a material with NO curated entry anywhere (%s) starts neutral "
          "with no demand pinned on it" % _mat,
          abs(f_none - 1.0) < 1e-9, f_none)
    s._material_demand_cache = {_mat: _pinned_demand}
    f_demand = s.material_price_factor(_mat)
    check("...but a real premium appears once demand for it is pinned high "
          "- the same response the 9 originally-tracked commodities always "
          "had, that this material never had before this pass",
          f_demand > 1.5, "%.3f" % f_demand)
    got = s.open_mine(_mat, 1e7, partial=False)
    for _ in range(int(s.MINE_LEAD_YEARS) + 1):
        s.year += 1
        s.commission_mines()
    check("opening your own production capacity in it (open_mine, "
          "generalised beyond the seven hand-named metals) actually "
          "commissions real standing capacity",
          s.mine_capacity.get(_mat, 0.0) > 0, s.mine_capacity.get(_mat))
    s._material_demand_cache = {_mat: _pinned_demand}
    f_mined = s.material_price_factor(_mat)
    check("...and flooding the market this way relieves the SAME premium, "
          "for a material this file has never named, purely because supply "
          "and demand are now real numbers rather than a rule",
          f_mined < f_demand, "before=%.3f after=%.3f" % (f_demand, f_mined))

# --- the effect actually reaches project_cost(), the number the game
# charges, not only an internal factor nothing reads - the same standard
# COMMODITY_DYNAMISM.md held the original 9 commodities to.
s = unopened_sim(civ="rome_100ad", capital=1e9)
check("mt2_duralumin_alloy is a real node that buys real aluminium_kg - "
      "not a synthetic example",
      NODES["mt2_duralumin_alloy"]["mat"].get("aluminium_kg", 0) > 0,
      NODES["mt2_duralumin_alloy"]["mat"])
s._material_demand_cache = {"aluminium_kg": 1000.0}
cost_no_mine = s.project_cost("mt2_duralumin_alloy")
s.open_mine("aluminium_kg", 1e7, partial=False)
for _ in range(int(s.MINE_LEAD_YEARS) + 1):
    s.year += 1
    s.commission_mines()
s._material_demand_cache = {"aluminium_kg": 1000.0}
cost_with_mine = s.project_cost("mt2_duralumin_alloy")
check("a real node's project_cost() itself falls once an aluminium mine "
      "covers demand pinned against it - the same standard the iron test "
      "elsewhere in this file already holds the originally-tracked "
      "commodities to",
      cost_with_mine < cost_no_mine, (cost_no_mine, cost_with_mine))

# --- a garbage material name is still refused, not silently accepted -
# generalising to "every material the tree prices" is not the same as
# accepting an arbitrary string. (Quoting and listing mines read no state the mine above changed.)
check("a material this file genuinely cannot price is still refused",
      s.mine_quote("not_a_real_material_xyz", 100.0) is None,
      s.mine_quote("not_a_real_material_xyz", 100.0))
check("...and mineable() agrees",
      s.mineable("aluminium") and s.mineable("aluminium_kg")
      and not s.mineable("not_a_real_material_xyz"),
      (s.mineable("aluminium"), s.mineable("aluminium_kg"),
       s.mineable("not_a_real_material_xyz")))

# --- the command surface itself accepts a generalised material name, not
# only the seven it used to: "buy mine aluminium_kg" must actually work.
_command_sim = unopened_sim()
_r_al = S._agent_dispatch(_command_sim, NODES, {"cmd": "buy", "what": "mine", "material": "aluminium_kg", "n": 0.1})
check("the command surface itself (not just the engine underneath it) "
      "accepts a material outside the original seven",
      _r_al.get("ok") is True, _r_al)
_r_bad = S._agent_dispatch(_command_sim, NODES, {"cmd": "buy", "what": "mine",
                                                 "material": "not_a_real_material_xyz", "n": 10})
check("...but still refuses a genuinely unpriced name, with a hint rather "
      "than a bare closed list",
      _r_bad.get("ok") is False and _r_bad.get("cause") == "unknown_material" and bool(_r_bad.get("choices")),
      _r_bad)

