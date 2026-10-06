"""Policies, creditors and hazard value shifts: knowledge is kept while plant is shed, the automatic hiring and training policies, staff trimming against credit, work in hand, and a hazard's gradual values delta."""
from .harness import *  # noqa: F401,F403
from .agent_command_helpers import ask_agent, pristine_game

# ============================================================================
# Round two, sections C-F: knowledge vs plant, the automatic policies, warning
# a player before they commit to work nobody can do, and legible hours.
# ============================================================================
import time as _time

# --- C: knowledge is not a building. A tester watched creditors make the
# founder forget Newton's laws and basic textile technique. "physics" was
# already protected; "theory" and "knowledge" (what the tree itself calls the
# rest of abstract science) were not, even though several of those nodes carry
# real upkeep the same way Newton's laws does. A loss-making node that is
# neither is the control: it SHOULD still be shed.
# The control must be a real establishment node that still carries upkeep
# under the JOB 1 upkeep audit - a technique such as hom_eraser_breadcrumb has
# zero upkeep there (a rubber eraser is a technique, not an establishment) and
# so never exercises this path. md2_sand_filtration stayed in the audit's
# kept "mining" category and still carries upkeep.
_KNOW1, _KNOW2, _LOSS = "md2_cell_theory", "md2_dna", "md2_sand_filtration"
s = sim()
check("theory and knowledge categories are protected the same way physics is",
      s.never_abandon(_KNOW1) and s.never_abandon("sc2_physics_newtons_laws"),
      "%s cat=%s" % (_KNOW1, NODES[_KNOW1]["cat"]))
check("a loss-making, non-knowledge node is NOT protected (the control case)",
      not s.never_abandon(_LOSS), NODES[_LOSS]["cat"])

s = sim(capital=-100000.0)
s.done.add(_LOSS); s.done.add(_KNOW1)
s._done_changed()
# IT HAS TO BE OPEN TO BE WORTH CLOSING. Upkeep follows `operating`, so a
# concern already shut is already costing nothing; shedding it saves nothing
# and would only destroy what you know. shed_loss_makers scanned `done` and
# did exactly that.
s.operating.add(_LOSS); s.operating.add(_KNOW1)
s.revenue = lambda: 0.0        # force a loss regardless of the rest of the economy
s.shed_loss_makers(100)
check("shed_loss_makers closes a loss-making concern, and spares knowledge",
      _LOSS not in s.operating and _KNOW1 in s.operating,
      "loss-maker closed=%s knowledge closed=%s"
      % (_LOSS not in s.operating, _KNOW1 not in s.operating))
check("...and what it closed is still something you know how to do",
      _LOSS in s.done and _KNOW1 in s.done,
      "still known: %s %s" % (_LOSS in s.done, _KNOW1 in s.done))
check("shed_loss_makers mothballs, and NAMES, what it takes",
      _LOSS in s.mothballed and any(_LOSS in message for _, message in s.log),
      [message for _, message in s.log])
# The control: a loss-maker that is SHUT is left alone entirely.
s_sh = sim(capital=-100000.0)
s_sh.done.add(_LOSS); s_sh._done_changed()
s_sh.revenue = lambda: 0.0
s_sh.shed_loss_makers(100)
check("a loss-maker that is already shut is not unlearned to no purpose",
      _LOSS in s_sh.done and _LOSS not in s_sh.mothballed,
      "known=%s mothballed=%s" % (_LOSS in s_sh.done, _LOSS in s_sh.mothballed))

s = sim(capital=-100000.0)
s.done.add(_LOSS); s.done.add(_KNOW2)
s._done_changed()
# A creditor seizes a CONCERN, not a memory, so it has to be open to be taken.
s.operating.add(_LOSS); s.operating.add(_KNOW2)
s.credit_limit = lambda: 0.0   # force straight past the credit floor
s.enforce_credit_limit(100)
# NOW ABOUT WHAT IS RUNNING, not about what is known. Creditors close and sell
# up a concern; they cannot take away your memory of how it worked, which is
# also why a weird-play tester could reach a state where a node was
# simultaneously forgotten and running and no verb would touch it.
check("creditors close a loss-making concern and cannot touch knowledge",
      _LOSS not in s.operating and _KNOW2 in s.operating,
      "loss-maker closed=%s knowledge closed=%s"
      % (_LOSS not in s.operating, _KNOW2 not in s.operating))
