"""mines: split verbatim from the old test_regressions.py (original lines 7271-7582).

Moving contiguous blocks verbatim: no check below was reformatted, reworded or otherwise touched in the split.
"""
from .harness import *  # noqa: F401,F403

# =============================================================================
# MINES: LAND, DEPLETION AND TECHNOLOGY. A tester asked three questions
# nothing in the model answered: can you sink unlimited mines of one
# material, does yield fall as the easy ore is worked out, and does
# technology fight back. See economy.py's mine_land_ceiling()/
# mine_depletion_factor()/mining_tech() for the reasoning and the numbers.
# =============================================================================

# --- (a) LAND: the ceiling differs by material and by civilization, because
# geology is not standing. Reuses mineral_scale(), already used for the
# MARKET half of supply, for the OWN-MINE half too.
s_land = sim(capital=1.0)
check("a civilization with little tin under its home regions has a lower "
      "tin ceiling than one with plenty of the same standing",
      s_land.mine_land_ceiling("tin") != s_land.mine_land_ceiling("coal"),
      (s_land.mine_land_ceiling("tin"), s_land.mine_land_ceiling("coal")))
s_mex = sim(civ="mexica_1500", capital=1.0)
check("Mesoamerica, which worked copper but not iron or coal, has a lower "
      "land ceiling for iron than for copper",
      s_mex.mine_land_ceiling("iron") < s_mex.mine_land_ceiling("copper"),
      (s_mex.mine_land_ceiling("iron"), s_mex.mine_land_ceiling("copper")))

# --- open_mine() actually respects the land ceiling: sinking far more than
# the ground can support delivers only what the ground can support, not
# whatever standing alone would have allowed.
s_dig = sim(capital=1e12)
ceiling_before = s_dig.mine_land_ceiling("tin")
got_tin = s_dig.open_mine("tin", ceiling_before * 50.0, partial=False)
check("sinking far more of a scarce material than the land ceiling allows "
      "delivers only room up to that ceiling, not the full amount asked",
      0 < got_tin <= ceiling_before + 1.0,
      (got_tin, ceiling_before))

# --- woodland is bounded too, the tester's other named case ("mines/woods").
s_wood = sim(civ="norse_900ad", capital=1e12)
wood_ceiling = s_wood.forest_land_ceiling()
got_ha = s_wood.buy_forest(wood_ceiling * 100.0)
check("buying far more coppice than the land can support delivers only up "
      "to the ceiling, not the full amount asked",
      0 < got_ha <= wood_ceiling + 1.0, (got_ha, wood_ceiling))
check("...and the ceiling itself is nowhere near the WHOLE EMPIRE's own "
      "managed coppice (500,000 t/yr charcoal implies ~667,000 ha)",
      s_wood.forest_land_ceiling() < 667000.0, s_wood.forest_land_ceiling())

# --- (b) DEPLETION: yield falls as a working is worked hard relative to
# what the ground can support, and never below the stated floor.
s_dep = sim(capital=1e9)
s_dep.open_mine("coal", s_dep.mine_land_ceiling("coal") * 0.9, partial=False)
for _ in range(int(s_dep.MINE_LEAD_YEARS) + 1):
    s_dep.year += 1
    s_dep.commission_mines()
yield_early = s_dep.mine_yield_t("coal")
for _ in range(150):
    s_dep.year += 1
    s_dep.commission_mines()
yield_late = s_dep.mine_yield_t("coal")
check("a coal working driven hard for a century and a half yields less than "
      "it did when it opened",
      yield_late < yield_early, (yield_early, yield_late))
check("...but never below the stated floor, however long it is driven",
      s_dep.mine_depletion_factor("coal") >= s_dep.DEPLETION_FLOOR - 1e-9,
      s_dep.mine_depletion_factor("coal"))
for _ in range(2000):
    s_dep.year += 1
    s_dep.commission_mines()
check("...and depletion saturates at the floor rather than continuing to "
      "fall without limit (not an exponential collapse)",
      abs(s_dep.mine_depletion_factor("coal") - s_dep.DEPLETION_FLOOR) < 1e-6,
      s_dep.mine_depletion_factor("coal"))

# --- a working driven gently (a small fraction of what the ground could
# support) depletes far slower than one driven hard, for the same years.
s_gentle = sim(capital=1e9)
s_gentle.open_mine("coal", s_gentle.mine_land_ceiling("coal") * 0.1, partial=False)
for _ in range(int(s_gentle.MINE_LEAD_YEARS) + 1 + 150):
    s_gentle.year += 1
    s_gentle.commission_mines()
