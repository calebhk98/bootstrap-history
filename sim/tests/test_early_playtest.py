"""early_playtest: split verbatim from the old test_regressions.py (original lines 202-919).

Moving contiguous blocks verbatim: no check below was reformatted, reworded or otherwise touched in the split.
"""
from .harness import *  # noqa: F401,F403

# --- Rome BREAK: negative quantity minted money while reporting failure
r, _, _ = proto([{"cmd": "state"},
                 {"cmd": "buy", "what": "forest", "n": -5},
                 {"cmd": "state"}])
check("negative buy quantity changes nothing",
      r[0]["capital"] == r[-1]["capital"] and r[-1]["forest_ha"] == 0,
      "capital %s -> %s" % (r[0]["capital"], r[-1]["capital"]))

# --- Rome BREAK: a non-string id killed the process
r, _, rc = proto([{"cmd": "why", "id": {"a": 1}}, {"cmd": "state"}])
check("non-string id does not kill the session", rc == 0 and len(r) == 2)

# --- Norse BREAK: bare non-object JSON killed the process one line later
_, raw, rc = proto([])  # placeholder to keep the helper simple
p = subprocess.run([sys.executable, os.path.join(HERE, "simulator.py"), "agent"],
                   input='null\n42\n"x"\n[1,2]\n{"cmd":"state"}\n',
                   capture_output=True, text=True, timeout=300, cwd=ROOT)
check("bare null/number/string/list does not kill the session",
      p.returncode == 0 and p.stdout.count("\n") >= 5)

# --- Norse BREAK: `why` crashed on nodes missing the v1 scalars
missing = [x["id"] for x in TREE["nodes"]
           if any(f not in x for f in ("sus", "gov", "cat", "pre"))]
check("no node is missing a required field", not missing, str(missing[:4]))

# --- Rome WEIRD: buy+manumit minted labour from money
s = sim(capital=200000.0)
a0 = s.artisans
s.buy_slaves(10); s.manumit(10)
check("manumission does not double-count the same person",
      s.artisans - a0 < 5.0, "gained %.1f artisans from 10 people" % (s.artisans - a0))

# --- Han WEIRD / Norse BREAK: slicing dodged the volume surcharge
def spend(slices, per):
    t = sim(capital=1e9)
    # ROOM TO PUT THEM. Buying now respects the same feed/house/oversee cap
    # `hire` always did, so a test about PRICING has to make room first or it
    # is really testing the cap.
    run_it(t, "workshop_first", "freedman_staff")
    c0 = t.capital
    for _ in range(slices):
        t.buy_slaves(per)
    return c0 - t.capital
one, four, twelve = spend(1, 12), spend(4, 3), spend(12, 1)
check("buying in slices costs the same as buying at once",
      max(one, four, twelve) - min(one, four, twelve) < 1.0,
      "%.0f / %.0f / %.0f" % (one, four, twelve))

# --- Rome WEIRD: manumitting untrained people skipped the training lag
s = sim(capital=200000.0)
a0 = s.artisans
s.buy_slaves(10); s.manumit(10)
check("freeing untrained people does not skip the training lag",
      s.artisans - a0 < 0.01, "instant gain %.2f" % (s.artisans - a0))

# --- Han BREAK: why quoted a civilization-blind cost
# Each civ gets its own fresh subprocess (proto() never takes a session
# file), so the two calls are independent and safe to overlap under --jobs.
_q_civs = ("rome_100ad", "han_china_100ad")
_q_results = _par_map(lambda civ: proto([{"cmd": "why", "id": "blast_furnace"}],
                                        civ=civ)[0], _q_civs)
q = dict(zip(_q_civs, (r[0]["cost"]["total"] for r in _q_results)))
check("why quotes a civilization-specific cost",
      q["rome_100ad"] != q["han_china_100ad"], str(q))

# --- Han BREAK: starting techs that do not exist were silently dropped
bad = []
for f in sorted(os.listdir(S.CIVDIR)):
    if not f.endswith(".json") or f.startswith("_"):
        continue
    c = json.load(open(os.path.join(S.CIVDIR, f)))
    ids = {x["id"] for x in TREE["nodes"]}
    bad += [t for t in (c.get("starting_techs") or []) if t not in ids]
check("every civilization's starting techs exist", not bad, str(bad))

# --- Han BREAK: one society was granted another's institutions
s = sim(civ="han_china_100ad", manual=False)
for _ in range(2):
    s.step()
foreign = [k for k in s.granted if "_roman" in k or "annona" in k]
check("a society is not granted another society's institutions",
      not foreign, str(foreign[:4]))

