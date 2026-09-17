"""people_attrition_scholars: split verbatim from the old test_regressions.py (original lines 7782-8420).

Moving contiguous blocks verbatim: no check below was reformatted, reworded or otherwise touched in the split.
"""
from .harness import *  # noqa: F401,F403

# =============================================================================
# PEOPLE ARE WHOLE. The user's objection, and it was right: "how can you have
# .8 people? I feel like all employees/people should be measured in
# integers." Attrition used to multiply every trade by (1 - 0.035) every
# single year, so ten smiths lost exactly 0.35 of a smith and the engine went
# on carrying the fraction forever - a household could read "1.32 artisans"
# or "0.03 engineers" on its own roster, the latter drawing 0.03 of a wage
# while supervising nothing. Attrition is now a per-person roll against
# self.rng (sorted by trade name, for the same PYTHONHASHSEED-independence
# every other rng loop over this dict already has); hire() and train() now
# refuse a fractional `n` outright, and the auto_hire smoothing that used to
# write a continuous target straight into `employees` now spends its
# fractional remainder as that year's CHANCE of the next whole hire instead
# (`_stochastic_round`).
# =============================================================================

s = sim(capital=50_000_000.0)
s.policy["auto_hire"] = False
s.employees["artisan"] = 500.0
s._resync_pools()
_whole_every_year, _never_grew, _prev = True, True, 500.0
for _ in range(150):
    s.step()
    _cur = s.employees.get("artisan", 0.0)
    if abs(_cur - round(_cur)) > 1e-9:
        _whole_every_year = False
    if _cur > _prev + 1e-9:
        _never_grew = False
    _prev = _cur
check("a whole headcount of artisans never picks up a fraction of a person, "
      "year after year of pure attrition",
      _whole_every_year, _prev)
check("...and with auto_hire off and nobody hiring, the headcount only ever "
      "falls, never climbs on its own",
      _never_grew, _prev)

# UNBIASED: the realised loss, averaged over many people and many
# independent seeds, should still land on the nominal 3.5%/yr every balance
# comment elsewhere in this file quotes - a per-person roll that happened to
# be biased would quietly make every one of those comments false.
_before_att, _after_att = 0.0, 0.0
for _seed in range(1, 31):
    _s = S.Sim(NODES, ORDER, random.Random(_seed), manual=True,
               civ=S.load_civ("rome_100ad"), cfg={"start_capital": 5e7})
    _s.goal, _s.done_year = GOAL, {}
    _s.policy["auto_hire"] = False
    _s.employees["artisan"] = 2000.0
    _s._resync_pools()
    _s.step()
    _before_att += 2000.0
    _after_att += _s.employees.get("artisan", 0.0)
_att_rate = 1.0 - _after_att / _before_att
check("whole-person attrition still averages the nominal 3.5% a year, over "
      "many people and many seeds",
      0.030 < _att_rate < 0.040, _att_rate)

# HIRE AND TRAIN LAND WHOLE PEOPLE.
s = sim(capital=1e6)
ok_frac_h, why_frac_h = s.hire("smith", 2.5)
check("hire refuses a fractional number of people",
      not ok_frac_h and "whole" in why_frac_h, why_frac_h)
ok_frac_t, why_frac_t = s.train("machinist", 1.5)
check("...and so does train",
      not ok_frac_t and "whole" in why_frac_t, why_frac_t)
ok_whole_h, _ = s.hire("smith", 2)
check("...but a whole number still goes through, and lands exactly that many",
      ok_whole_h and s.employees.get("smith") == 2.0, s.employees.get("smith"))


# =============================================================================
# THE TWO RULEBOOKS. Measured, reproducible: `hire scholar 12` was refused
# - "this society's literacy will not supply more than 5.9 scholars in
# total, ever, at any price" - while `policy auto_hire on` mutated
# self.scholars directly, never once called hire() or literate_capacity(),
# and reached 146.4 scholars in the same civilisation forty years later. The
# goal itself, and two nodes on the only road to it, want 25. Both halves are
# fixed together: step()'s auto_hire now clamps its target to
# literate_capacity("scholar") (see core.py), and literate_capacity("scholar")
# now adds the SAME institutional pool staff_capacity() already credited
# auto_hire with (see labour.py) - so the wall is not only closed, it is wide
# enough to reach what the tree actually asks for.
# =============================================================================

# 73 SECONDS, because it needs two and a half centuries of a rich run before
# the question it asks even becomes interesting. The cheap half of the same
# fix - that the ceiling itself widens with the institutions - is checked
# below in milliseconds and stays on the fast path.
def _auto_hire_respects_the_wall():
    s_ = sim(capital=1e9, manual=False)
    for _ in range(250):
        s_.step()
    return (s_.scholars <= s_.literate_capacity("scholar") + 1e-6
            and s_.scholars > 10.0,
            (s_.scholars, s_.literate_capacity("scholar")))