check("a concern the creditors took is still a thing you know how to do",
      _LOSS in s.done,
      "still known: %s" % (_LOSS in s.done))
check("creditors' seizure mothballs, and NAMES, what it takes",
      _LOSS in s.mothballed and any(_LOSS in message for _, message in s.log),
      [message for _, message in s.log])

# --- C: a repossessed work must not look like fresh research
s = sim(capital=100000.0)
s.done.add(_LOSS); s._done_changed()      # you BUILT it; that is what mothballing means
s.mothballed.add(_LOSS)
ok, why = s.start_reason(_LOSS)
check("a mothballed work refuses to be started as if it were new research",
      not ok and "restore" in why, why)
avail = S._agent_available(s, NODES, {"all": True})
check("a mothballed work does not appear in available looking like new research",
      not any(entry["id"] == _LOSS for entry in avail["available"]), avail["count"])

# --- ROUND 8: THE DEADLOCK. A play tester lost precision_three_plate to a
# third-century sack and could not get it back by any verb: `start` sent them
# to `restore`, `restore` said they no longer knew how, `open` said they had
# not built it, `mothball` said there was nothing to shut. That node gates the
# whole precision branch, so `available` read "0 startable now" for a hundred
# and eighty years while they held a quarter of a billion denarii.
s_dl = sim(capital=100000.0)
s_dl.trades_created.add("engineer")
s_dl.employees["engineer"] = 2.0
s_dl.mothballed.add(_LOSS)                # mothballed, and NOT known: the trap
ok_dl, why_dl = s_dl.start_reason(_LOSS)
check("a work whose knowledge was destroyed can be built again",
      ok_dl, why_dl)
ok_rs, why_rs = s_dl.restore_work(_LOSS)
check("...and restore says to build it, not that it cannot be restored",
      not ok_rs and "start" in why_rs, why_rs)
_av_dl = S._agent_available(s_dl, NODES, {"all": True})
check("...and it is visible in available, not hidden behind a stale mothball",
      any(entry["id"] == _LOSS for entry in _av_dl["available"]), _av_dl["count"])
s_dl.start_project(_LOSS)
check("...and starting it clears the stale mothball entry",
      _LOSS not in s_dl.mothballed and _LOSS in s_dl.active,
      (_LOSS in s_dl.mothballed, _LOSS in s_dl.active))

# The path that created it: insolvency abandonment discarded from `done` AND
# added to `mothballed`, the same pair of lines already fixed twice elsewhere.
s_ab = sim(capital=-100000.0)
s_ab.done.add(_LOSS); s_ab._done_changed()
s_ab.operating.add(_LOSS)
s_ab.revenue = lambda: 0.0
s_ab.step()
check("no path in the engine leaves a work mothballed but unknown",
      _LOSS in s_ab.mothballed and not (s_ab.mothballed - s_ab.done),
      sorted(s_ab.mothballed - s_ab.done)[:4])

# --- D1: auto_hire must not take on staff this year's income cannot carry
s = sim(civ="rome_100ad", capital=400.0, manual=False, events=False)
s.step()
check("auto_hire does not overcommit turn one against a thin surplus",
      s.scholars < 0.2 and s.artisans < 0.6,
      "scholars %.3f artisans %.3f capital %.1f" % (s.scholars, s.artisans, s.capital))

# --- D2/E: auto_train (and a `start` warning) must be demand-led: driven by
# what is startable now but for the trade, not by every node whose direct
# prerequisites happen to be satisfied somewhere deep in the tree.
s = sim(civ="rome_100ad", capital=1e6, manual=True, events=False)
ok_ig, why_ig = s.start_reason("ag2_hydrometer", ignore_trade=True)
check("ignore_trade accepts a node that is startable but for the trade alone",
      ok_ig, why_ig)
ok_norm, why_norm = s.start_reason("ag2_hydrometer")
check("without ignore_trade the same node is refused specifically for the trade",
      not ok_norm and "optician" in why_norm, why_norm)
s.done.update(NODES["ag2_cold_store"]["pre"])  # prerequisites held, so only staffing can refuse
ok_staff, why_staff = s.start_reason("ag2_cold_store", ignore_trade=True)
check("ignore_trade still refuses a node blocked by missing STAFF, not just the trade",
      not ok_staff and "craftsmen" in why_staff, why_staff)