# --- Norse WIN: handicap_remedies was never wired
s = sim(civ="norse_900ad")
before = s.civ_cost_factor("blast_furnace")
s.done.add("collegium_licensed")
after = s.civ_cost_factor("blast_furnace")
check("building a remedy lifts the handicap", after < before,
      "%.2f -> %.2f" % (before, after))

# --- Norse WIN: _TECH_EFFECTS was never wired
s = sim()
f0 = s.w["w_magic_fear"]
s.apply_tech_effects("scientific_method")
check("a technology changes the society that built it",
      s.w["w_magic_fear"] < f0, "%.2f -> %.2f" % (f0, s.w["w_magic_fear"]))

# --- the user: an organised army is a more capable state, not only a safer
# founder - general_staff is the same state_capacity field railway and
# semaphore_telegraph already use for "the state gets more capable of acting"
s = sim()
sc0 = s.civ["state_capacity"]
s.apply_tech_effects("mil_general_staff")
check("standing a general staff up raises what the state can organise and "
      "compel, the same as railway or the telegraph does",
      s.civ["state_capacity"] > sc0, "%.3f -> %.3f" % (sc0, s.civ["state_capacity"]))

# --- Norse WEIRD: abandonment shed a persona and softlocked the run
s = sim(civ="norse_900ad", capital=1000000.0)
s.start_project("identity_cover")
for _ in range(4):
    s.step()
s.buy_slaves(150)
for _ in range(40):
    s.step()
check("bankruptcy never abandons a persona or institution",
      "identity_cover" in s.done, "identity_cover was shed")

# --- Norse BREAK: topping up a mine reset the whole pool's clock
s = sim(capital=5e6)
for _ in range(8):
    s.open_mine("coal", 200)
    s.step()
check("topping up a mine still delivers capacity",
      s.mine_capacity.get("coal", 0) > 0, str(s.mine_capacity))

# --- Norse BREAK: knowledge_risk advertised risk a civ could not face
r, _, _ = proto([{"cmd": "risk"}], civ="norse_900ad")
kr = r[0]["knowledge_risk"]
check("no loss risk is reported where nothing sacks",
      kr["expected_technologies_lost_per_sacking"] == 0.0, str(kr)[:80])

# --- naive BREAK: read-only commands before the first step
r, _, rc = proto([{"cmd": "available"}, {"cmd": "state"}, {"cmd": "help"}])
check("state/available/help work before the first step",
      rc == 0 and all(x.get("ok") for x in r), str(r[:1])[:90])

# --- naive C/A/BREAK: save then restart must not brick the game
import tempfile
sp = os.path.join(tempfile.mkdtemp(), "sess.json")
proto([{"cmd": "state"}], )  # warm
subprocess.run([sys.executable, os.path.join(HERE, "simulator.py"), "agent",
                "--session", sp], input='{"cmd":"state"}\n',
               capture_output=True, text=True, timeout=300, cwd=ROOT)
p2 = subprocess.run([sys.executable, os.path.join(HERE, "simulator.py"), "agent",
                     "--session", sp], input='{"cmd":"state"}\n',
                    capture_output=True, text=True, timeout=300, cwd=ROOT)
check("a saved game reloads without bricking",
      '"ok": true' in p2.stdout, p2.stdout[:90])

# --- naive BREAK: no advanced physics on the first morning
early = {"sc2_physics_nuclear_fission", "sc2_physics_wave_mechanics",
         "el2_sonar_acoustic_detection_ranging", "el2_photomultiplier_single_photon"}
# all:true, because `available` is a digest by default now
r, _, _ = proto([{"cmd": "available", "all": True}])
offered = {a["id"] for a in r[0]["available"]} & early
check("no advanced physics is startable in year one", not offered, str(offered))

# --- naive A: debasement must not make everything cheaper
s = sim()
base = s.cost_money_factor()
s.money_real = 0.005
check("a debased currency does not collapse prices",
      abs(s.cost_money_factor() - base) < 1e-9,
      "%.4f -> %.4f" % (base, s.cost_money_factor()))

# --- reviewer: debt must be bounded and ruin must be recoverable.
#     Two hundred simulated years; the single most expensive check here.
def _ruin_run():
    s = sim(manual=False, capital=1e6)
    s.buy_slaves(400)
    worst = 0.0
    for _ in range(200):
        s.step()
        worst = min(worst, s.capital)
    return s, worst


_RUIN = {}


def _ruin():
    if not _RUIN:
        _RUIN["s"], _RUIN["worst"] = _ruin_run()
    return _RUIN["s"], _RUIN["worst"]