slow_check("auto_hire never grows scholars past the wall hire() enforces, and "
           "over two and a half centuries grows well past the old ceiling of six",
           _auto_hire_respects_the_wall)

# The bare, no-institution ceiling a fresh household sees is unchanged...
s0 = sim()
check("the market-reach ceiling for a fresh household is the same as before",
      5.5 < s0.literate_capacity("scholar") < 6.5, s0.literate_capacity("scholar"))
# ...and grows once the institutions auto_hire was already trusted to grow
# toward are actually running - not from literacy alone, which is the
# mechanism that lets a household eventually reach the tree's 25.
s1 = run_it(sim(capital=1e9), "interchangeable_parts", "power_grid")
check("building the institutions auto_hire already credited widens the wall "
      "hire() enforces, which used to move only with literacy",
      s1.literate_capacity("scholar") > 20.0, s1.literate_capacity("scholar"))

# The refusal is honest about what is actually binding: a household's reach
# into the labour market, narrowed by literacy, not literacy by itself.
s2 = sim()
ok2, why2 = s2.hire("scholar", 12)
check("the refusal names the household's market reach, not literacy alone",
      not ok2 and "reach" in why2 and "literacy" in why2, why2)


# =============================================================================
# ONLY `scholar` COUNTS AS A TRAINED SCHOLAR. TRADE_FAMILY groups scholar,
# chemist, engineer, scribe and merchant together as "scholar" for
# market_supply()'s sake - they draw on the same small, literate-or-
# propertied slice of the population - and an earlier version of
# _resync_pools() reused that same grouping to decide who counts as a
# trained scholar for the tech tree's "sch" gate. Hiring three scribes
# measurably raised effective_scholars() from 0 to 4.0, while STAFF_SOURCES
# - the advice on how to grow scholars - has only ever named `hire scholar`.
# Now only the `scholar` trade itself feeds the gate; the market-sizing use
# of the wider grouping (market_supply, labour_price_factor) is untouched.
# =============================================================================

s = sim(capital=1e6)
_before_sch = s.effective_scholars()
ok_scribe, _ = s.hire("scribe", 3)
check("(three scribes were actually hired)", ok_scribe, s.employees)
check("hiring scribes does not inflate the trained-scholar headcount any more",
      abs(s.effective_scholars() - _before_sch) < 1e-6,
      (s.effective_scholars(), _before_sch))
s.capital = 1e6
ok_sch, _ = s.hire("scholar", 2)
check("...but hiring an actual scholar still does",
      ok_sch and s.effective_scholars() >= _before_sch + 2 - 1e-6,
      s.effective_scholars())
check("the advice on how to get scholars never points at a different trade "
      "family's trade, which would not even count",
      all("scribe" not in why and "chemist" not in why and "merchant" not in why
          and "engineer" not in why
          for _node, why in s.STAFF_SOURCES.get("scholars", [])),
      s.STAFF_SOURCES.get("scholars"))

# --- SAVE INTEGRITY, JOB 2a: FOG CAN BE REWOUND. A tester described the
# exploit exactly: "since `load` restores the game but not the player's
# memory, a player can save, build a node, look at what appeared in
# `available`, load back, and keep the knowledge. Fog of war is one command
# away from being off" (playtest/AUDIT_rounds_1_6.md, C1), and reproduced
# it live: save at year 1300, step to 1350, load the 1300 save, and the fifty
# years of frontier that had opened up in `available` cost nothing at all,
# because the ledger went back to 1300 and the knowledge did not. The fix
# makes `revealed` a ratchet: assigning to it may grow what this running
# session has seen, never shrink it - a property on FogMixin (engine/fog.py)
# rather than a change to `load_state` itself, so the guarantee holds for
# every caller that ever assigns `.revealed`, load_state included, without
# needing to edit protocol.py. See the comment on the property.
s_fog = sim(civ="rome_100ad")
s_fog.fog = True
s_fog.revealed = {"identity_cover"}
_fog_save = os.path.join(ROOT, _PLAY_DIR, "fog_rewind.json")
S.save_state(s_fog, _fog_save)                  # "before you paid for it"
# Something completes and reveals what it leads to - the same thing
# _complete() does in projects.py when a project actually finishes.
s_fog.reveal_from("workshop_first")
_fog_after = set(s_fog.revealed)
check("(setup) building something under fog reveals what it leads to",
      _fog_after > {"identity_cover"}, sorted(_fog_after))
S.load_state(s_fog, _fog_save)                  # the rewind to before paying
check("fog cannot be rewound: loading an earlier save keeps everything this "
      "session has already seen, instead of refunding the look for free",
      _fog_after <= s_fog.revealed, sorted(_fog_after - s_fog.revealed))