s = sim(civ="rome_100ad", capital=1e6, manual=True, events=False)
node = "ag2_cold_store"
for p in NODES[node]["pre"]:
    s.done.add(p)
s.artisans, s.scholars = 10.0, 10.0
r0 = S._agent_dispatch(s, NODES, {"cmd": "start", "id": node})
check("start refuses outright when a needed trade has never been taught",
      not r0["ok"] and "engineer" in r0.get("error", ""), r0)
s.labour.train("engineer", 2)          # training begun; nobody is ready for two years
r1 = S._agent_dispatch(s, NODES, {"cmd": "start", "id": node})
check("start accepts work nobody can do yet only WITH a warning naming the trade",
      r1["ok"] and "engineer" in r1.get("warning", ""), r1)

# --- D4: fractional staff counts are explained, not silently shown (D1's game, one year in)
st = S._agent_state(s, NODES, {})
check("a fractional staff count comes with an explanation of what the fraction means",
      (abs(s.scholars - round(s.scholars)) < 0.02 and abs(s.artisans - round(s.artisans)) < 0.02)
      or bool(st.get("staff_are_fractional_because")),
      "scholars %.3f artisans %.3f" % (s.scholars, s.artisans))
st2 = S._agent_state(pristine_game(), NODES, {})
check("a whole-number staff carries no fraction footnote",
      st2.get("staff_are_fractional_because") is None, st2.get("staff_are_fractional_because"))

# --- F: say how the founder's hours were spent
ratios = []
for _ in range(3):
    s.step()
    h = s.hours_this_year
    total = h["wage_work"] + h["teaching"] + h["offered_to_projects"] + h["unused"]
    check("a year's founder hours are fully accounted for (year %d)" % s.year,
          abs(total - h["available"]) < 1e-6, h)
    for k, pst in s.active.items():
        off = pst.get("hours_offered_this_year", 0.0)
        eff = pst.get("hours_effective_this_year", 0.0)
        if off > 1:
            ratios.append(eff / off)
check("an underfunded project's refund is proportional, not always exactly half",
      any(abs(ratio - 0.5) > 0.02 for ratio in ratios), ratios)
st = S._agent_state(s, NODES, {})
check("state reports the year's hours summary",
      st.get("hours_this_year") == s.hours_this_year, st.get("hours_this_year"))
check("state reports hours offered/effective per active project",
      not st["active"] or any("hours_offered_this_year" in value for value in st["active"].values()),
      st["active"])

# --- performance: `available` must return quickly even deep in the tree under
# fog. A regression here (start_reason recursing into is_visible, which
# recurses into start_reason, unmemoised) took a single `available` call under
# fog on norse_900ad from instant to over a minute.
s = sim(civ="norse_900ad")
s.fog = True
s.revealed = set()
t0 = _time.time()
S._agent_available(s, NODES, {})
elapsed = _time.time() - t0
check("available returns quickly under fog, not in tens of seconds",
      elapsed < 5.0, "%.2fs" % elapsed)

# ============================================================================
# Round two, section P: a hazard can carry a `values` delta, the same way a
# technology does, and it must land gradually and be visible while it is
# happening. Norse Christianisation (995-1100) is the case in point: it
# carries a `values` block in the civ file, not a placeholder ENGINE TODO
# note.
# ============================================================================

_christ = next(hazard for hazard in S.load_civ("norse_900ad")["hazards"]
              if hazard["name"].startswith("Christianisation"))
check("Christianisation now carries a values delta, not just a TODO note",
      bool(_christ.get("values")), _christ.get("values"))

# --- gradual, not a single jump: one year of a 106-year hazard should move
# the needle by roughly a hundredth of the total, not all of it at once.
s = sim(civ="norse_900ad")
before = dict(s.value_weights)
s._shocks(995)
step1 = s.value_weights["w_religious_rigidity"] - before["w_religious_rigidity"]
total_asked = _christ["values"]["w_religious_rigidity"]
check("a hazard's values shift lands gradually: one year moves it a fraction "
      "of the total, not the whole amount",
      0 < step1 < total_asked * 0.5, "%.4f of %.2f" % (step1, total_asked))

# --- and by the hazard's last year the FULL delta has landed, spread evenly
# across every year in between (995 already applied above; finish the span).
for yr in range(996, 1101):
    s._shocks(yr)