slow_check("debt stays inside a credit limit",
           lambda: (_ruin()[1] > -200000, "worst capital %.0f" % _ruin()[1]))
slow_check("a ruined founder rebuilds rather than freezing",
           lambda: (len(_ruin()[0].done - _ruin()[0].granted) > 200,
                    "earned %d in 200 years"
                    % len(_ruin()[0].done - _ruin()[0].granted)))
slow_check("ruin never deletes a step the goal needs",
           lambda: ("identity_cover" in _ruin()[0].done, ""))

# --- naive B: the game must not buy people on the player's behalf
s = sim(capital=200000.0, manual=True)
for _ in range(40):
    s.step()
check("manual play never buys people for you", s.slaves == 0 and s.freedmen == 0,
      "slaves %d freedmen %d" % (s.slaves, s.freedmen))

# --- naive WEIRD: nothing should repay its whole cost in weeks
pumps = [k for k, n in NODES.items()
         if float(n.get("rev") or 0) > 0 and n["_total_cost"] > 0
         and n["_total_cost"] / float(n["rev"]) < 0.5]
check("no node repays its entire cost in under six months", not pumps,
      "%d pumps, e.g. %s" % (len(pumps), pumps[:3]))

# --- naive WEIRD 7 / Han BREAK 5: a project must actually be PAID for
s = sim(capital=400.0, manual=True)
ok, why = s.start_project("identity_cover")         # 1,580 den against 400
for _ in range(6):
    s.step()
paid = s.active.get("identity_cover", {}).get("spent", 0.0)
check("an unfunded project never completes",
      ok and "identity_cover" not in s.done,
      "started=%s (%s) done=%s paid=%.0f" % (ok, why, "identity_cover" in s.done, paid))

# --- the user: you arrive alone
s = sim()
check("you arrive with no employees and no slaves",
      not s.employees and s.slaves == 0 and s.freedmen == 0 and s.artisans == 0.0,
      "employees %r artisans %.1f" % (s.employees, s.artisans))

# --- the user: a skilled smith is not a skilled writer
s = sim()
ok_hire, err = s.hire("engineer", 1)
check("a trade this society does not have cannot be hired",
      not ok_hire and "no engineer" in (err or "").lower(),
      "hire engineer -> %s / %s" % (ok_hire, err))
s.capital = 20000.0
ok_train, _ = s.train("machinist", 2)
check("you can teach a trade into existence",
      ok_train and "machinist" in s.trades_created and not s.trade_available("chemist"),
      "trained %s created %r" % (ok_train, sorted(s.trades_created)))

# --- the user: hire a job, not a person
s = sim(capital=5000.0)
before = s.capital
ok_job, _ = s.commission("smith", 200)
check("you can buy a job without employing anybody",
      ok_job and not s.employees and s.capital < before,
      "ok %s employees %r" % (ok_job, s.employees))

# --- the user: everything automatic must be switchable
s = sim(manual=False)
check("every automatic behaviour has a switch",
      set(s.policy) >= {"auto_hire", "auto_buy_people", "auto_manumit", "auto_train",
                        "auto_mine", "auto_forest", "auto_mothball", "auto_shed",
                        "auto_bribe"},
      sorted(s.policy))

# --- naive B/C: there must be a way to shed the upkeep of a finished work
s = sim(capital=200000.0)
s.hire("artisan", 2)
s.done.add("fin_restaurant")
s._done_changed()
# OPEN IT FIRST. Upkeep follows what you RUN, not what you know, so a node
# sitting in `done` has no running cost to stop until you open its doors.
_ok_open, _why_open = s.open_venture("fin_restaurant")
up_before = s.upkeep()
ok_mb, _ = s.mothball_work("fin_restaurant")
check("a finished work can be shut down to stop its upkeep",
      _ok_open and ok_mb and up_before > 0 and s.upkeep() < up_before,
      "open %s (%s), upkeep %.0f -> %.0f"
      % (_ok_open, _why_open, up_before, s.upkeep()))
check("shutting a concern down does not make you forget how it worked",
      "fin_restaurant" in s.done and "fin_restaurant" not in s.operating,
      "done %s operating %s" % ("fin_restaurant" in s.done,
                                "fin_restaurant" in s.operating))

# --- the user: hazards must be answerable with technology
s = sim()
bare, _ = s.hazard_relief("staff_loss")
s.done.add("sanitation_antisepsis")
s.done.add("germ_theory")
better, why = s.hazard_relief("staff_loss")
check("medicine blunts a plague", bare == 1.0 and better < 0.6 and why,
      "%.2f -> %.2f %s" % (bare, better, why))