# A GENUINELY FRESH RESUME - a new process loading someone's save as its very
# first act, exactly what `--session` does - must be untouched by this: it has
# seen nothing yet, so the union with nothing is exactly the file's own
# contents, the same as before this fix existed.
s_fresh = sim(civ="rome_100ad")
s_fresh.fog = True
s_fresh.revealed = set()
S.load_state(s_fresh, _fog_save)
check("a fresh resume still sees only what that save file actually recorded",
      s_fresh.revealed == {"identity_cover"}, sorted(s_fresh.revealed))

# --- SAVE INTEGRITY, JOB 2b: SAVE LOST ON A CLOSED PIPE. Two testers found,
# independently and the same way, that a command's progress could be lost if
# the process's own stdout closed mid-reply: `naive6/C/WEIRD_C.md` - "I lost
# 12 years of play twice before I noticed, because I was piping output
# through `head`" - and `naive5/C/WEIRD_C.md`, against the game's own promise
# in `help sittings` that you can "close the terminal, anything" and come back
# to exactly where you left off. `agent`'s stdin loop wrote the reply and
# saved the session AFTER it, so a SIGPIPE on that write killed the process
# before `save_state` ever ran, even though `_agent_dispatch` had already
# mutated `s` in memory. The fix reorders it to save first, the same as
# `play` already did; this proves it against the real subprocess, a real
# closed pipe, and a real file on disk.
_pipe_sess = os.path.join(ROOT, _PLAY_DIR, "closedpipe.json")
if os.path.exists(_pipe_sess):
    os.remove(_pipe_sess)
_pp = subprocess.Popen(
    [sys.executable, os.path.join(HERE, "simulator.py"), "agent",
     "--civ", "rome_100ad", "--seed", "1", "--session", _pipe_sess],
    stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    text=True, cwd=ROOT)
# Close OUR end of stdout before the child ever writes a single byte to it -
# the same thing `| head -c0`, or a closed terminal, does to a running
# process. Whatever the child writes after this has nowhere to go.
_pp.stdout.close()
try:
    _pp.stdin.write(json.dumps({"cmd": "step", "years": 3}) + "\n")
    _pp.stdin.close()
except BrokenPipeError:
    pass
_pp.wait(timeout=60)
try:
    _pp.stderr.close()
except Exception:
    pass
_pipe_saved = json.load(open(_pipe_sess))
check("a command's progress is saved even when the reply that describes it "
      "cannot be delivered because the reading end of the pipe is gone",
      _pipe_saved.get("year") == 103, _pipe_saved.get("year"))

# --- JOB 1: THE PLANNER. "Why is the sim a monte carlo sim? We know the end
# state, right? Or is it too complex to just calculate backwards?" It is not
# too complex: planner.py works backward from the goal by critical-path
# method (CPM) over its prerequisite closure, instead of walking a
# hand-written list. These checks pin the structural properties the measured
# comparison (playtest or the session report) depends on actually
# holding, not just the one run that happened to be timed.
_p_s = sim(civ="rome_100ad")
_p_order, _p_c, _p_extras, _p_staff = PLANNER.backward_plan(NODES, GOAL, _p_s, side_branches=0)
_p_need = S.closure(NODES, GOAL)
check("the planner's closure matches its own order's count for the goal",
      len(_p_need) == len(_p_order), (len(_p_need), len(_p_order)))
# closure() now follows the single-option req_any groups too - it also
# follows the `req_any` groups that have exactly one option (a mandatory
# dependency authored as a substitution rather than a `pre` edge; a group
# with two or more real alternatives is correctly left alone, both because
# only one is actually required and because counting every option can
# cycle). The gap is real and was the second thing this session's own audit
# found blocking the goal: `mat_bulk_steel` needs `mat_manganese` through
# exactly this kind of single-option `req_any`, `closure()` cannot see it on
# purpose, and a traced Rome run with 111 scholars, 428 artisans and 11.7
# million denarii in hand still had not built it by year 700 because it was
# never in `need` at all - staffing and money were both long since solved,
# ordering was not.
_pre_only = set()
_stk = [GOAL]
while _stk:
    _c = _stk.pop()
    if _c in _pre_only:
        continue
    _pre_only.add(_c)
    _stk.extend(NODES[_c]["pre"])
check("following `pre` alone understates what the goal needs by the "
      "req_any groups that are not really alternatives",
      _pre_only < _p_need and len(_p_need) > len(_pre_only),
      (len(_pre_only), len(_p_need)))