total_moved = s.value_weights["w_religious_rigidity"] - before["w_religious_rigidity"]
check("a hazard's values shift reaches its full stated amount across the "
      "full span of years",
      abs(total_moved - total_asked) < 1e-6,
      "%.6f vs %.2f asked" % (total_moved, total_asked))

# --- visible WHILE it happens: the society turning against the player has to
# show up in the log more than once, and not only at the first or last year,
# or a player has no way to see it coming except by reading the future.
shift_years = [y for y, msg in s.log if "values are shifting" in msg]
check("a values shift is logged more than once while the hazard is running, "
      "not only as a single note",
      len(shift_years) >= 3, shift_years)
check("some of those log lines land mid-hazard, not only at the first or "
      "last year",
      any(995 < y < 1100 for y in shift_years), shift_years)

# --- a hazard with no staff_loss/sack_chance/output_factor/real_erosion at
# all, only `values`, must still be applied (the mechanism must not be
# piggy-backing on one of the four old fields being present).
s2 = sim(civ="norse_900ad")
s2.civ = dict(s2.civ)
s2.civ["hazards"] = [{"name": "values-only test hazard",
                      "values": {"w_novelty": -0.2}, "years": [900, 909]}]
s2.value_weights = s2.civ["values"] = dict(s2.value_weights)
f0 = s2.value_weights["w_novelty"]
for yr in range(900, 910):
    s2._shocks(yr)
check("a hazard that carries ONLY a values delta (no staff_loss, sack_chance, "
      "output_factor or real_erosion) still moves the society",
      abs(s2.value_weights["w_novelty"] - (f0 - 0.2)) < 1e-6,
      "%.4f -> %.4f" % (f0, s2.value_weights["w_novelty"]))

# --- foreseeable, not just felt: knowledge_risk must let a player see the
# shift coming before it starts, the same complaint that section G raised
# about Christianisation producing "no event and no visible consequence".
kr = ask_agent(pristine_game("norse_900ad"), cmd="risk")["knowledge_risk"]
christ_row = next((hazard for hazard in kr["known_hazards_ahead"]
                   if hazard["name"].startswith("Christianisation")), None)
check("knowledge_risk lists Christianisation among the hazards ahead, "
      "before it starts",
      christ_row is not None, kr.get("known_hazards_ahead"))
check("knowledge_risk's note on Christianisation says what it does to the "
      "society, not only what it does to output",
      christ_row is not None and "values" in christ_row.get("note", "").lower(),
      christ_row and christ_row.get("note"))

# --- the "Norse cannot be sacked" finding this mechanism must not disturb:
# a values shift is not a sack, and Christianisation still has none of the
# sack_chance fields that would make it one.
check("Christianisation still carries no sack_chance (a values shift is not "
      "a sacking, and Norse assembly society still has no capital to sack)",
      "sack_chance" not in _christ, _christ)

# 2. Staff force-fired to zero with credit still to spare, and nothing logged.
# The tester's exact condition: staff on the books, capital NEGATIVE but only a
# third of the way into a credit line nobody has withdrawn. A household with
# credit left borrows and makes payroll; that is what credit is for.
# (a) A payroll the remaining credit COVERS costs you nobody but attrition.
s = sim(capital=22400.0 * pristine_game().labour.money_per_labour_hour())  # 6000 coin at the old coin value, in labour hours
s.policy["auto_hire"] = False
# One labourer: wages track labour tightness now, so a smith or two people
# would exceed the credit line and rightly be trimmed. The precondition on
# the check keeps the case honest.
s.labour.hire("labourer", 1)
s.capital = -s.credit_limit() * 0.35
_before = sum(s.employees.values())
# What the household can still spend on wages: income plus remaining credit,
# after the costs that are not wages.
_room = (s.revenue() + s.capital + s.credit_limit()
         - (s.living_cost() - s.labour.wage_bill()) - s.upkeep())
_payroll_before = s.labour.wage_bill()
s.step()
_after = sum(s.employees.values())
check("staff are not let go while there is still credit to pay them",
      _room > _payroll_before and _after > _before * 0.95,
      "%.2f -> %.2f with %.0f still to spend against a %.0f payroll"
      % (_before, _after, _room, s.labour.wage_bill()))