s2 = sim()
s2.mines.append({"material": "gold", "capacity": 1.0, "opened_year": s2.year,
                 "capex_paid": 0.0, "intensity_yrs": 0.0})
gold, _ = s2.hazard_relief("real_erosion")
check("your own gold mine blunts a debasement", gold < 0.5, "%.2f" % gold)

# --- the user: "if I woke up in Rome and made cannons, that should massively
# affect a lot of things, and shouldn't that make the country bigger / win
# more wars?" Measured before this round of changes: a founder who built
# every one of the tree's 111+ military, weapon and fortification nodes
# differed from one who built none in exactly one respect anywhere in the
# engine - weapon_democratising raising suspicion (see alarm_of). Nothing
# protected the founder, nothing changed what a war cost the state, nothing
# recovered faster. These checks pin the fix and the boundary around it: the
# branch now matters, and does not matter so much that it swallows the tree.
_MIL_NODES = sorted(k for k in NODES if "military" in (NODES[k].get("traits") or ()))
check("the tree still has a real military branch to test against",
      len(_MIL_NODES) >= 100, len(_MIL_NODES))

s = sim()
_FOUNDER_MIL_NODES = [k for k in _MIL_NODES if k not in s.granted]
lev0 = s.military_leverage()
s.done.add(_FOUNDER_MIL_NODES[0])
lev1 = s.military_leverage()
for k in _FOUNDER_MIL_NODES[:25]:
    s.done.add(k)
lev25 = s.military_leverage()
for k in _MIL_NODES:
    s.done.add(k)
levall = s.military_leverage()
check("military strength is zero for a founder who has built none of the "
      "branch, rises with the first node, and saturates well short of the "
      "whole branch (so the branch cannot be a strategy unto itself)",
      lev0 == 0.0 and 0.0 < lev1 < lev25 == 1.0 and levall == 1.0,
      (lev0, lev1, lev25, levall))

s_bare = sim()
s_bare.update_protection()
s_mil_nopatron = sim()
for k in _MIL_NODES:
    s_mil_nopatron.done.add(k)
s_mil_nopatron.update_protection()
check("a cannon foundry with nobody to sell to protects the founder not at "
      "all - the leverage is with a patron, not the hardware itself",
      abs(s_mil_nopatron.protection - s_bare.protection) < 1e-9,
      (s_bare.protection, s_mil_nopatron.protection))

s_patron = sim()
run_it(s_patron, "patron_imperial")
s_patron.update_protection()
s_patron_mil = sim()
run_it(s_patron_mil, "patron_imperial")
for k in _MIL_NODES:
    s_patron_mil.done.add(k)
s_patron_mil.update_protection()
check("an armourer with an imperial patron to arm is protected more than "
      "the same patron without the armoury, and the gain is a real fraction "
      "of a percent, not a rounding error or a dominant strategy on its own",
      0.02 < s_patron_mil.protection - s_patron.protection < 0.12,
      (s_patron.protection, s_patron_mil.protection))

s_out_bare = sim()
out_bare, _ = s_out_bare.hazard_relief("output_factor")
s_out_mil = sim()
for k in _MIL_NODES:
    s_out_mil.done.add(k)
out_mil, out_why = s_out_mil.hazard_relief("output_factor")
check("a war costs an armed empire's trade less than an unarmed one's - "
      "every output_factor hazard in these civilization files is a war or "
      "its administrative aftermath, and this is the branch's answer to it",
      out_mil < out_bare and any("military strength" in w for w in out_why),
      (out_bare, out_mil, out_why))

staff_bare, _ = s_out_bare.hazard_relief("staff_loss")
staff_mil, _ = s_out_mil.hazard_relief("staff_loss")
check("military technology gives no relief against staff loss - most "
      "staff_loss hazards in these civilizations are disease and famine, "
      "not war, and a founder with cannon should not cure the Antonine "
      "plague",
      staff_bare == staff_mil, (staff_bare, staff_mil))

s_rec_bare = sim(); s_rec_bare.output_factor = 0.7
s_rec_mil = sim()
for k in _MIL_NODES:
    s_rec_mil.done.add(k)
s_rec_mil.output_factor = 0.7
s_rec_bare.step()
s_rec_mil.step()
check("an armed empire's trade recovers from a war faster than an unarmed "
      "one's, year over year, and the war still happened either way - this "
      "is recovery speed, not a rewrite of the event",
      s_rec_mil.output_factor > s_rec_bare.output_factor > 0.7,
      (s_rec_bare.output_factor, s_rec_mil.output_factor))