# --- THE DATA SAID OVERLAND IN THREE PLACES AND THE TREE SAID ROUND THE
# CAPE. mat_platinum_bulk's own note says the Ural placers are "reachable
# overland through Scythian and Sarmatian trade without crossing any ocean";
# geography.json lists platinum in siberia_urals as well as americas_south
# and repeats the sentence; and the node's only prerequisite was
# exp_africa_circumnavigation. Once closure() started following single-option
# req_any groups this stopped being a curiosity and became load-bearing:
# platinum is required for the glass-to-metal seal, so the goal's closure
# grew an entire age of exploration - six expedition nodes, the sextant, the
# compass, the lodestone, the cross-staff, the backstaff and a world map,
# seventeen nodes in all - to fetch a metal the data says is on a wagon road.
# --- THE ONE REMEDY THE GAME OFFERS, CAPPED AT THE HOUSEHOLD OF YEAR FIVE.
# Saltpetre has no market to buy from (MARKET_SHARE is 0.0; the only bought
# supply is sixty tonnes a year of Bengal nitre once the eastern trade route
# runs), so nitre beds are the whole answer. auto_mine laid
# min(capital * 0.05, 2000) denarii of bed a year - a flat ceiling, never
# asking how short it was - while the mine branch beside it took 25% of
# capital and sized itself to the measured shortfall. A Rome run with
# staffing and money both solved spent 277 of its years short of saltpetre.
def _nitre_laid(capital):
    """One year of the auto_mine nitre branch at a given wealth."""
    n = sim(civ="rome_100ad")
    n.capital = float(capital)
    n.policy["auto_mine"] = True
    n.nitre_bed_m2 = 0.0
    n.binding = "saltpetre"
    before = n.nitre_bed_m2
    n.step()
    return n.nitre_bed_m2 - before

check("the nitre purchase is held to a flat two thousand denarii a year "
      "however rich the household - sizing it to the shortfall instead, "
      "the way the mine branch beside it does, measured worse on every "
      "count and is recorded in core.py as a road not to walk again",
      _nitre_laid(5_000_000.0) <= 2000.0 / S.Sim.NITRE_COST_PER_M2 + 1e-6,
      _nitre_laid(5_000_000.0))
check("...and a poor household is held to a twentieth of its capital",
      _nitre_laid(3_000.0) <= 3_000.0 * 0.05 / S.Sim.NITRE_COST_PER_M2 + 1e-6,
      _nitre_laid(3_000.0))
check("the nitre yield and price the advice quotes are the ones the "
      "purchase actually uses - 0.0008 t/m2 at 2.0 den/m2, so a tonne a "
      "year of shortfall costs 2,500 denarii of bed",
      abs(S.Sim.NITRE_YIELD_T_PER_M2 - 0.0008) < 1e-12
      and abs(S.Sim.NITRE_COST_PER_M2 - 2.0) < 1e-12,
      (S.Sim.NITRE_YIELD_T_PER_M2, S.Sim.NITRE_COST_PER_M2))
check("saltpetre still cannot simply be bought - the beds are the answer, "
      "not a market share",
      S.Sim.MARKET_SHARE["saltpetre"] == 0.0, S.Sim.MARKET_SHARE["saltpetre"])
# --- DEVELOPER MARKERS IN PLAYER PROSE, THE SECOND TIME. A strip pass removed
# 1,108 `[AUDIT: ...]` markers from node notes after a first-time tester found
# one in the win condition itself. It matched that one phrase, and 22 nodes
# carried a DIFFERENT one - "[FIXED after independent audit: ...]" - which an
# outside player then found in a furnace description and reported as
# immersion-breaking. The markers are worth keeping; `note` is not where they
# belong. `_internal` is read by nothing in sim/engine.
#
# This check is deliberately about the SHAPE rather than a list of phrases,
# because the thing that failed twice was a phrase list.
_BRACKETED = __import__("re").compile(r"\[[^\]]{0,400}\]")
_DEV_WORDS = ("audit", "fixed after", "todo", "fixme", "xxx", "see job",
              "provenance", "heuristic", "my own", "treat as a floor")
_leaks = []
for _k, _n in sorted(NODES.items()):
    for _m in _BRACKETED.findall(_n.get("note") or ""):
        if any(_w in _m.lower() for _w in _DEV_WORDS):
            _leaks.append((_k, _m[:70]))
check("no node's player-facing note carries a bracketed developer aside - "
      "an outside player found '[FIXED after independent audit: ...]' in a "
      "furnace description after the first strip pass missed that phrase",
      _leaks == [], _leaks[:4])
check("...and the markers were moved rather than destroyed, so the "
      "provenance of an inferred edge is still recoverable",
      sum(1 for _n in NODES.values()
          if "FIXED after independent audit" in (_n.get("_internal") or "")) == 22,
      sum(1 for _n in NODES.values()
          if "FIXED after independent audit" in (_n.get("_internal") or "")))