# (b) A payroll it only PARTLY covers costs you part of the staff, not all of
#     it. The tester's five went to zero in one step with two thirds of the
#     credit line untouched; what should happen is that you keep as many as
#     your remaining means will pay for.
s = sim(capital=22400.0 * pristine_game().labour.money_per_labour_hour())  # 6000 coin at the old coin value, in labour hours
s.policy["auto_hire"] = False
s.labour.hire("smith", 5)
# Means that cover a bit over half the payroll: what is left of the credit line plus the year's revenue,
# after upkeep, mining and living costs other than wages, as the staff step measures it. Living costs
# can move with capital, so settle capital until the means match.
for _settle in range(20):
    _means = (s.revenue() - s.upkeep() - (s.living_cost() - s.labour.wage_bill()) - s.mine_operating_cost()
              + s.capital + s.credit_limit())
    s.capital += 0.6 * s.labour.wage_bill() - _means
_b3 = sum(s.employees.values())
s.step()
check("an unaffordable payroll is trimmed to what you can pay, not emptied",
      0.5 < sum(s.employees.values()) < _b3,
      "%.2f -> %.2f" % (_b3, sum(s.employees.values())))

# ...and when they DO go, because there is genuinely no money left to borrow,
# it is said. The old code logged only in the branch that never happened.
s = sim(capital=22400.0 * pristine_game().labour.money_per_labour_hour())  # 6000 coin at the old coin value, in labour hours
s.policy["auto_hire"] = False
s.labour.hire("smith", 5)
s.capital = -s.credit_limit() * 1.5
_b2 = sum(s.employees.values())
s.step()
check("losing staff you cannot pay is written in the log, never silent",
      sum(s.employees.values()) < _b2
      and any("cannot pay everyone" in message for _year, message in s.log),
      "%.2f -> %.2f, log %r" % (_b2, sum(s.employees.values()), s.log[-3:]))

# 4. auto_shed discards technologies you built - under fog the only score there
#    is - and it was on by default for a player.
_manual_policy, _optimizer_policy = sim(manual=True).policy, sim(manual=False).policy
check("nothing that deletes your work is on by default for a player",
      _manual_policy["auto_shed"] is False and _optimizer_policy["auto_shed"] is True,
      (_manual_policy["auto_shed"], _optimizer_policy["auto_shed"]))

# --- the sweep of every playtest note: what was still live ------------------
# S2. `start` took all 104 available projects in a fresh England game - 43,914
# denarii of work in hand against 400 in cash and a displayed credit limit of
# 1,503 - and put the player at -3,672 one step later. `help economy` promises
# "as far as somebody will lend you and no further"; nothing enforced it.
s = sim(civ="england_1300")
_taken, _refused = 0, None
for _k in list(s.order):
    if s.can_start(_k):
        _ok, _why = s.start_project(_k)
        if _ok:
            _taken += 1
        elif "work in hand" in (_why or ""):
            _refused = _why
            break
_owed = sum(project_state.get("cost_left") or 0.0 for project_state in s.active.values())
check("you cannot commit to more work than cash and credit could ever cover",
      _refused is not None and _owed <= max(0.0, s.capital) + s.credit_limit() + 1,
      "took %d projects, owing %.0f against %.0f of cash and credit"
      % (_taken, _owed, max(0.0, s.capital) + s.credit_limit()))

# S14. A node that costs nothing to build and 20 a year to keep could be shut
# down and brought back around the annual tick for nothing, so its upkeep was
# optional. The engine already gets this right for mines.
# The candidate is named directly rather than found by filter (up>0, no
# prerequisite, project_cost under 1 denarius): the JOB 1 upkeep audit zeros
# `up` on every technique that filter would match, and every remaining
# up>0/no-prerequisite/near-free node turns out to be something auto-granted
# on turn one (a capability rung, a road network) - excluded by `not in
# s.granted` and so invisible to the filter too. There is also a sharper
# reason not to compute this dynamically: `s.done.add` below bypasses
# `start`'s own prerequisite check, but restore_work has its OWN separate
# check ("you no longer have what it stands on") that reads real
# prerequisites regardless of how `done` was populated, so a candidate with
# unmet prerequisites makes restore_work silently refuse and charge nothing -
# which reads as exactly the bug this check exists to catch, for a completely
# different reason. md2_sand_filtration is not
# auto-granted (its `ph` is not zero), and keeps real mining-establishment
# upkeep under the audit, so it is named directly rather than found.
s = sim(civ="england_1300", capital=50000.0)
_free = ["md2_sand_filtration"]
s.done.add(_free[0])
s.done.update(NODES[_free[0]]["pre"])  # restore_work refuses while a prerequisite is unmet
s._done_changed()
s.mothball_work(_free[0])
_cap = s.capital
s.restore_work(_free[0])
check("shutting a work down and reopening it is never free",
      _cap - s.capital >= NODES[_free[0]]["up"],
      "%s round trip cost %.0f against %.0f a year of upkeep"
      % (_free[0], _cap - s.capital, NODES[_free[0]]["up"]))