# --- the Mexica case: the sharpest test named in the brief. Firearms and
# steel should plausibly blunt a sacking; they must not un-happen the
# Spanish arrival, whose dates are untouched, or cure the same contact
# epidemics that hit staff_loss, which nothing military should touch.
s_mex = sim(civ="mexica_1500")
_spanish = next(h for h in s_mex.civ["hazards"] if "Spanish" in h.get("name", ""))
check("the Spanish invasion still arrives on its historical date, unmoved "
      "by anything this change does",
      _spanish["years"] == [1519, 1521], _spanish["years"])
check("the Spanish invasion hazard carries no staff_loss of its own - the "
      "contact epidemics are a separate, later hazard entry, so military "
      "technology (which never touches staff_loss) cannot appear to cure "
      "them by touching this one",
      "staff_loss" not in _spanish, sorted(_spanish))
_mex_bare = sim(civ="mexica_1500")
_sack_bare, _ = _mex_bare.hazard_relief("sack_chance")
_mex_mil = sim(civ="mexica_1500")
for k in _MIL_NODES:
    if k in NODES:
        _mex_mil.done.add(k)
_sack_mil, _sack_why = _mex_mil.hazard_relief("sack_chance")
check("a Mexica founder who had built firearms and fortification before "
      "the Spanish arrived would face a real, non-zero chance of a "
      "sacking still - the counterfactual is blunted, never zeroed",
      0.0 < _sack_mil < _sack_bare, (_sack_bare, _sack_mil, _sack_why[:3]))

# --- the user: downstream_count is a fog spoiler
p = subprocess.run([sys.executable, os.path.join(HERE, "simulator.py"), "agent",
                    "--civ", "rome_100ad", "--fog"],
                   input='{"cmd":"why","id":"identity_cover"}\n',
                   capture_output=True, text=True, timeout=120, cwd=ROOT)
reply = json.loads([l for l in p.stdout.splitlines() if l.strip()][0])
check("fog hides the exact downstream count",
      reply.get("downstream_count") is None and reply.get("how_much_rests_on_this"),
      "downstream %r band %r" % (reply.get("downstream_count"),
                                 reply.get("how_much_rests_on_this")))

# --- the user: debt bondage is worked off where a society had it, and Rome did not
check("debt bondage follows the society, and is a term of years",
      S.load_civ("rome_100ad").get("debt_bondage") is False
      and S.load_civ("han_china_100ad").get("debt_bondage") is True
      and S.load_civ("han_china_100ad").get("bondage_years", 0) > 0,
      "rome %r han %r" % (S.load_civ("rome_100ad").get("debt_bondage"),
                          S.load_civ("han_china_100ad").get("debt_bondage")))

# --- the user: a reply nobody can read is a reply nobody reads
r, _, _ = proto([{"cmd": "state"}, {"cmd": "available"}, {"cmd": "help"},
                 {"cmd": "labour"}])
sizes = {c: len(json.dumps(x)) for c, x in
         zip(("state", "available", "help", "labour"), r)}
check("no ordinary reply is a wall of text",
      all(v < 6000 for v in sizes.values()), str(sizes))

# a late-game available must not blow up either: it was 165KB at year 250.
#
# THIS USED TO STEP A REAL SIM 150 YEARS to get the tree open enough to be
# worth measuring - 44s of wall time to populate s.done, for a state that
# then had only 12 things concurrently startable. But _agent_available is a
# pure function of s.done/s.operating/fog (via can_start/start_reason,
# neither of which reads anything about how a node got marked done) - it
# does not care whether `done` was populated by 150 years of the optimizer's
# own choices or written directly. Constructing it directly is not a weaker
# test of the same thing, it is a HARDER one: a natural 150-year run leaves
# the frontier narrow (12 startable) because the optimizer greedily closes
# off branches as it goes, while cutting an arbitrary slice of ORDER opens
# unrelated branches all over the tree at once - 251 things startable at the
# 30% cut below, 21x what the real run ever produced - which is exactly the
# case a "stays a summary, never a dump" claim needs to survive. Two
# fractions, not one: how many nodes cross from locked to startable is not
# monotonic in how much of the tree is done, so a single cut point could get
# lucky and land somewhere unusually tame.
def _tree_opens_up():
    out = []
    for frac in (0.30, 0.55):
        s = sim(capital=1e6, manual=False)
        s.fog = True
        cut = int(len(ORDER) * frac)
        s.done.update(ORDER[:cut])
        s._done_changed()
        avail = S._agent_available(s, NODES)
        digest = len(json.dumps(avail))
        out.append((digest < 12000,
                    "%d bytes at %d%% of tree done with %d things startable"
                    % (digest, int(frac * 100), avail["count"])))
    return all(ok for ok, _ in out), "; ".join(d for _, d in out)