check("nothing in the engine reads _internal, which is what makes it safe "
      "to keep developer notes there",
      not any("_internal" in open(os.path.join(HERE, "engine", _f)).read()
              for _f in ("core.py", "economy.py", "projects.py", "labour.py",
                         "society.py", "protocol.py", "cli.py", "fog.py",
                         "data.py")),
      "engine files mentioning _internal")

# --- THE SAME HOLE IN A SECOND COMMAND. `available`'s parser read bare words
# only, so `available all:true` - the spelling `help commands` itself gives -
# fell through to the subject branch and was used as a search string named
# "all:true", matching nothing, silently. The same hole swallowed limit:30,
# find:furnace and every other pair. `state full:true` has always taken this
# spelling, so a player who learned it there was right to expect it.
for _av, _want in (("available all", {"cmd": "available", "all": True}),
                   ("available all:true", {"cmd": "available", "all": True}),
                   ("available limit:30 offset:30",
                    {"cmd": "available", "limit": 30, "offset": 30}),
                   ("available find:furnace",
                    {"cmd": "available", "find": "furnace"})):
    check("'%s' is understood" % _av, _PT(_av)[0] == _want, _PT(_av)[0])
check("a bare subject is still a subject, not mistaken for a flag",
      _PT("available metallurgy")[0] == {"cmd": "available",
                                         "subject": "metallurgy"},
      _PT("available metallurgy")[0])

# --- THE HELP PROMISED SOMETHING THE CODE DELIBERATELY DOES NOT DO. auto_open
# opens a capability institution at a loss on purpose - a school takes 2,500 a
# year, hands back 800, and is where twelve of your scholars come from - while
# its help said it "will NOT open anything whose upkeep exceeds its takings".
# Two players on different civilisations each watched it open a loss-maker,
# checked the help, and reported the automation as broken. The code was right.
_ao = S._agent_dispatch(sim(civ="rome_100ad"), NODES, {"cmd": "policy"})
_ao_txt = str(_ao)
check("auto_open's help admits it opens the institutions that train people "
      "even at a loss, which is what it actually does",
      "at a loss" in _ao_txt and "scholars come from" in _ao_txt,
      [l for l in _ao_txt.split(".") if "auto_open" in l][:1])
check("...and still says what it leaves shut, the case the original "
      "sentence was written for",
      "left shut" in _ao_txt, "left shut")

# --- THREE PLAYERS, THREE CIVILISATIONS, THE SAME COMPLAINT. Norse, England
# and Rome each independently reported being carried into debt they had not
# decided to take on, and two of them found out what happens past the credit
# limit by losing a school and a collegium they had built decades earlier.
# `start` financed the gap between what a project costs and what the
# household has, silently, at up to twelve per cent. Borrowing to build is a
# real move and stays allowed; not being told was the bug.
_cr = sim(civ="england_1300")
_cr.capital = 1300.0
_cr_out = S._agent_dispatch(_cr, NODES, {"cmd": "start", "id": "identity_cover"})
check("starting a project you cannot cover in cash says you would be "
      "borrowing, what it costs a year, and how much room is left",
      _cr_out.get("ok") and _cr_out.get("on_credit", {}).get("you_would_borrow", 0) > 0
      and _cr_out["on_credit"].get("interest_rate_percent", 0) > 0
      and _cr_out["on_credit"].get("estimated_annual_interest", 0) > 0
      and _cr_out["on_credit"].get("no_one_advances_past", 0) > 0,
      _cr_out.get("on_credit"))
check("...and names what the creditors do there, which is take things you "
      "built long ago and had no debt against",
      "built long ago" in (_cr_out.get("on_credit", {})
                           .get("what_happens_there") or ""),
      (_cr_out.get("on_credit") or {}).get("what_happens_there"))
# --- BREAK: this block said "borrowed_now" and "you_will_owe" on the exact
# command that had not borrowed a denarius yet - credit only actually draws
# down at step resolution - and a Norse player read "borrowed now: 123.8"
# here, then "(none used)" on `money` in the very next command, and called
# it a ledger contradiction. It was. The numbers were always right; only the
# tense was a lie.
check("the credit warning reads as a forecast, not a completed action - "
      "nothing has actually been borrowed by 'start' itself",
      "forecast" in (_cr_out.get("on_credit", {})
                    .get("nothing_is_borrowed_yet") or "").lower(),
      (_cr_out.get("on_credit") or {}).get("nothing_is_borrowed_yet"))
_cr_money = S._agent_dispatch(_cr, NODES, {"cmd": "money"})
check("...and `money` agrees that no credit is actually in use the moment "
      "after 'start' returns it, matching the forecast framing above",
      _cr_money.get("of_that_limit_you_have_used") == "none",
      _cr_money.get("of_that_limit_you_have_used"))
