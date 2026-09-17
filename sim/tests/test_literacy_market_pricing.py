"""literacy_market_pricing: split verbatim from the old test_regressions.py (original lines 3157-3534).

Moving contiguous blocks verbatim: no check below was reformatted, reworded or otherwise touched in the split.
"""
from .harness import *  # noqa: F401,F403

# =============================================================================
# FINDINGS_ROUND2 section Q: literacy bounds who you can hire.
# =============================================================================

# --- Q: a low-literacy society genuinely cannot hire scribes a high-literacy
# one can, at any price. This is the exact case the finding asked for: "if
# only 0.001% of the population can read... you can only hire 0.001%".
s_hi = sim(civ="rome_100ad", capital=1e9)
s_lo = sim(civ="norse_900ad", capital=1e9)
check("a low-literacy society's literate-trade pool is smaller than a "
      "high-literacy one's",
      s_lo.literate_capacity("scribe") < s_hi.literate_capacity("scribe"),
      "norse=%.2f rome=%.2f" % (s_lo.literate_capacity("scribe"),
                                s_hi.literate_capacity("scribe")))
ok_hi, why_hi = s_hi.hire("scribe", 3)
ok_lo, why_lo = s_lo.hire("scribe", 3)
check("money alone cannot hire scribes a low-literacy society has nobody to "
      "supply, at any price",
      ok_hi and not ok_lo and "literacy" in why_lo,
      "rome ok=%s / norse ok=%s (%s)" % (ok_hi, ok_lo, why_lo))

# --- Q: the same wall applies to TEACHING a trade into existence, the only
# way engineer/chemist/machinist/optician can ever exist at all (hire()
# refuses them outright until train() has made them real).
ok_lo, why_lo = sim(civ="norse_900ad", capital=1e9).train("machinist", 2)
check("a society that cannot read cannot be taught machinists into "
      "existence either",
      not ok_lo and "literacy" in why_lo, why_lo)
ok_hi, why_hi = sim(civ="rome_100ad", capital=1e9).train("machinist", 2)
check("the same teaching succeeds where enough people can read",
      ok_hi, why_hi)

# --- Q: the institutional scholar ceiling (staff_capacity, which is what
# auto_hire actually grows) is bounded by literacy_elite too, not only the
# named `scholar`/`scribe` trades hired one at a time.
s_hi = run_it(sim(civ="rome_100ad", capital=1e9), "school_founded")
s_lo = run_it(sim(civ="norse_900ad", capital=1e9), "school_founded")
sc_hi, sc_lo = s_hi.staff_capacity()[0], s_lo.staff_capacity()[0]
check("a school trains fewer scholars where fewer of the propertied class "
      "can read",
      sc_lo < sc_hi, "norse sc=%.2f rome sc=%.2f" % (sc_lo, sc_hi))

# --- Q: printing, schools and libraries WIDEN the pool -- the whole point --
# rather than raising a number nothing reads. Played out on Norse, where
# there is room for it to move; Rome starts at this file's own reference
# literacy and is not expected to move much.
s = sim(civ="norse_900ad", capital=1e9)
cap0 = s.literate_capacity("scribe")
s.apply_tech_effects("rag_paper")
s.apply_tech_effects("printing_press")
cap1 = s.literate_capacity("scribe")
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

# --- R: taking a large share of a trade's local supply raises what it costs
# (labour_price_factor), the same principle market_pressure already applies
# to slaves -- and it decays, the same way.
s = sim(civ="rome_100ad", capital=1e9)
f0 = s.labour_price_factor("millwright")
s._add_labour_pressure("millwright", 6 * s.HOURS_PER_PERSON_YEAR)
f1 = s.labour_price_factor("millwright")
check("leaning hard on a scarce trade's local supply raises what it costs",
      f1 > f0 * 1.5, "before=%.3f after=%.3f" % (f0, f1))
s.year += 5
f2 = s.labour_price_factor("millwright")
check("recent demand pressure decays: the same trade is not dearer forever",
      f2 < f1 and f2 < 1.3, "immediate=%.3f +5yr=%.3f" % (f1, f2))