slow_check("available stays a summary as the tree opens up", _tree_opens_up)

# --- the menu: a bare invocation must open it, and every civ must be playable
p = subprocess.run([sys.executable, os.path.join(HERE, "simulator.py")],
                   input="q\n", capture_output=True, text=True, timeout=120, cwd=ROOT)
check("a bare invocation opens the menu rather than a usage error",
      p.returncode == 0 and "ONE PERSON" in p.stdout, p.stdout[:80] + p.stderr[:80])
check("the bare menu is a main menu (New game / Load / Options), not "
      "straight into the civilisation picker",
      all(w in p.stdout for w in ("New game", "Load a saved game", "Options")),
      p.stdout[:1500])

# The civilisation list itself lives one door in, behind "New game" - "1"
# opens it, "b" backs out again without starting anything (so this writes no
# save file at all) and "q" leaves the main menu.
p2 = subprocess.run([sys.executable, os.path.join(HERE, "simulator.py")],
                    input="1\nb\nq\n", capture_output=True, text=True, timeout=120,
                    cwd=ROOT)
check("the menu offers every civilisation with its lore",
      all(w in p2.stdout for w in ("Later Han", "Trajan", "Viking", "Edward I", "Mexica")),
      "missing one of the five")

# `play` was Rome-only and its loop ended at 100+horizon, so any civ that does
# not start in year 100 ended before the player could type anything.
# Each is its own fresh, unrelated `play` session (no --session file), so the
# two civs are dispatched together and checked in order under --jobs.
_civ_year_pairs = (("norse_900ad", "900 AD"), ("mexica_1500", "1500 AD"))


def _play_manual_civ(pair):
    civ, first_year = pair
    return subprocess.run([sys.executable, os.path.join(HERE, "simulator.py"), "play",
                           "--manual", "--civ", civ],
                          input="n\nq\n", capture_output=True, text=True, timeout=120, cwd=ROOT)


for (civ, first_year), p in zip(_civ_year_pairs,
                                _par_map(_play_manual_civ, _civ_year_pairs)):
    check("play runs a civilisation that does not start in 100 AD (%s)" % civ,
          first_year in p.stdout and "Ended %s" % first_year not in p.stdout,
          p.stdout[-120:])

civ_files = [f for f in os.listdir(os.path.join(ROOT, "data", "civilizations"))
             if f.endswith(".json") and not f.startswith("_")]
missing_lore = []
for f in civ_files:
    d = json.load(open(os.path.join(ROOT, "data", "civilizations", f)))
    op = d.get("opening") or {}
    if not all(op.get(k) for k in ("arrival", "what_you_can_see",
                                   "what_is_missing", "what_is_coming")):
        missing_lore.append(d.get("id", f))
check("every civilisation has its opening written", not missing_lore, str(missing_lore))

# --- round two, section M: the robustness batch
r, _, _ = proto([{"cmd": "save", "file": "/etc/should_not_happen.json"},
                 {"cmd": "save", "file": "../../escape.json"},
                 {"cmd": "save", "file": "notasave.txt"}])
check("a save cannot be written outside the game directory",
      all(not x.get("ok") for x in r), str([x.get("ok") for x in r]))
check("/etc was not written to", not os.path.exists("/etc/should_not_happen.json"))

r, _, _ = proto([{"cmd": "step", "years": 100000}, {"cmd": "step", "years": True}])
check("step refuses more years than the game contains", not r[0].get("ok"),
      str(r[0])[:80])
check("step refuses true as a number of years", not r[1].get("ok"), str(r[1])[:80])

r, _, _ = proto([{"cmd": "hire", "trade": "smith", "n": "banana"},
                 {"cmd": "bribe", "amount": "lots"},
                 {"cmd": "state"}])
check("a quantity that is not a number is refused, not defaulted",
      not r[0].get("ok") and not r[1].get("ok") and not r[2].get("employees"),
      str(r[0].get("error"))[:70])

r, _, _ = proto([{"cmd": "quote", "what": "mine", "material": "gold", "n": 1}])
check("a mine can be priced before it is bought",
      r[0].get("ok") and r[0].get("to_sink_it", 0) > 0
      and r[0].get("every_year_it_stands", 0) > 0, str(r[0])[:90])

r, _, _ = proto([{"cmd": "buy", "what": "mine", "material": "coal", "n": 20},
                 {"cmd": "step", "years": 5}, {"cmd": "state"},
                 {"cmd": "close", "material": "coal"}, {"cmd": "state"}])