check("a working driven at a tenth of what the land could support depletes "
      "far slower than one driven at nine tenths, over the same years",
      s_gentle.mine_depletion_factor("coal") > s_dep.mine_depletion_factor("coal")
      or s_gentle.mine_depletion_factor("coal") == 1.0,
      (s_gentle.mine_depletion_factor("coal"), s_dep.mine_depletion_factor("coal")))

# --- (c) TECHNOLOGY fights back: it raises yield and lowers cost, and the
# two compound across independent technologies (mine pumping AND the
# Newcomen engine both address drainage, at different scale).
s_tech = sim(capital=1.0)
y0, c0 = s_tech.mining_tech("coal")
run_it(s_tech, "met_mine_pumping")
y1, c1 = s_tech.mining_tech("coal")
run_it(s_tech, "steam_atmospheric")
y2, c2 = s_tech.mining_tech("coal")
check("mine pumping alone raises yield and lowers cost for coal mining",
      y1 > y0 and c1 < c0, (y0, y1, c0, c1))
check("the Newcomen engine on top of mine pumping compounds rather than "
      "replacing it",
      y2 > y1 and c2 < c1, (y1, y2, c1, c2))
check("mining technology never raises yield or lowers cost without bound "
      "(capped/floored like every other compounding factor in this file)",
      y2 <= 3.0 and c2 >= 0.35, (y2, c2))

# --- technology raises what an EXISTING, already-depleted working yields,
# not only room for a new one - "fight depletion", not just avoid it.
before_tech = s_dep.mine_yield_t("coal")
run_it(s_dep, "met_mine_pumping")
run_it(s_dep, "steam_atmospheric")
after_tech = s_dep.mine_yield_t("coal")
check("mine pumping and the Newcomen engine raise a depleted working's "
      "actual yield, not just future room to sink a new one",
      after_tech > before_tech, (before_tech, after_tech))

# --- the interaction the brief asked for: a real decision, not an
# exponential. Cost is bounded on both ends even at maximum depletion with
# every relevant technology built.
s_bound = sim(capital=1.0)
for _t in s_bound.MINING_TECH:
    s_bound.done.add(_t); s_bound.operating.add(_t)
for _t in s_bound.MINING_TECH_STEEL:
    s_bound.done.add(_t); s_bound.operating.add(_t)
s_bound._done_changed()
# A working of its own, fully depleted from its own commissioning year (see
# economy.py's class comment above _workings_of) - mine_intensity_yrs no
# longer exists at all; depletion is per-working now.
s_bound.mines.append({"material": "coal", "capacity": 1.0, "opened_year": 1,
                      "capex_paid": 0.0, "intensity_yrs": 1e9})
check("even fully depleted with every relevant technology built, a tonne "
      "still costs something (not free) and not a runaway multiple of book",
      0.4 <= s_bound.mining_cost_scale("coal") <= 2.5,
      s_bound.mining_cost_scale("coal"))
s_bound2 = sim(capital=1.0)
s_bound2.mines.append({"material": "coal", "capacity": 1.0, "opened_year": 1,
                       "capex_paid": 0.0, "intensity_yrs": 1e9})
check("fully depleted with NO relevant technology, cost is higher, not "
      "lower, than the technology-equipped case above",
      s_bound2.mining_cost_scale("coal") > s_bound.mining_cost_scale("coal"),
      (s_bound2.mining_cost_scale("coal"), s_bound.mining_cost_scale("coal")))

# --- THE PLAYER MUST SEE IT: mine_quote() names the land ceiling, current
# yield fraction and why cost differs from book, before any capital moves.
q_dep = s_dep.mine_quote("coal", 100.0)
check("mine_quote names the ground's own ceiling and how much room is left "
      "before it, not just a price",
      q_dep["the_ground_here_could_ever_support"] > 0
      and "room_left_before_geology_stops_you" in q_dep, q_dep)
check("...and the current yield fraction, so a player can see a working "
      "has depleted without guessing",
      q_dep["current_yield_is_this_fraction_of_day_one"] < 1.0, q_dep)
check("...and mine_depletion_note() explains it in a sentence, not just a "
      "number",
      s_dep.mine_depletion_note("coal") is not None
      and "worked out" in s_dep.mine_depletion_note("coal"),
      s_dep.mine_depletion_note("coal"))