# --- R: the SAME recent demand costs less once the trade's own supply is
# bigger -- this is "teaching fifty machinists is what makes hiring the
# fifty-first one cheap again", tested directly against pressure rather than
# waiting on a training run to mature.
thin = sim(civ="rome_100ad", capital=1e9)
thick = sim(civ="rome_100ad", capital=1e9)
thick.employees["millwright"] = 20.0
pressure_hours = 6 * thin.HOURS_PER_PERSON_YEAR
thin._add_labour_pressure("millwright", pressure_hours)
thick._add_labour_pressure("millwright", pressure_hours)
check("a bigger trained workforce in a trade makes the same recent demand "
      "cheaper to satisfy",
      thick.labour_price_factor("millwright") < thin.labour_price_factor("millwright"),
      "thin supply=%.3f thick supply=%.3f"
      % (thin.labour_price_factor("millwright"), thick.labour_price_factor("millwright")))

# --- R, end to end: hiring the same trade repeatedly through `hire` really
# does cost more each time, not only in the internal factor.
s = sim(civ="rome_100ad", capital=1e9)
run_it(s, "workshop_first", "school_founded", "academy_network", "patron_imperial")
fees = []
for _ in range(3):
    before = s.capital
    ok, msg = s.hire("millwright", 10)
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
s = sim(civ="rome_100ad", capital=1e9)
s.active["gunpowder"] = {}
f_no_beds = s.material_price_factor("saltpetre")
check("demand for a material the market barely sells costs a real premium "
      "over the flat catalogue price",
      f_no_beds > 1.5, "%.3f" % f_no_beds)
s.nitre_bed_m2 = 2_000_000.0
f_with_beds = s.material_price_factor("saltpetre")
check("owning enough of your own supply (nitre beds) relieves the premium "
      "-- this is 'opening a mine lowers what iron costs you', generalised",
      f_with_beds < f_no_beds, "no beds=%.3f with beds=%.3f" % (f_no_beds, f_with_beds))

# --- R: the price response actually reaches the number the game quotes and
# charges (project_cost), not only an internal factor nothing reads.
s = sim(civ="rome_100ad", capital=1e9)
s.active["gunpowder"] = {}
cost_no_beds = s.project_cost("gunpowder")
s.nitre_bed_m2 = 2_000_000.0
cost_with_beds = s.project_cost("gunpowder")
check("project_cost itself falls once your own supply covers the demand",
      cost_with_beds < cost_no_beds * 0.6,
      "no beds=%.0f with beds=%.0f" % (cost_no_beds, cost_with_beds))

# --- refactor safety: resource_throttle()'s own quantity ceiling (unrelated
# to price, and pre-existing) is unchanged by factoring its material lookup
# out for material_price_factor() to share.
s = sim(civ="rome_100ad", capital=1e9)
s.active["gunpowder"] = {}
check("resource_throttle still throttles a material the market will not "
      "sell you at all",
      s.resource_throttle() < 1.0, s.resource_throttle())
s.nitre_bed_m2 = 2_000_000.0
check("...and stops once your own supply covers the need",
      s.resource_throttle() > 0.99, s.resource_throttle())

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
    s = sim(civ="rome_100ad", capital=1e9)
    f_none = s.material_price_factor(_mat)
    check("a material with NO curated entry anywhere (%s) starts neutral "
          "with no demand pinned on it" % _mat,
          abs(f_none - 1.0) < 1e-9, f_none)
    s._material_demand_cache = {_mat: 1000.0}
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
    s._material_demand_cache = {_mat: 1000.0}
    f_mined = s.material_price_factor(_mat)
    check("...and flooding the market this way relieves the SAME premium, "
          "for a material this file has never named, purely because supply "
          "and demand are now real numbers rather than a rule",
          f_mined < f_demand, "before=%.3f after=%.3f" % (f_demand, f_mined))

# --- the effect actually reaches project_cost(), the number the game
# charges, not only an internal factor nothing reads - the same standard
# COMMODITY_DYNAMISM.md held the original 9 commodities to.
s = sim(civ="rome_100ad", capital=1e9)
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
# accepting an arbitrary string.
s = sim(civ="rome_100ad", capital=1e9)
check("a material this file genuinely cannot price is still refused",
      s.mine_quote("not_a_real_material_xyz", 100.0) is None,
      s.mine_quote("not_a_real_material_xyz", 100.0))