_cr2 = sim(civ="england_1300")
_cr2.capital = 50_000.0
_cr2_out = S._agent_dispatch(_cr2, NODES, {"cmd": "start", "id": "identity_cover"})
check("a project you can pay for outright says nothing about credit",
      _cr2_out.get("ok") and "on_credit" not in _cr2_out,
      sorted(_cr2_out))

# --- THE RATE WAS ON THE SCREEN AND THE SUM NEVER WAS. `why` quoted "10% per
# attempt" and nothing else; a failure takes a flat 40% of the money and puts
# 40% of the hours back on the slate. An England player read the single digit
# as a small thing and lost 35,433 pence off a 141,824-pence project.
_fw = S._agent_dispatch(sim(civ="england_1300"), NODES,
                        {"cmd": "why", "id": "lead_metallurgy"})
check("why says what a failure costs, not only how likely one is",
      _fw.get("failure_costs", 0) > 0
      and abs(_fw["failure_costs"] - _fw["cost"]["total"] * 0.4) < 1.0,
      (_fw.get("failure_costs"), (_fw.get("cost") or {}).get("total")))
check("...and a work that cannot fail is not given an imaginary danger",
      S._agent_dispatch(sim(civ="england_1300"), NODES,
                        {"cmd": "why", "id": "identity_cover"}).get("failure_costs", 0) == 0
      if NODES["identity_cover"]["risk"] == 0 else True,
      NODES["identity_cover"]["risk"])

# --- THE HELP ADVERTISED A SPELLING THE PARSER DID NOT ACCEPT, and the
# failure was silent and expensive. `rush`'s own help says "add limit:N to
# cap it"; `limit:3` is not a number, so the token scan came back empty, no
# limit was set, and rush went on to begin everything startable. A Norse
# player who read the help, wanted three things, and typed exactly what they
# were told got twenty-one projects and every denarius of their credit. The
# safest-looking spelling of the most expensive command in the game was the
# one that removed the safety.
for _sp in ("rush 3", "rush limit:3", "rush limit 3", "rush limit=3"):
    check("'%s' caps the rush at three" % _sp,
          _PT(_sp)[0] == {"cmd": "rush", "limit": 3},
          _PT(_sp)[0])
check("a cap that does not parse is refused, not shrugged off into "
      "starting everything - the one typo a careful player can make must "
      "not be the typo that begins the whole tree",
      _PT("rush limit:abc")[0] is None
      and "not a number" in (_PT("rush limit:abc")[1] or ""),
      _PT("rush limit:abc"))
check("platinum is reachable the way its own note and the geography file "
      "both say it is, overland, without rounding the Cape",
      "exp_africa_circumnavigation" not in S.closure(NODES, "mat_platinum_bulk"),
      sorted(x for x in S.closure(NODES, "mat_platinum_bulk")
             if x.startswith("exp_")))
check("...and the goal no longer requires an age of exploration to reach a "
      "transistor: one trade route, not six voyages",
      sorted(x for x in S.closure(NODES, GOAL) if x.startswith("exp_"))
      == ["exp_trade_route_extend"],
      sorted(x for x in S.closure(NODES, GOAL) if x.startswith("exp_")))
check("the Colombian placers are still a route, just not the only one",
      "americas_south" in (GEO_MATS := S.load_geography()
                           ["located_materials"]["platinum"]["regions"])
      and "siberia_urals" in GEO_MATS,
      GEO_MATS)
check("mat_bulk_steel (on the critical path) is gated on mat_manganese "
      "through exactly one req_any option, no real alternative offered",
      NODES["mat_bulk_steel"]["req_any"] ==
      [{"group": "manganese_supply", "options": {"mat_manganese": 1.0}}],
      NODES["mat_bulk_steel"]["req_any"])
check("closure() catches it now: mat_manganese and its own "
      "prerequisite mat_pyrolusite are both required, where a pre-only "
      "walk leaves both out",
      {"mat_manganese", "mat_pyrolusite"} <= _p_need
      and not ({"mat_manganese", "mat_pyrolusite"} & _pre_only),
      (sorted({"mat_manganese", "mat_pyrolusite"} & _p_need),
       sorted({"mat_manganese", "mat_pyrolusite"} & _pre_only)))
# ONE DEFINITION OF A HARD EDGE, or the ordering schedules a requirement too
# late. closure() learned the single-option groups first and topo_order and
# critical_path did not, so mat_manganese was correctly called required and
# then sorted AFTER the mat_bulk_steel that requires it. All three read
# hard_pre() now.
check("the order the ENGINE receives puts the single-option dependency "
      "first - topo_stable in cli.py was the last place still reading `pre` "
      "alone, and brought mat_manganese out at 187 behind the "
      "mat_bulk_steel at 65 that cannot be built without it",
      (lambda o: o.index("mat_manganese") < o.index("mat_bulk_steel"))(
          PLANNER._repaired(NODES, GOAL, _p_order)),
      "engine-order manganese/bulk steel")