check("a mine can be closed, and stops costing",
      r[2].get("mine_operating_cost", 0) > 0 and r[4].get("mine_operating_cost") == 0,
      "before %s after %s" % (r[2].get("mine_operating_cost"),
                              r[4].get("mine_operating_cost")))

# --- Mexica WEIRD: the unknown-command message advertised ten commands while
#     the game had twenty-four, so a player who mistyped was handed a list that
#     silently omitted labour, hire, train, money, risk, policy and the rest.
r, _, _ = proto([{"cmd": "definitely_not_a_command"}], civ="mexica_1500")
_advertised = r[0].get("error", "")
_real = [c for c in S.KNOWN_COMMANDS]
check("the unknown-command message advertises every command there is",
      all(c in _advertised for c in _real),
      "missing: %s" % [c for c in _real if c not in _advertised])

# and every command it advertises must actually answer. FIVE SECONDS, because
# it builds a fresh Mexica game per command and there are now dozens; the
# cheap half above, that the message names them all, stays on the fast path.
def _every_advertised_command_answers():
    dead = []
    for c in _real:
        if c in ("quit", "save", "load"):
            continue                  # need arguments or end the session
        rr, _, _ = proto([{"cmd": c}], civ="mexica_1500")
        if rr and "unknown cmd" in str(rr[0].get("error", "")):
            dead.append(c)
    return not dead, str(dead)

slow_check("every advertised command is one the game answers to",
           _every_advertised_command_answers)

r, _, _ = proto([{"cmd": "why"}], civ="mexica_1500")
check("a missing id asks for one rather than naming a Python type",
      "NoneType" not in r[0].get("error", "") and "available" in r[0].get("error", ""),
      r[0].get("error", "")[:90])

# --- reproducibility: the same seed must give the same answer, and it must not
#     depend on PYTHONHASHSEED.
#
# This used to shell out to `run --mc 3 --seed 42` twice and compare stdout,
# which is six complete 500-year Monte-Carlo runs and took longer than the
# other seventy-odd checks put together - the whole suite stopped finishing
# inside fifteen minutes and started getting killed. A check nobody can afford
# to run is a check that rots, which is the exact thing this file exists to
# prevent. It also could not pass at all while a second process was editing
# the tree, because then it was comparing two different programs.
#
# Same property, measured directly: run the model in-process over a short
# horizon and compare the state, under two different hash seeds. Set
# explicitly, because Python randomises string hashing per process and three
# separate bugs in this project have come from iterating a set of node ids.
def _det_fingerprint():
    src = """
import sys, random
sys.path.insert(0, %r)
import simulator as S
TREE, PRICES, NODES, WAGES, GOODS = S.load()
GOAL = TREE["meta"]["goal_node"]
_L, ORDER, _B = S.load_strategy("recommended", NODES, GOAL)
out = []
for seed in (42, 43):
    s = S.Sim(NODES, ORDER, random.Random(seed), events=True, manual=False,
              civ=S.load_civ("rome_100ad"))
    s.goal, s.done_year = GOAL, {}
    for _ in range(60):
        s.step()
    out.append("%%d|%%.9f|%%.9f|%%.6f" %% (len(s.done), s.capital, s.revenue(),
                                         s.eminence))
print(";".join(out))
""" % HERE
    seen = set()
    for hashseed in ("0", "12345"):
        env = dict(os.environ, PYTHONHASHSEED=hashseed)
        r = subprocess.run([sys.executable, "-c", src], capture_output=True,
                           text=True, timeout=600, cwd=ROOT, env=env)
        seen.add(r.stdout.strip() or ("ERROR: " + r.stderr[-200:]))
    return seen


def _determinism():
    seen = _det_fingerprint()
    return (len(seen) == 1 and not any(x.startswith("ERROR") for x in seen),
            " || ".join(sorted(seen))[:160])


slow_check("the same seed gives the same result, whatever PYTHONHASHSEED is",
           _determinism)

# --- round 2 A: the setting is Rome wearing a hat -- notes must generalise
_ROME_TEMPLATES = ("ROME ALREADY HAS THIS", "ROME HAS THIS", "ROME POSSIBLY HAS THIS")
bare_rome_notes = [k for k, n in NODES.items()
                    if any(t in (n.get("note") or "") for t in _ROME_TEMPLATES)]
check("no node note bluntly claims 'Rome [already] has this'",
      not bare_rome_notes, str(bare_rome_notes[:5]))