# --- a run that has stopped has to say so --------------------------------
# A weird-play tester's "most important finding": a run sat at exactly -924.5
# denarii for fifty years, completing nothing, while INSOLVENCY SETTLED fired
# once a decade for ever, and nothing anywhere said the run had effectively
# stopped or that it was escapable. It WAS escapable - they got out by working
# for wages - which is exactly why silence was the defect.
s = sim(civ="norse_900ad", capital=40000.0)
s.labour.hire("smith", 3)
_loser = [node_id for node_id in NODES if NODES[node_id]["up"] > NODES[node_id]["rev"] > 0][:1]
if _loser:
    s.done.add(_loser[0]); s._done_changed(); s.open_venture(_loser[0])
s.capital = -900.0
s.insolvent_years = 12
_diag = s.stall_diagnosis()
check("a run that has effectively stopped says so, and says what would restart it",
      _diag and _diag["what_would_change_it"]
      # "work for wages" became "work as a <trade>", because advice that does
      # not say which job to take can be followed into a loss.
      and any(reason.startswith("work as a ") for reason in _diag["what_would_change_it"]),
      _diag)
check("a solvent run is not told it is stuck",
      pristine_game("norse_900ad").stall_diagnosis() is None,
      pristine_game("norse_900ad").stall_diagnosis())

# --- the invariant behind a whole class of contradiction ---------------------
# A weird-play tester reached, in seven years from a fresh start, a node that
# was simultaneously forgotten and running: `state` said the concern was
# running, `ventures` billed for it, `money` charged nothing, and all four
# verbs refused it on mutually contradictory grounds - `start` said restore it,
# `restore` said start it, `open` said you do not know it, `mothball` said you
# never built it. The entry could never be cleared. Every one of those symptoms
# is the same broken invariant: you cannot be running something you do not know
# how to do.
def _operating_subset_of_done(sim_state):
    return sorted(sim_state.operating - sim_state.done)


s = sim(capital=-100000.0, civ="norse_900ad")
s.done.add(_LOSS); s._done_changed(); s.operating.add(_LOSS)
s.credit_limit = lambda: 0.0
s.enforce_credit_limit(100)
check("creditors' seizure cannot leave you running what you no longer know",
      not _operating_subset_of_done(s), _operating_subset_of_done(s))

s = sim(civ="han_china_100ad", manual=False)
for _ in range(2):          # the first year opens nothing yet
    s.step()
check("a long run never ends up running something it does not know",
      s.operating and not _operating_subset_of_done(s), _operating_subset_of_done(s)[:5])

# 8. `policy auto_hire on` must still grow the staff of a household that can pay for it. The
#    no-surplus case (no hiring floor under the affordability scale) is the D1 check above.
s = sim(civ="han_china_100ad")
# Han's coin is small, so a fixed purse is a fraction of a labourer-year.
s.capital = 1000 * s.labour.market.quote_annual("labourer")
s.policy["auto_hire"] = True
s.step()
check("auto_hire on a rich household actually hires",
      sum(s.employees.values()) > 1.0,
      "staff %.2f on %.0f" % (sum(s.employees.values()), s.capital))

# A play tester spent about eight years and 5,952 denarii working out that
# negative capital silently disables hiring and opening while both switches
# still read ON.
s = sim(civ="rome_100ad")
s.policy["auto_hire"] = True
s.policy["auto_open"] = True
s.capital = -500.0
_pol = S._agent_dispatch(s, NODES, {"cmd": "policy"})
check("a switch that is on but cannot act says so",
      set(_pol.get("switched_on_but_cannot_act_right_now") or {})
      >= {"auto_hire", "auto_open"},
      _pol.get("switched_on_but_cannot_act_right_now"))
check("...and says nothing when they all can",
      "switched_on_but_cannot_act_right_now" not in
      S._agent_dispatch(sim(capital=50000.0), NODES, {"cmd": "policy"}),
      "field present on a solvent household")