check("topo_order puts a single-option req_any dependency before the node "
      "that requires it, not after",
      (lambda o: o.index("mat_manganese") < o.index("mat_bulk_steel"))(
          S.topo_order(NODES, _p_need)),
      "mat_manganese/mat_bulk_steel ordering")
check("hard_pre never repeats an id, however a node names it - a "
      "duplicate inflates topo_order's in-degree past what the decrement "
      "can undo, and reports ten blameless nodes as a cycle",
      all(len(S.hard_pre(NODES, k)) == len(set(S.hard_pre(NODES, k)))
          for k in NODES),
      [k for k in sorted(NODES)
       if len(S.hard_pre(NODES, k)) != len(set(S.hard_pre(NODES, k)))][:5])
_syn_req = {
    "goal2":  {"pre": ["mandatory"], "req_any": [], "yrs": 0, "ph": 0, "_total_cost": 0},
    "mandatory": {"pre": [], "req_any": [{"group": "g1", "options": {"onlyroute": 1.0}}],
                  "yrs": 1, "ph": 0, "_total_cost": 10},
    "onlyroute": {"pre": [], "req_any": [], "yrs": 1, "ph": 0, "_total_cost": 5},
    "choice":    {"pre": [], "req_any": [{"group": "g2", "options": {"routeA": 1.0, "routeB": 1.0}}],
                  "yrs": 1, "ph": 0, "_total_cost": 5},
    "routeA":    {"pre": [], "req_any": [], "yrs": 1, "ph": 0, "_total_cost": 5},
    "routeB":    {"pre": [], "req_any": [], "yrs": 1, "ph": 0, "_total_cost": 5},
}
check("a single-option req_any group's target is pulled into "
      "closure() - the mandatory-dependency-in-disguise case",
      "onlyroute" in S.closure(_syn_req, "goal2"),
      S.closure(_syn_req, "goal2"))
_syn_req["goal2"]["pre"] = ["choice"]
check("a genuine req_any CHOICE is left alone - neither option of a "
      "two-way alternative is forced into the closure",
      "routeA" not in S.closure(_syn_req, "goal2")
      and "routeB" not in S.closure(_syn_req, "goal2"),
      S.closure(_syn_req, "goal2"))
# The acyclic check against the WHOLE real tree (not just this synthetic
# pair) needs `_cycle_on`, defined later in this file - see the check next
# to "the tree is acyclic on hard prerequisites" below.
# THE STAFFING LAYER, which is the one thing in a plan that the tech tree
# cannot supply. A node's prerequisites are other nodes; its demand for
# "eight trained scholars" is a demand on the household, and no amount of
# ordering the closure correctly satisfies it. Both civilisations' plans used
# to run out of horizon with quantum_solidstate_theory as the first blocked
# node - the cheapest node in the late programme, wanting eight scholars
# against a society whose lettered pool tops out at 5.9.
check("the planner names the institutions that train people, which the "
      "goal's own prerequisite closure never mentions",
      _p_staff and all(k not in _p_need for k in _p_staff)
      and "school_founded" in _p_staff and "academy_network" in _p_staff,
      _p_staff)
check("...and does not order them, which was measured and made Rome's run "
      "three centuries worse - 278,000 denarii of founding cost and "
      "perpetual upkeep against a household that starts with four hundred",
      all(k not in _p_order for k in _p_staff),
      [k for k in _p_staff if k in _p_order])
check("the staffing list is read from the same table staff_capacity() "
      "itself iterates, so the two cannot drift apart",
      all(k in {e[0] for e in S.Sim.STAFF_CAPACITY_SOURCES} for k in _p_staff),
      sorted(_p_staff))
check("every node staff_capacity() credits actually exists in the tree - "
      "bessemer_openhearth did not, so its sixty-five artisans were never "
      "once handed over",
      [e[0] for e in S.Sim.STAFF_CAPACITY_SOURCES if e[0] not in NODES] == [],
      [e[0] for e in S.Sim.STAFF_CAPACITY_SOURCES if e[0] not in NODES])
_p_zero = [k for k in _p_need if _p_c["slack"][k] <= 1e-6]
_p_pos = {k: i for i, k in enumerate(_p_order)}
check("every zero-slack (critical-path) node is ordered before every node "
      "that has room to wait",
      max(_p_pos[k] for k in _p_zero) < min(_p_pos[k] for k in _p_need
                                            if _p_c["slack"][k] > 1e-6),
      "critical nodes occupy positions 0-%d of %d" % (len(_p_zero) - 1, len(_p_order)))