check("...and mineable() agrees",
      s.mineable("aluminium") and s.mineable("aluminium_kg")
      and not s.mineable("not_a_real_material_xyz"),
      (s.mineable("aluminium"), s.mineable("aluminium_kg"),
       s.mineable("not_a_real_material_xyz")))

# --- A PLAYER MUST SEE IT: `money` surfaces a material price premium in
# aggregate, generalised the same way goods_market_summary already is for
# the goods side.
s = sim(civ="rome_100ad", capital=1e9)
s.active["gunpowder"] = {}
s.resource_throttle()
_mms = s.material_market_summary()
check("material_market_summary names a material trading above book price",
      bool(_mms) and "saltpetre" in _mms, _mms)
_money_mat = S._agent_dispatch(s, NODES, {"cmd": "money"})
check("...and `money` itself carries the same line",
      bool(_money_mat.get("materials_costing_you_a_premium")), _money_mat)

# --- the command surface itself accepts a generalised material name, not
# only the seven it used to: "buy mine aluminium_kg" must actually work.
_r_al, _, _ = proto([{"cmd": "buy", "what": "mine", "material": "aluminium_kg",
                      "n": 0.1}])
check("the command surface itself (not just the engine underneath it) "
      "accepts a material outside the original seven",
      _r_al[0].get("ok") is True, _r_al[0])
_r_bad, _, _ = proto([{"cmd": "buy", "what": "mine",
                       "material": "not_a_real_material_xyz", "n": 10}])
check("...but still refuses a genuinely unpriced name, with a hint rather "
      "than a bare closed list",
      _r_bad[0].get("ok") is False and "aluminium_kg" in _r_bad[0].get("error", ""),
      _r_bad[0])

# --- COMMODITY FRAMEWORK (data/world/COMMODITIES.md,
# sim/engine/commodities.py). Standalone from Sim, so these checks
# build a CommodityLedger directly off commodities.json and the tech tree's
# NODES rather than going through `sim()`/`proto()`. See the design doc for
# what each claim below is meant to prove and why.

LED = COMMOD.CommodityLedger(nodes=NODES)

check("commodities.json defines the nine commodities the design doc promises",
      set(LED.commodities) == {"iron", "copper", "copper_wire", "coal", "gold",
                                "wool", "cloth", "cotton", "coffee"},
      sorted(LED.commodities))

# --- gold: a water pump and chemical extraction should compound, not just
# pick the better of the two, because they are independent improvements
# stacked on the same mine (COMMODITIES.md section 3, "multiplier" entries).
mult_none = LED.best_multiplier("gold", built=[])
mult_pump = LED.best_multiplier("gold", built=["met_mine_pumping"])
mult_both = LED.best_multiplier("gold", built=["met_mine_pumping", "mt2_cyanidation"])
check("a mine with a water pump and chemical extraction multiplies gold "
      "output by roughly the brief's own '20x' figure",
      19.0 <= mult_both <= 23.0, mult_both)
check("the two gold technologies compound rather than the model just taking "
      "the better of the two",
      mult_both > mult_pump > mult_none == 1.0,
      "none=%.1f pump=%.1f both=%.1f" % (mult_none, mult_pump, mult_both))

# --- cloth: automated looms make cloth more available, which drops its
# price, which makes a hot air balloon (400 kg of linen_kg) cheaper to build.
CLOTH_DEMAND_T = 20000.0
price_hand = LED.price("cloth", CLOTH_DEMAND_T, LED.market_available("cloth", built=[]))
price_power = LED.price("cloth", CLOTH_DEMAND_T, LED.market_available("cloth", built=["tex_power_loom"]))
check("a power loom makes cloth more available (higher national output) "
      "than the baseline loom, at the same demand",
      LED.country_output("cloth", ["tex_power_loom"]) > LED.country_output("cloth", []))
check("...which drops the market price of cloth, not just a premium on top "
      "of a flat floor (the thing economy.py's material_price_factor cannot do)",
      price_power < price_hand * 0.5,
      "hand loom=%.2f power loom=%.2f den/kg" % (price_hand, price_power))
balloon_linen_kg = NODES["hot_air_balloon"]["mat"]["linen_kg"]
cost_hand = balloon_linen_kg * price_hand
cost_power = balloon_linen_kg * price_power
check("...which makes the real hot_air_balloon node's linen bill cheaper "
      "to buy once the power loom exists",
      cost_power < cost_hand, "hand=%.0f power=%.0f denarii" % (cost_hand, cost_power))