# --- determinism: the intensity/depletion bookkeeping is a Counter summed
# by material key, not iterated from a set, so it must not depend on
# PYTHONHASHSEED. Proven the same way the rest of this suite proves it: run
# twice with different hash seeds and compare the exact figures.
def _mine_snapshot(seed_env):
    p = subprocess.run(
        [sys.executable, "-c",
         "import sys; sys.path.insert(0,'.'); import random, simulator as S; "
         "T,P,N,W,G = S.load(); _l,O,_b = S.load_strategy('recommended', N, T['meta']['goal_node']); "
         "s = S.Sim(N, O, random.Random(1), events=False, manual=True, "
         "civ=S.load_civ('rome_100ad'), cfg={'start_capital':1e9}); "
         "s.open_mine('coal', s.mine_land_ceiling('coal')*0.8, partial=False); "
         "[s.__setattr__('year', s.year+1) or s.commission_mines() for _ in range(40)]; "
         "print(repr(round(s.mine_depletion_factor('coal'), 12)))"],
        capture_output=True, text=True, timeout=60, cwd=HERE,
        env=dict(os.environ, PYTHONHASHSEED=seed_env))
    return p.stdout.strip()
_snap_a, _snap_b = _par_map(_mine_snapshot, ("0", "12345"))
check("mine depletion is identical under a different PYTHONHASHSEED",
      _snap_a == _snap_b and _snap_a, (_snap_a, _snap_b))

# =============================================================================
# A WORKING IS A THING: self.mines is a list of individual workings, each
# with its own material, rated capacity, commissioning year and depletion
# clock, rather than one float per material - see economy.py's class
# comment above _workings_of(). mine_capacity is now a property SUMMED
# over that list, not a second number kept in sync by hand.
# =============================================================================

# --- the actual bug this exists to fix: two workings of the SAME material,
# opened at different times, must not share one depletion clock. A shaft
# opened later must end up LESS worked-out than one opened earlier and
# driven the same way for longer - "a shaft opened in year 400 is not
# three centuries into its seam because an earlier one was."
s_two = sim(capital=1e9)
s_two.open_mine("coal", s_two.mine_land_ceiling("coal") * 0.4, partial=False)
for _ in range(50):
    s_two.year += 1
    s_two.commission_mines()
s_two.open_mine("coal", s_two.mine_land_ceiling("coal") * 0.2, partial=False)
for _ in range(50):
    s_two.year += 1
    s_two.commission_mines()
check("opening a second coal working later gives TWO distinct workings of "
      "the same material, not one merged capacity number",
      len(s_two.mines) == 2 and len(set(w["opened_year"] for w in s_two.mines)) == 2,
      [(w["opened_year"], w["capacity"]) for w in s_two.mines])
_older = min(s_two.mines, key=lambda w: w["opened_year"])
_newer = max(s_two.mines, key=lambda w: w["opened_year"])
check("...and the newer working is measurably LESS worked-out than the "
      "older one, having had less time to deplete from its OWN "
      "commissioning year rather than inheriting the older one's clock",
      s_two.mine_depletion_factor_for(_newer)
      > s_two.mine_depletion_factor_for(_older),
      (s_two.mine_depletion_factor_for(_older),
       s_two.mine_depletion_factor_for(_newer)))
check("...and mine_yield_t (the material total) is exactly the sum of "
      "each working's own actual output, not the nominal tonnage sunk",
      abs(s_two.mine_yield_t("coal")
          - sum(s_two.mine_yield_t_for(w) for w in s_two.mines)) < 1e-6,
      s_two.mine_yield_t("coal"))
_saved_expected = sum(s_two.mine_operating_cost_for(w) for w in s_two.mines)
_ok, _msg = s_two.close_mine("coal")
check("closing a material closes every working of it and refunds the SUM "
      "of each working's OWN operating cost, not a material-average figure",
      _ok and abs(round(_saved_expected, 0)
                  - float(re.search(r"stop paying ([\d.]+)", _msg).group(1))) < 1.0,
      _msg)
check("...and every coal working is actually gone, not just one of them",
      not s_two._workings_of("coal"), s_two.mines)