bare_rome_prices = [k for k, v in PRICES["wage_rates_denarii_per_hour"].items()
                     if not k.startswith("_") and isinstance(v, dict)
                     and ("Rome has" in (v.get("note") or "")
                          or "Rome already has" in (v.get("note") or ""))]
check("no wage-rate note bluntly claims 'Rome has these'",
      not bare_rome_prices, str(bare_rome_prices))

check("the cover identity is not named after one civilization's version",
      "Alexandrian" not in NODES["identity_cover"]["name"],
      NODES["identity_cover"]["name"])

# --- round 2 A: institutions Rome already has must cost real work for
# anyone else, and still be free for Rome (via starting_techs, not via a
# zero price tag every civilization can exploit)
_ROMAN_INSTITUTIONS = ["civ_arch_roman", "fin_annona", "fin_argentarii",
                       "fin_collegium", "fin_societas", "hom_cosmetics_roman"]
rome_missing = [k for k in _ROMAN_INSTITUTIONS
                if k not in (S.load_civ("rome_100ad").get("starting_techs") or [])]
check("Rome is granted its own institutions through starting_techs",
      not rome_missing, str(rome_missing))
still_free = [k for k in _ROMAN_INSTITUTIONS if NODES[k]["cap"] == 0 and NODES[k]["ph"] == 0]
check("Rome's institutions are not free for whoever starts them",
      not still_free, str(still_free))
s = sim(civ="norse_900ad")
norse_has_them_free = [k for k in _ROMAN_INSTITUTIONS if k in s.done]
check("a Norse founder is not handed Rome's institutions for nothing",
      not norse_has_them_free, str(norse_has_them_free))

# --- round 2 A: geography-locked agriculture must not be startable
# anywhere on earth
s = sim(civ="norse_900ad")
ok_chinampa = s.can_start("fud_chinampa")
check("chinampa agriculture is not startable in Norway",
      not ok_chinampa)
s = sim(civ="mexica_1500")
check("chinampa agriculture is still free for the Mexica",
      "fud_chinampa" in s.done)

# --- round 2 B: anachronism is gated by nothing much
s = sim(civ="rome_100ad")
_ANACHRONISMS = ["mil_chemical_mustard", "mil_trace_italienne", "mil_general_staff",
                 "mil_conscription_reserve", "mil_trench", "hot_air_balloon",
                 "mil_observation_balloon", "mil_gunpowder_base"]
startable_turn_one = [k for k in _ANACHRONISMS if s.can_start(k)]
check("no anachronistic weapon or doctrine is startable turn one",
      not startable_turn_one, str(startable_turn_one))
check("mustard gas needs industrial chlorine and a delivery shell",
      set(["mat_chlorine", "mil_artillery_shell"]) <= set(NODES["mil_chemical_mustard"]["pre"]),
      str(NODES["mil_chemical_mustard"]["pre"]))
check("trace italienne fortification answers an actual cannon",
      "mil_artillery_piece" in NODES["mil_trace_italienne"]["pre"],
      str(NODES["mil_trace_italienne"]["pre"]))
check("a trench answers an actual machine gun and shellfire",
      set(["mil_machine_gun_recoil", "mil_artillery_shell"]) <= set(NODES["mil_trench"]["pre"]),
      str(NODES["mil_trench"]["pre"]))
check("gunpowder claims no saltpetre it has not earned via nitre_beds",
      "nitre_beds" in NODES["mil_gunpowder_base"]["pre"],
      str(NODES["mil_gunpowder_base"]["pre"]))

# --- round 2 G: five centuries, two events -- Norse hazards must do something
norse_hazards = S.load_civ("norse_900ad")["hazards"]
check("the Norse civilization has more than one dated hazard",
      len(norse_hazards) > 1, "only %d" % len(norse_hazards))
_EFFECT_FIELDS = ("staff_loss", "sack_chance", "output_factor", "real_erosion",
                   # "values" was missing from this tuple even though it has
                   # been a real, engine-read effect field since the
                   # Christianisation gradual-shift mechanism was added (see
                   # _shocks in society.py) - Rome's Ostrogothic Italy, Han's
                   # Jin reunification and several Mexica entries are all
                   # already values-only and this check simply never looked
                   # at them, because it only ever scanned Norse. Adding the
                   # Norse settlement-of-Iceland, Hakon-Hakonarson and
                   # Reformation entries - each a real event whose honest
                   # effect on this society is what it believes, not a body
                   # count or a burned field - is what caught the gap.
                   "values")
inert = [h["name"] for h in norse_hazards if not any(f in h for f in _EFFECT_FIELDS)]
check("no Norse hazard is purely decorative (no effect field the engine reads)",
      not inert, str(inert))