# --- copper wire: the real test. A modest order is fully met; an industrial
# order of 'kilometres of copper wire' is not, and the shortfall is
# attributed to copper (the ore), not to copper_wire (the smiths' craft),
# even though copper_wire also comes up short -- this is the distinction a
# flat resource_throttle() cannot draw at all.
modest = LED.propagate_demand("copper_wire", 5.0, built=[])
check("a modest order of copper wire (5 t/yr) is fully met by the ordinary "
      "market for copper",
      modest["met_fraction"] > 0.999, modest["met_fraction"])

big = LED.propagate_demand("copper_wire", 500.0, built=[])
check("an industrial order for copper wire is NOT fully met: there is not "
      "enough copper being mined to meet the demand",
      big["met_fraction"] < 0.95, big["met_fraction"])
check("the shortfall is attributed to copper specifically, not to copper_wire "
      "-- the smiths' wire-drawing bench is not the bottleneck",
      LED.bottlenecks(big) == ["copper"], LED.bottlenecks(big))
check("copper_wire itself is NOT flagged as its own bottleneck: it only "
      "inherited the shortage from its input",
      big["bottleneck"] is None, big["bottleneck"])
check("copper_wire's own wire-drawing capacity is not, in fact, the "
      "constraint (it is far above what was asked)",
      big["own_capacity_t"] > big["requested_t"], big["own_capacity_t"])

fixed = LED.propagate_demand("copper_wire", 500.0, built=[],
                             own_production={"copper": 100.0})
check("opening your own copper mine (Sim.open_mine's real-world analogue) "
      "relieves the same industrial order",
      fixed["met_fraction"] > 0.999, fixed["met_fraction"])

# --- monopoly: you know where coffee grows and how to process it, so you
# sell it at a margin nobody can undercut, bounded by what a buyer's next
# best alternative would cost them.
sole = LED.monopoly_price("coffee", marginal_cost=2.0, alternative_price=None)
competitive = LED.monopoly_price("coffee", marginal_cost=2.0, alternative_price=2.4)
check("a sole supplier with no rival prices well above what a competitive "
      "market (many sellers, price near marginal cost) would charge",
      sole > competitive * 2, "sole=%.1f competitive=%.1f" % (sole, competitive))
undercut = LED.monopoly_price("coffee", marginal_cost=2.0, alternative_price=9.0)
check("...but never above what a buyer's next-best alternative would cost "
      "them, once one exists",
      undercut == 9.0, undercut)

# --- price never runs away in either direction, however extreme the ratio
# (price_floor_factor / price_ceiling_factor, COMMODITIES.md section 2).
c = LED.commodities["iron"]
base = c["base_price_denarii_per_kg"]
lo = LED.price("iron", demand_t=0.0001, supply_t=1e9)
hi = LED.price("iron", demand_t=1e9, supply_t=0.0001)
check("a total glut never prices a commodity below its floor",
      abs(lo - base * c["price_floor_factor"]) < 1e-6, lo)
check("a total shortage never prices a commodity above its ceiling",
      abs(hi - base * c["price_ceiling_factor"]) < 1e-6, hi)

rng = random.Random(3)
noisy = [LED.price_with_noise("iron", 2000.0, 2475.0, rng) for _ in range(200)]
check("fluctuation stays within the same floor/ceiling bounds over many draws",
      all(base * c["price_floor_factor"] - 1e-9 <= p <= base * c["price_ceiling_factor"] + 1e-9
          for p in noisy),
      (min(noisy), max(noisy)))
check("fluctuation actually varies year to year rather than being decorative",
      len(set(round(p, 4) for p in noisy)) > 50, len(set(noisy)))

# --- 'how much you have' is a stock, tracked separately from the flows
# above (COMMODITIES.md section 8): a minimal Ledger proves the distinction
# is representable even though Sim itself has no inventory today.
ledger = COMMOD.Ledger()
ledger.add("copper", 500.0)
taken = ledger.remove("copper", 800.0)
check("a stock ledger cannot be overdrawn: taking more than is on hand "
      "returns only what was actually there",
      taken == 500.0 and ledger.on_hand("copper") == 0.0,
      (taken, ledger.on_hand("copper")))