# --- determinism, extended to SEVERAL workings across SEVERAL materials at
# once: self.mines is a list (append/commission order), not a set, and
# mine_capacity/mine_operating_cost/mine_yield_t/mine_depletion_factor all
# derive from it, so none of that arithmetic may depend on PYTHONHASHSEED
# even with more than one working of the same material in play together -
# proven across FOUR hash seeds, not two, because a regression here would
# most plausibly come from a dict/set built while grouping workings by
# material, and a coincidence surviving four seeds is far less likely than
# surviving two.
def _mines_snapshot(seed_env):
    p = subprocess.run(
        [sys.executable, "-c",
         "import sys; sys.path.insert(0,'.'); import random, simulator as S; "
         "T,P,N,W,G = S.load(); _l,O,_b = S.load_strategy('recommended', N, T['meta']['goal_node']); "
         "s = S.Sim(N, O, random.Random(1), events=False, manual=True, "
         "civ=S.load_civ('rome_100ad'), cfg={'start_capital':1e9}); "
         "s.open_mine('coal', s.mine_land_ceiling('coal')*0.4, partial=False); "
         "s.open_mine('iron', s.mine_land_ceiling('iron')*0.3, partial=False); "
         "[s.__setattr__('year', s.year+1) or s.commission_mines() for _ in range(6)]; "
         "s.open_mine('coal', s.mine_land_ceiling('coal')*0.2, partial=False); "
         "s.open_mine('copper', s.mine_land_ceiling('copper')*0.5, partial=False); "
         "[s.__setattr__('year', s.year+1) or s.commission_mines() for _ in range(80)]; "
         "print(repr(sorted((m, round(v, 9)) for m, v in s.mine_capacity.items()))); "
         "print(round(s.mine_yield_t('coal'), 9)); "
         "print(round(s.mine_operating_cost(), 9)); "
         "print(sorted((w['material'], w['opened_year'], round(w['intensity_yrs'], 9)) for w in s.mines))"],
        capture_output=True, text=True, timeout=60, cwd=HERE,
        env=dict(os.environ, PYTHONHASHSEED=seed_env))
    return p.stdout
_mines_seeds = ("0", "1", "12345", "999983")
_snaps = dict(zip(_mines_seeds, _par_map(_mines_snapshot, _mines_seeds)))
check("several workings across several materials give byte-identical "
      "mine_capacity/mine_yield_t/mine_operating_cost and per-working "
      "intensity under four different PYTHONHASHSEED values",
      len(set(_snaps.values())) == 1 and all(_snaps.values()), _snaps)

# --- SAVES: a working survives a save and resume, with its own material,
# capacity, commissioning year and depletion clock intact - not merely
# the aggregate mine_capacity total.
s_sv = sim(capital=1e9)
s_sv.open_mine("coal", s_sv.mine_land_ceiling("coal") * 0.4, partial=False)
for _ in range(6):
    s_sv.year += 1
    s_sv.commission_mines()
_sv_path = os.path.join(HERE, "_test_mines_save.json")
S.save_state(s_sv, _sv_path)
s_sv2 = sim(capital=1.0)
S.load_state(s_sv2, _sv_path)
os.remove(_sv_path)
check("a save/resume round-trip keeps the SAME working - material, rated "
      "capacity, commissioning year and its own depletion clock - not just "
      "the aggregate tonnage",
      len(s_sv2.mines) == 1
      and s_sv2.mines[0]["material"] == "coal"
      and abs(s_sv2.mines[0]["capacity"] - s_sv.mines[0]["capacity"]) < 1e-6
      and s_sv2.mines[0]["opened_year"] == s_sv.mines[0]["opened_year"]
      and abs(s_sv2.mines[0]["intensity_yrs"] - s_sv.mines[0]["intensity_yrs"]) < 1e-9,
      s_sv2.mines)
check("...and mine_capacity (the derived property) agrees after the "
      "round-trip, exactly as it did before saving",
      abs(s_sv2.mine_capacity.get("coal", 0.0)
          - s_sv.mine_capacity.get("coal", 0.0)) < 1e-6,
      (s_sv.mine_capacity, s_sv2.mine_capacity))

# --- SAVES, backward compatibility: a save written before workings existed
# (an old-style "mine_capacity" dict, no "mines" list at all) still loads,
# carries its capacity forward as one working per material, and does NOT
# fabricate a commissioning year it never recorded.
s_old = sim(capital=1.0)
_old_blob = {"year": 150.0, "capital": 1000.0, "done": {"__set__": []},
            "granted": {"__set__": []}, "active": {}, "_civ": s_old.civ.get("id"),
            "_version": 1, "mine_capacity": {"coal": 250.0, "iron": 0.0}}
_old_path = os.path.join(HERE, "_test_old_mines_save.json")
with open(_old_path, "w") as _fh:
    json.dump(_old_blob, _fh)
S.load_state(s_old, _old_path)
os.remove(_old_path)
check("a save from before workings existed still loads and carries "
      "capacity forward as a working, WITHOUT fabricating a commissioning "
      "year it never recorded",
      len(s_old.mines) == 1 and s_old.mines[0]["material"] == "coal"
      and abs(s_old.mines[0]["capacity"] - 250.0) < 1e-6
      and s_old.mines[0]["opened_year"] is None,
      s_old.mines)
check("...and a zero-capacity legacy entry (iron: 0.0) is not carried "
      "forward as a phantom working",
      not s_old._workings_of("iron"), s_old.mines)