check("the critical-path total the planner computes matches `validate`'s "
      "142-year figure for this tree",
      abs(_p_c["total"] - S.critical_path(NODES, GOAL)[0]) < 1e-6,
      (_p_c["total"], S.critical_path(NODES, GOAL)[0]))
# A strategy file this module writes must reach the engine with no node ever
# asked to start before its own prerequisite - the thing `load_strategy`'s
# own `topo_stable` exists to guarantee for ANY strategy file, not only this
# one, but the planner's raw CPM order is exactly the case that needs it:
# slack is not monotonic along an edge (see the comment in planner.py), so
# the unrepaired order has real violations, and this checks the repair that
# reaches the engine removes every one of them.
_p_path = os.path.join(ROOT, _PLAY_DIR, "planned_check.json")
PLANNER.write_strategy(_p_path, "test", [], PLANNER.interleave(
    _p_order, PLANNER.pick_side_branches(NODES, _p_need, _p_s, 12), 8))
_p_label, _p_full, _p_bounties = S.load_strategy(_p_path, NODES, GOAL)
_p_fullpos = {k: i for i, k in enumerate(_p_full)}
_p_violations = [(p, k) for k in _p_need for p in NODES[k]["pre"]
                 if p in _p_need and _p_fullpos.get(p, -1) > _p_fullpos.get(k, 10 ** 9)]
check("a plan this module writes never asks the engine to start something "
      "before its own prerequisite, once loaded the same way --strategy loads it",
      not _p_violations, _p_violations[:5])
check("the side branches a plan weaves in are all revenue-positive and none "
      "is a technical prerequisite of the goal",
      _p_extras is not None and all(
          k not in _p_need and NODES[k]["rev"] > NODES[k]["up"]
          for k in PLANNER.pick_side_branches(NODES, _p_need, _p_s, 12)),
      PLANNER.pick_side_branches(NODES, _p_need, _p_s, 12)[:5])

# A SEED IMPROVES TIES, IT DOES NOT OVERRIDE THE GRAPH. Proven on a tiny
# synthetic DAG rather than the real tree, because the real tree (checked
# directly) has no two unrelated nodes with identical slack AND identical
# earliest-start - the tie-break is real but the live data never exercises it,
# which is exactly the gap a synthetic case is for.
_syn = {
    "goal": {"pre": ["a", "b"], "yrs": 0, "ph": 0, "_total_cost": 0},
    "a":    {"pre": [],         "yrs": 1, "ph": 0, "_total_cost": 10},
    "b":    {"pre": [],         "yrs": 1, "ph": 0, "_total_cost": 10},
}
_syn_order1, _c1, _e1, _s1 = PLANNER.backward_plan(_syn, "goal", _p_s, seed_order=["b", "a"],
                                              side_branches=0)
_syn_order2, _c2, _e2, _s2 = PLANNER.backward_plan(_syn, "goal", _p_s, seed_order=["a", "b"],
                                              side_branches=0)
check("(setup) the synthetic pair is a genuine tie: equal slack and equal "
      "earliest start, with no dependency between them",
      _c1["slack"]["a"] == _c1["slack"]["b"] and _c1["es"]["a"] == _c1["es"]["b"],
      (_c1["slack"], _c1["es"]))
check("a seed order breaks a tie the critical path itself cannot call, "
      "without needing to change when the seed agrees with the default",
      _syn_order1.index("b") < _syn_order1.index("a")
      and _syn_order2.index("a") < _syn_order2.index("b"),
      (_syn_order1, _syn_order2))

# --- refine() MUST MEASURE WHAT --strategy ACTUALLY LOADS, not its own raw,
# unrepaired ~161-node order. The first version of refine() handed
# `cur_order` straight to `Sim()`, skipping the `topo_stable` repair
# `load_strategy` always applies - and since the raw CPM order has 132 real
# topological violations (see the comment after `cpm` in planner.py), that
# silently measured a different, broken order: a live check of one refine
# round went from 0/3 trials reaching the goal to 3/3 the moment this was
# fixed, against the IDENTICAL seeds and the identical starting order. This
# pins the fix: `_repaired` must agree with what `load_strategy` returns for
# the same order.
_p_repaired = PLANNER._repaired(NODES, GOAL, _p_order)
_p_label2, _p_expected, _p_b2 = S.load_strategy(
    PLANNER.write_strategy(os.path.join(ROOT, _PLAY_DIR, "refine_check.json"),
                           "test", [], _p_order),
    NODES, GOAL)
check("refine() measures a candidate order the same way --strategy loads it "
      "(full tree, topo_stable-repaired), not its own raw closure-only list",
      _p_repaired == _p_expected, (len(_p_repaired), len(_p_expected)))
