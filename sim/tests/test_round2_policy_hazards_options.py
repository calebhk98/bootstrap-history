"""round2_policy_hazards_options: regression checks, run individually with `--only round2_policy_hazards_options`."""
from .harness import *  # noqa: F401,F403

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
for _ in range(6):
    s_ab.step()
check("no path in the engine leaves a work mothballed but unknown",
      not (s_ab.mothballed - s_ab.done),
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
s.train("engineer", 2)          # training begun; nobody is ready for two years
r1 = S._agent_dispatch(s, NODES, {"cmd": "start", "id": node})
check("start accepts work nobody can do yet only WITH a warning naming the trade",
      r1["ok"] and "engineer" in r1.get("warning", ""), r1)

# --- D4: fractional staff counts are explained, not silently shown
s = sim(civ="rome_100ad", capital=400.0, manual=False, events=False)
s.step()
st = S._agent_state(s, NODES, {})
check("a fractional staff count comes with an explanation of what the fraction means",
      (abs(s.scholars - round(s.scholars)) < 0.02 and abs(s.artisans - round(s.artisans)) < 0.02)
      or bool(st.get("staff_are_fractional_because")),
      "scholars %.3f artisans %.3f" % (s.scholars, s.artisans))
s2 = sim(civ="rome_100ad")
st2 = S._agent_state(s2, NODES, {})
check("a whole-number staff carries no fraction footnote",
      st2.get("staff_are_fractional_because") is None, st2.get("staff_are_fractional_because"))

# --- F: say how the founder's hours were spent
s = sim(civ="rome_100ad", capital=400.0, manual=False, events=False)
ratios = []
for _ in range(6):
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
r, _, _ = proto([{"cmd": "risk"}], civ="norse_900ad")
kr = r[0]["knowledge_risk"]
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

# ============================================================================
# Section S: three nodes the machine list was missing. Honest prerequisites
# matter more than the node existing at all, especially for the LED, which
# is not a light bulb.
# ============================================================================

check("the light-emitting diode exists and sits behind a real semiconductor "
      "diode, not the lighting branch",
      "com_led" in NODES and "com_semiconductor_diode" in NODES["com_led"]["pre"],
      NODES.get("com_led", {}).get("pre"))
check("the LED needs the same purity/single-crystal semiconductor lineage a "
      "diode needs, not a shortcut around it",
      "com_led" in NODES and "junction_transistor" in S.closure(NODES, "com_led"),
      None)

check("the clothes dryer exists as its own node, distinct from the washing "
      "machine it builds on",
      "hom_clothes_dryer_electric" in NODES
      and NODES["hom_clothes_dryer_electric"]["id"] != "hom_washing_machine_electric"
      and "hom_washing_machine_electric" in NODES["hom_clothes_dryer_electric"]["pre"],
      NODES.get("hom_clothes_dryer_electric", {}).get("pre"))

check("the domestic freezer exists as its own node, distinct from the "
      "refrigerator it builds on",
      "hom_freezer_domestic" in NODES
      and NODES["hom_freezer_domestic"]["id"] != "hom_refrigerator_home_electric"
      and "hom_refrigerator_home_electric" in NODES["hom_freezer_domestic"]["pre"],
      NODES.get("hom_freezer_domestic", {}).get("pre"))
# New work: a human-readable rendering (--pretty), the menu starting the game
# instead of describing how to, and `load` refusing a file that is not a
# save from this game.
# ============================================================================

def _run_agent(input_lines, extra_args=(), civ="rome_100ad", cwd=None):
    """Drive the real `agent` subcommand in a real subprocess, optionally with
    extra CLI flags (--pretty among them). Returns (stdout, stderr, returncode)."""
    cmd = [sys.executable, os.path.join(HERE, "simulator.py"), "agent", "--civ", civ] + list(extra_args)
    proc = subprocess.run(cmd, input="\n".join(json.dumps(command) for command in input_lines) + "\n",
                       capture_output=True, text=True, timeout=300, cwd=(cwd or ROOT))
    return proc.stdout, proc.stderr, proc.returncode


_PRETTY_CMDS = [
    {"cmd": "state"}, {"cmd": "available"}, {"cmd": "why", "id": "blast_furnace"},
    {"cmd": "money"}, {"cmd": "labour"}, {"cmd": "risk"},
    {"cmd": "step", "years": 1}, {"cmd": "hire", "trade": "smith", "n": 1},
    {"cmd": "quit"},
]

# --- I/N: the one guarantee the whole feature rests on. A script that only
# ever reads stdout must not be able to tell --pretty was even passed.
_out_plain, _err_plain, _rc_plain = _run_agent(_PRETTY_CMDS)
_out_pretty, _err_pretty, _rc_pretty = _run_agent(_PRETTY_CMDS, extra_args=["--pretty"])
_first_diff = next((i for i in range(min(len(_out_plain), len(_out_pretty)))
                    if _out_plain[i] != _out_pretty[i]), None)
check("stdout is byte-for-byte identical whether or not --pretty is passed",
      _rc_plain == 0 and _rc_pretty == 0 and _out_plain == _out_pretty,
      "plain %d bytes, pretty %d bytes, first differs at %s"
      % (len(_out_plain), len(_out_pretty), _first_diff))

_bad_lines = []
for _ln in _out_pretty.splitlines():
    try:
        json.loads(_ln)
    except ValueError:
        _bad_lines.append(_ln)
check("with --pretty on, every stdout line is still exactly one JSON object",
      not _bad_lines, _bad_lines[:3])

# --- N: the rendering actually renders something recognisable for each of
# state/available/why/money/labour/risk, and stays silent on stderr when
# nobody asked for it.
check("--pretty renders state as a position, to stderr",
      "YEAR" in _err_pretty and "RUNNING" in _err_pretty and "EMPLOY" in _err_pretty,
      _err_pretty[:200])
check("--pretty renders available as a table, to stderr",
      "AVAILABLE" in _err_pretty and "COST" in _err_pretty, "")
check("--pretty renders why as a page about one thing, to stderr",
      "COST:" in _err_pretty and "STATUS:" in _err_pretty, "")
check("--pretty renders money as a ledger, to stderr",
      "LEDGER" in _err_pretty, "")
check("--pretty renders labour readably, to stderr",
      "ON YOUR STAFF" in _err_pretty, "")
check("--pretty never mixes a Python dict repr into the risk rendering",
      "{'" not in _err_pretty, [line for line in _err_pretty.splitlines() if "{'" in line])
check("why does not print the missing-prerequisites list twice",
      _err_pretty.count("bellows_water_blown") <= 1 or "MISSING PREREQUISITES" not in _err_pretty,
      [line for line in _err_pretty.splitlines() if "bellows_water_blown" in line])
check("without --pretty, stderr carries no rendered reply (only the welcome banner)",
      "RUNNING (" not in _err_plain and "LEDGER" not in _err_plain, _err_plain[:200])

_out_kit, _err_kit, _ = _run_agent([{"cmd": "state"}, {"cmd": "quit"}],
                                   extra_args=["--pretty", "--kit", "equestrian"])
check("large numbers in the pretty rendering carry thousands separators",
      "100,000" in _err_kit or "100,000" in _err_kit.replace(",", "", 0), _err_kit[:300])

# --- 2: the menu ends by starting the game, not by printing a command line
# and asking permission to run it. It must also honour the mortality choice
# made in the menu, which `agent` never had a flag for at all before this.
#
# The menu is now three doors (New game / Load a saved game / Options), not
# straight into the civilisation picker - see cli.py's cmd_menu. "1" at the
# MAIN MENU chooses New game; the civilisation picker, fog, kit, mortality
# and (new) horizon questions follow in that order.
_menu_dir = tempfile.mkdtemp()
# A FRESH CONFIG FILE, EXPLICITLY, so this check of the DEFAULT save
# location is not at the mercy of a config some earlier check in this same
# run (or a real person's own ~/.rome-sim-config.json) pointed elsewhere.
# ROME_SAVE_DIR is deliberately left unset for the same reason. IN A
# DIRECTORY OF ITS OWN, NOT _menu_dir: the New Game wizard now remembers its
# own answers as next time's defaults (civilisation/kit/fog/mortality/
# horizon moved off the Options screen - see settings.py's module docstring
# - onto "whatever was played last"), which means finishing the wizard
# below writes this config file once, and _menu_dir is also the directory
# the "nothing beside the source" check just below reads back - a config
# file is not a game save, but it would still be a .json file sitting in
# the same directory that check is examining, for a reason that has nothing
# to do with what that check exists to catch.
_menu_cfg_dir = tempfile.mkdtemp()
_menu_cfg = os.path.join(_menu_cfg_dir, "menu_default_cfg.json")
_menu_env = dict(os.environ, ROME_SIM_CONFIG=_menu_cfg)
_menu_env.pop("ROME_SAVE_DIR", None)
# THE MENU DROPS INTO `play`, NOT `agent`: a JSON prompt is the right front
# end for a script and the wrong one for the human the menu exists to greet;
# `play` speaks typed words over the same dispatcher. So the commands fed
# here are typed, and what comes back is the rendered view rather than JSON.
_menu_input = "1\n1\ny\n\ny\n\n\nstate\nquit\n"
_pm = subprocess.run([sys.executable, os.path.join(HERE, "simulator.py")],
                     input=_menu_input, capture_output=True, text=True, timeout=120,
                     cwd=_menu_dir, env=_menu_env)
check("the menu offers a main menu with New game, Load, and Options",
      all(option in _pm.stdout for option in ("New game", "Load a saved game", "Options")),
      _pm.stdout[:2000])
check("the menu says it is starting, not offering a command to run later",
      "Starting now" in _pm.stdout, _pm.stdout[-500:])
check("the menu names a resumable --session file ending in .json",
      "--session" in _pm.stdout and ".json" in _pm.stdout, _pm.stdout[-500:])
# Saves live in ~/.rome-saves by default, not beside the source: eighty-nine
# of them had piled up in the repository root and a play tester said so.
_save_dir = os.path.join(os.path.expanduser("~"), ".rome-saves")
check("saves are written somewhere of their own, not beside the source",
      os.path.isdir(_save_dir)
      and not [filename for filename in os.listdir(_menu_dir) if filename.endswith(".json")],
      _save_dir)
_saved = ([filename for filename in os.listdir(_save_dir) if filename.endswith(".json")]
          if os.path.isdir(_save_dir) else [])
# The one this run chose, by name out of the banner, rather than "exactly one
# file in the directory" - the save directory is the user's and keeps every
# game they have played.
_named = [line.split("--session")[1].strip()
          for line in _pm.stdout.splitlines() if "--session" in line]
check("the menu's chosen session file actually exists on disk after playing",
      _named and os.path.exists(_named[0]), (_named[:1], len(_saved)))
check("the menu drops straight into a playable session, no extra prompt",
      _pm.returncode == 0 and "YEAR" in _pm.stdout and "RUNNING" in _pm.stdout,
      _pm.stdout[-300:])
check("the mortality choice made in the menu reaches the actual game",
      "and ageing" in _pm.stdout, _pm.stdout[-300:])
if _named and os.path.exists(_named[0]):
    os.remove(_named[0])
    _mp = _named[0] + ".meta.json"
    if os.path.exists(_mp):
        os.remove(_mp)

# --- PLAYER REQUEST #1: saves in a place that survives. ROME_SAVE_DIR
# overrides everything, including a config file's own save_dir.
_redir_dir = tempfile.mkdtemp()
_redir_cfg_dir = tempfile.mkdtemp()
_redir_cfg = os.path.join(_redir_cfg_dir, "cfg.json")
# Config says one place, ROME_SAVE_DIR says another - the environment
# variable has to win, for the player whose $HOME does not survive between
# terminal sessions but who CAN export one line into a shell profile that
# does.
json.dump({"save_dir": os.path.join(_redir_cfg_dir, "not_this_one")},
          open(_redir_cfg, "w"))
_redir_env = dict(os.environ, ROME_SAVE_DIR=_redir_dir, ROME_SIM_CONFIG=_redir_cfg)
_pr = subprocess.run([sys.executable, os.path.join(HERE, "simulator.py")],
                     input="1\n1\ny\n\nn\n\n\n\nquit\n", capture_output=True, text=True,
                     timeout=120, cwd=_redir_dir, env=_redir_env)
check("ROME_SAVE_DIR redirects the menu's save away from the config file's "
      "own save_dir, and away from the default",
      any(filename.endswith(".json") for filename in os.listdir(_redir_dir)),
      (_pr.stdout[-400:], os.listdir(_redir_dir)))

# --- the Options menu: a preference set from it is read back on the NEXT
# invocation, unprompted - the whole point of PLAYER REQUEST #1 being a
# config file and not just a flag.
_opt_dir = tempfile.mkdtemp()
_opt_cfg = os.path.join(_opt_dir, "cfg.json")
_opt_savedir = os.path.join(_opt_dir, "chosen_saves")
_opt_env = dict(os.environ, ROME_SIM_CONFIG=_opt_cfg)
_opt_env.pop("ROME_SAVE_DIR", None)
subprocess.run([sys.executable, os.path.join(HERE, "simulator.py")],
               input="3\n1\n%s\nb\nq\n" % _opt_savedir,
               capture_output=True, text=True, timeout=60, cwd=_opt_dir, env=_opt_env)
check("a save location chosen from the Options menu is written to a config "
      "file", os.path.exists(_opt_cfg), _opt_cfg)
_opt_cfg_read = json.load(open(_opt_cfg)) if os.path.exists(_opt_cfg) else {}
check("...and it is the directory the player actually typed",
      _opt_cfg_read.get("save_dir") == _opt_savedir, _opt_cfg_read)
_pm2 = subprocess.run([sys.executable, os.path.join(HERE, "simulator.py")],
                      input="3\nb\nq\n", capture_output=True, text=True, timeout=60,
                      cwd=_opt_dir, env=_opt_env)
check("...and a LATER invocation - no flag, nothing repeated - shows it back "
      "as the current save location, which is the whole ask: it must stick "
      "between invocations",
      _opt_savedir in _pm2.stdout, _pm2.stdout[-800:])

# --- "Load a saved game" lists what is in the save directory well enough to
# choose by: civilisation, year, how far along, and when it was last written.
_load_dir = tempfile.mkdtemp()
_load_cfg = os.path.join(_load_dir, "cfg.json")
_load_env = dict(os.environ, ROME_SAVE_DIR=_load_dir, ROME_SIM_CONFIG=_load_cfg)
subprocess.run([sys.executable, os.path.join(HERE, "simulator.py")], input="1\n1\nn\n\nn\n\n\n\nquit\n",
               capture_output=True, text=True, timeout=120, cwd=_load_dir, env=_load_env)
_pl_load = subprocess.run([sys.executable, os.path.join(HERE, "simulator.py")],
                          input="2\nb\nq\n", capture_output=True, text=True, timeout=60,
                          cwd=_load_dir, env=_load_env)
check("Load a saved game lists the civilisation and year of a save on disk",
      "AD" in _pl_load.stdout and
      any(civ_name in _pl_load.stdout for civ_name in
          ("Rome", "Trajan", "Han", "Viking", "Norse", "Edward", "Mexica")),
      _pl_load.stdout[-1200:])
check("...and how far along it is (a technology count, since this save has "
      "fog off and so gets a goal-progress fraction instead)",
      "toward Grown and alloy junction transistors" in _pl_load.stdout,
      _pl_load.stdout[-1200:])
check("...and roughly when it was last written",
      "ago" in _pl_load.stdout or "AD" in _pl_load.stdout, _pl_load.stdout[-1200:])
_pl_resume = subprocess.run([sys.executable, os.path.join(HERE, "simulator.py")],
                            input="2\n1\nstate\nquit\n", capture_output=True, text=True,
                            timeout=120, cwd=_load_dir, env=_load_env)
check("picking a save from the Load Game list actually resumes it, not a "
      "fresh game",
      "Resumed from" in _pl_resume.stdout, _pl_resume.stdout[:600])

# --- fog-on saves do NOT get the goal-progress fraction in the Load Game
# list: that number gives away the size of the whole tree, which fog exists
# to keep a player from knowing before they have built their way to it.
_fogload_dir = tempfile.mkdtemp()
_fogload_cfg = os.path.join(_fogload_dir, "cfg.json")
_fogload_env = dict(os.environ, ROME_SAVE_DIR=_fogload_dir, ROME_SIM_CONFIG=_fogload_cfg)
subprocess.run([sys.executable, os.path.join(HERE, "simulator.py")], input="1\n1\ny\n\nn\n\n\n\nquit\n",
               capture_output=True, text=True, timeout=120, cwd=_fogload_dir, env=_fogload_env)
_pl_fogload = subprocess.run([sys.executable, os.path.join(HERE, "simulator.py")],
                             input="2\nb\nq\n", capture_output=True, text=True, timeout=60,
                             cwd=_fogload_dir, env=_fogload_env)
check("a fogged save's Load Game entry does not leak how big the tree is",
      "toward Grown and alloy junction transistors" not in _pl_fogload.stdout
      and "technologies built" in _pl_fogload.stdout,
      _pl_fogload.stdout[-1200:])

# --- the in-game 'options' command: horizon changes stick across a plain
# `play --session` resume (no flag repeated), and mortality can only be
# turned ON, never off, from there.
_ig_dir = tempfile.mkdtemp()
_ig_session = os.path.join(_ig_dir, "ig.json")
_ig1 = subprocess.run([sys.executable, os.path.join(HERE, "simulator.py"), "play",
                       "--civ", "rome_100ad", "--session", _ig_session],
                      input="options\n1\n250\nb\nquit\n", capture_output=True, text=True,
                      timeout=120, cwd=_ig_dir)
check("the in-game options command changes the horizon",
      "now ends in 250 AD" in _ig1.stdout, _ig1.stdout[-600:])
_ig2 = subprocess.run([sys.executable, os.path.join(HERE, "simulator.py"), "play",
                       "--session", _ig_session],
                      input="state\nquit\n", capture_output=True, text=True,
                      timeout=120, cwd=_ig_dir)
check("...and a later plain `play --session` resume - no --horizon repeated "
      "- still honours it",
      "horizon at 250" in _ig2.stdout, _ig2.stdout[-1500:])
_ig3 = subprocess.run([sys.executable, os.path.join(HERE, "simulator.py"), "play",
                       "--session", _ig_session, "--horizon", "9"],
                      input="state\nquit\n", capture_output=True, text=True,
                      timeout=120, cwd=_ig_dir)
check("...while an EXPLICIT --horizon flag still overrides the remembered one",
      ("horizon at %d" % (100 + 9)) in _ig3.stdout, _ig3.stdout[-1500:])

_ig4 = subprocess.run([sys.executable, os.path.join(HERE, "simulator.py"), "play",
                       "--session", _ig_session],
                      input="options\n2\ny\nb\nstate\nquit\n", capture_output=True,
                      text=True, timeout=120, cwd=_ig_dir)
check("the in-game options command can turn mortality on mid-game",
      "and ageing" in _ig4.stdout, _ig4.stdout[-1200:])
_ig5 = subprocess.run([sys.executable, os.path.join(HERE, "simulator.py"), "play",
                       "--session", _ig_session],
                      input="state\nquit\n", capture_output=True, text=True,
                      timeout=120, cwd=_ig_dir)
check("...and that survives a resume, the ordinary save mechanism already "
      "carrying it (life_left/founder_alive/cfg.immortal are all "
      "SAVE_FIELDS)", "and ageing" in _ig5.stdout, _ig5.stdout[-800:])
check("the in-game options menu never offers to change civilisation, kit or "
      "fog - none of those are honest to change mid-game",
      not any(option in _ig1.stdout for option in
              ("change the civilisation", "change the kit",
               "change the starting", "turn fog")),
      [line for line in _ig1.stdout.splitlines() if "fog" in line.lower()])

# --- moving a save from the in-game options command actually relocates it,
# meta-sidecar included, and the old file is gone.
_mv_dir = tempfile.mkdtemp()
_mv_from = os.path.join(_mv_dir, "from.json")
_mv_to = os.path.join(_mv_dir, "to.json")
_mv = subprocess.run([sys.executable, os.path.join(HERE, "simulator.py"), "play",
                      "--civ", "rome_100ad", "--session", _mv_from],
                     input="options\n1\n300\nb\noptions\n3\n%s\nb\nquit\n" % _mv_to,
                     capture_output=True, text=True, timeout=120, cwd=_mv_dir)
check("moving a save from the in-game options command relocates the file",
      os.path.exists(_mv_to) and not os.path.exists(_mv_from),
      (os.listdir(_mv_dir), _mv.stdout[-400:]))
check("...and carries its remembered horizon along with it",
      os.path.exists(_mv_to + ".meta.json"), os.listdir(_mv_dir))

# =============================================================================
# THE PRINCIPLE: Options is for the APPLICATION, not for any one game. The
# main-menu Options screen holds save location, display width, rows per
# table, and whether the welcome/tutorial text prints - never per-game
# choices such as civilisation, starting kit, fog, mortality or horizon, by
# the owner's own words: "change where saves are, change language, change
# window size, etc? Not about each save, like fog or mortality?" Those five
# per-game defaults live in "whatever the New Game wizard was told last
# time", written back silently the moment a game actually starts (cli.py's
# _new_game), with no settings screen of their own; horizon and mortality
# stay mid-game-changeable through the in-game 'options' command.
# =============================================================================

_appopt_dir = tempfile.mkdtemp()
_appopt_cfg = os.path.join(_appopt_dir, "cfg.json")
_appopt_env = dict(os.environ, ROME_SIM_CONFIG=_appopt_cfg)
_appopt_env.pop("ROME_SAVE_DIR", None)
_appopt = subprocess.run([sys.executable, os.path.join(HERE, "simulator.py")],
                         input="3\nb\nq\n", capture_output=True, text=True,
                         timeout=60, cwd=_appopt_dir, env=_appopt_env)
check("the main-menu Options screen offers the application preferences",
      all(option in _appopt.stdout for option in
          ("save location", "display width", "rows per table",
           "welcome/tutorial")),
      _appopt.stdout[-1200:])
check("...and no longer offers the per-game defaults that used to live here - "
      "civilisation, starting kit, fog, and mortality are a playthrough's own "
      "business, decided when that game starts, not a standing preference",
      not any(option in _appopt.stdout for option in
              ("default civilisation", "default starting kit",
               "default fog of war", "default mortality",
               "default horizon")),
      _appopt.stdout[-1200:])

# --- display width: an explicit override set from Options sticks (same
# pattern as save location), and it actually changes how wide a line wraps,
# not just what the Options screen echoes back.
_dw_dir = tempfile.mkdtemp()
_dw_cfg = os.path.join(_dw_dir, "cfg.json")
_dw_env = dict(os.environ, ROME_SIM_CONFIG=_dw_cfg)
_dw_env.pop("ROME_SAVE_DIR", None)
subprocess.run([sys.executable, os.path.join(HERE, "simulator.py")],
               input="3\n2\n150\nb\nq\n", capture_output=True, text=True,
               timeout=60, cwd=_dw_dir, env=_dw_env)
_dw_cfg_read = json.load(open(_dw_cfg)) if os.path.exists(_dw_cfg) else {}
check("a display width set from Options is written to the config file",
      _dw_cfg_read.get("display_width") == 150, _dw_cfg_read)
_dw_saves = tempfile.mkdtemp()
_dw_env2 = dict(os.environ, ROME_SIM_CONFIG=_dw_cfg, ROME_SAVE_DIR=_dw_saves)
_dw_session = os.path.join(_dw_dir, "wide.json")
_dw_play = subprocess.run([sys.executable, os.path.join(HERE, "simulator.py"),
                           "play", "--civ", "rome_100ad", "--session", _dw_session],
                          input="quit\n", capture_output=True, text=True,
                          timeout=120, env=_dw_env2)
_dw_arrival_lines = [line for line in _dw_play.stdout.splitlines()
                     if line.strip().startswith("You arrive in")]
check("a wider display width actually produces a longer wrapped line than "
      "the old hardcoded 76 ever could",
      _dw_arrival_lines and len(_dw_arrival_lines[0]) > 76,
      _dw_arrival_lines)
from engine import cli as _CLI, settings as _SETTINGS
from engine import protocol as _protocol
_narrow_lines = _CLI._wrap("word " * 40, width=30, indent="   ").splitlines()
_wide_lines = _CLI._wrap("word " * 40, width=150, indent="   ").splitlines()
check("...and, directly: cli._wrap actually uses the width it is given "
      "(narrower wraps the same text into visibly more lines than wider)",
      len(_narrow_lines) > len(_wide_lines) and len(_wide_lines) >= 1,
      (len(_narrow_lines), len(_wide_lines)))
check("...and _apply_display_prefs is what carries an Options override into "
      "both cli._wrap's own default and protocol.DISPLAY_WIDTH - the one "
      "place every renderer reads it from, per protocol.py's own comment",
      (lambda: (_CLI._apply_display_prefs({"display_width": 222}),
               _CLI._DISPLAY_WIDTH == 222 and _protocol.DISPLAY_WIDTH == 222
               )[1])(),
      (_CLI._DISPLAY_WIDTH, _protocol.DISPLAY_WIDTH))
# Reset the module globals _apply_display_prefs just changed, so no later
# check in this file (many of which render through the same shared protocol
# module, in-process) is silently run at width 222 instead of the default.
_CLI._apply_display_prefs(dict(_SETTINGS.CONFIG_DEFAULTS))

# --- rows per table: a preference set from Options changes the default page
# size of a long, filtered `available` list - the exact "paging through long
# lists thirty at a time by hand" complaint this exists to fix.
_rpp_dir = tempfile.mkdtemp()
_rpp_cfg = os.path.join(_rpp_dir, "cfg.json")
json.dump({"rows_per_page": 4}, open(_rpp_cfg, "w"))
_rpp_saves = tempfile.mkdtemp()
_rpp_env = dict(os.environ, ROME_SIM_CONFIG=_rpp_cfg, ROME_SAVE_DIR=_rpp_saves)
_rpp_play = subprocess.run([sys.executable, os.path.join(HERE, "simulator.py"),
                            "play", "--civ", "rome_100ad", "--session",
                            os.path.join(_rpp_dir, "s.json")],
                           input="available find a\nquit\n", capture_output=True,
                           text=True, timeout=120, env=_rpp_env)
check("a 'rows per table' preference of 4 pages a filtered `available` list "
      "at 4 rows, not the old bare 30",
      "1-4 matching" in _rpp_play.stdout, _rpp_play.stdout[:1500])

# --- the welcome/tutorial text is a preference, default on (nothing changes
# for a player who has never touched Options), and off actually suppresses it.
_wt_on_dir = tempfile.mkdtemp()
_wt_on_saves = tempfile.mkdtemp()
_wt_on_env = dict(os.environ, ROME_SIM_CONFIG=os.path.join(_wt_on_dir, "nope.json"),
                  ROME_SAVE_DIR=_wt_on_saves)
_wt_on = subprocess.run([sys.executable, os.path.join(HERE, "simulator.py"),
                         "play", "--civ", "rome_100ad", "--session",
                         os.path.join(_wt_on_dir, "s.json")],
                        input="quit\n", capture_output=True, text=True,
                        timeout=120, env=_wt_on_env)
check("with no preference ever set, the welcome/tutorial text still prints "
      "on a new game - nothing changes for a player who has never opened "
      "Options", "five to start with" in _wt_on.stdout, _wt_on.stdout[:800])
_wt_off_dir = tempfile.mkdtemp()
_wt_off_cfg = os.path.join(_wt_off_dir, "cfg.json")
json.dump({"show_welcome": False}, open(_wt_off_cfg, "w"))
_wt_off_saves = tempfile.mkdtemp()
_wt_off_env = dict(os.environ, ROME_SIM_CONFIG=_wt_off_cfg, ROME_SAVE_DIR=_wt_off_saves)
_wt_off = subprocess.run([sys.executable, os.path.join(HERE, "simulator.py"),
                          "play", "--civ", "rome_100ad", "--session",
                          os.path.join(_wt_off_dir, "s.json")],
                         input="quit\n", capture_output=True, text=True,
                         timeout=120, env=_wt_off_env)
check("...and turning it off from Options actually suppresses it on a "
      "player's fifth new game, not just on the Options screen itself",
      "five to start with" not in _wt_off.stdout
      and "You arrive in" not in _wt_off.stdout,
      _wt_off.stdout[:800])
check("...while the session still starts and is still playable with it off",
      _wt_off.returncode == 0 and "Saved to" in _wt_off.stdout,
      _wt_off.stdout[-300:])

# --- BREAK: the merchant kit is quoted at 4,000 den, Han's price_index is
# 0.750, and the first playable screen said "You arrive in 100 AD with 3000
# cash" with no word anywhere connecting the two numbers. A blind Han
# playthrough picked the kit because it was the recommended middle income
# and then reported the 1,000-den gap as unexplained, twice, as both a
# balance worry and a trust issue. The arithmetic was always right; only
# the silence was a bug.
_mk_dir = tempfile.mkdtemp()
_mk_env = dict(os.environ, ROME_SIM_CONFIG=os.path.join(_mk_dir, "nope.json"),
               ROME_SAVE_DIR=tempfile.mkdtemp())
_mk_play = subprocess.run([sys.executable, os.path.join(HERE, "simulator.py"),
                           "play", "--civ", "han_china_100ad", "--kit", "merchant",
                           "--session", os.path.join(_mk_dir, "s.json")],
                          input="quit\n", capture_output=True, text=True,
                          timeout=120, env=_mk_env)
check("a civilisation whose price_index differs from Rome's explains the "
      "gap between the kit's quoted denarii and the cash actually arrived "
      "with, on the same screen that shows both numbers",
      "4000" in _mk_play.stdout and "0.75" in _mk_play.stdout
      and "Rome" in _mk_play.stdout,
      _mk_play.stdout[:1200])
# --- and Rome itself (price_index 1.0) says nothing extra: there is no gap
# to explain, and a sentence explaining a non-existent discrepancy would be
# its own new confusion.
_mkr_dir = tempfile.mkdtemp()
_mkr_env = dict(os.environ, ROME_SIM_CONFIG=os.path.join(_mkr_dir, "nope.json"),
                ROME_SAVE_DIR=tempfile.mkdtemp())
_mkr_play = subprocess.run([sys.executable, os.path.join(HERE, "simulator.py"),
                            "play", "--civ", "rome_100ad", "--kit", "merchant",
                            "--session", os.path.join(_mkr_dir, "s.json")],
                           input="quit\n", capture_output=True, text=True,
                           timeout=120, env=_mkr_env)
check("...while a civilisation at Rome's own prices gets no such sentence "
      "at all, since there is no gap to explain",
      "is quoted in Rome" not in _mkr_play.stdout, _mkr_play.stdout[:1200])

# --- none of this reaches `agent`: its JSON protocol, and the --pretty
# rendering alongside it, is a stable machine interface that must not vary
# with a human's own saved terminal preferences.
_agentpref_cfg = os.path.join(tempfile.mkdtemp(), "cfg.json")
json.dump({"display_width": 200, "rows_per_page": 2}, open(_agentpref_cfg, "w"))
_agentpref_env = dict(os.environ, ROME_SIM_CONFIG=_agentpref_cfg)
_ap = subprocess.run([sys.executable, os.path.join(HERE, "simulator.py"), "agent",
                      "--civ", "rome_100ad", "--pretty"],
                     input=json.dumps({"cmd": "available", "find": "a"}) + "\n"
                           + json.dumps({"cmd": "quit"}) + "\n",
                     capture_output=True, text=True, timeout=60,
                     env=_agentpref_env)
check("a saved display-width/rows-per-page preference never reaches `agent` "
      "- its --pretty rendering still pages at the old default of 30, "
      "regardless of what a human's own config file says",
      "1-30 matching" in _ap.stderr and "1-2 matching" not in _ap.stderr,
      _ap.stderr[:1200])

# --- the New Game wizard remembers its own last answers as next time's
# defaults, with no settings screen of its own - see settings.py's module
# docstring. Play once with non-default choices; a LATER invocation offers
# those same choices as the default, and accepting every default (blank)
# actually starts a game with them.
_rem_dir = tempfile.mkdtemp()
_rem_cfg = os.path.join(_rem_dir, "cfg.json")
_rem_saves = tempfile.mkdtemp()
_rem_env = dict(os.environ, ROME_SIM_CONFIG=_rem_cfg, ROME_SAVE_DIR=_rem_saves)
# civ 1 (han_china_100ad, not the hardcoded default_civ rome_100ad), fog OFF,
# kit 'merchant' (not the hardcoded default_kit poor_scholar), mortality ON,
# goal left at its default (the blank answer), horizon 321 - deliberately not
# what CONFIG_DEFAULTS starts with.
# TWO NEW WIZARD QUESTIONS LANDED AT ONCE, in different branches: goal
# selection (seventeen goals now, blank takes the default) and the horizon as a
# named-mode menu with "an exact number of years" as one more choice on it
# rather than the only one. 321 matches none of the four named presets, so it
# goes through that fifth option, exactly as a player asking for a number that
# is not named would. Both answers have to be in the script or the wizard
# consumes the horizon as the goal.
_rem1 = subprocess.run([sys.executable, os.path.join(HERE, "simulator.py")],
                       input="1\n1\nn\nmerchant\ny\n\n5\n321\nquit\n",
                       capture_output=True, text=True, timeout=120, env=_rem_env)
_rem_cfg_read = json.load(open(_rem_cfg)) if os.path.exists(_rem_cfg) else {}
check("finishing the New Game wizard remembers every answer as next time's "
      "default, with no Options screen involved",
      _rem_cfg_read.get("default_civ") == "han_china_100ad"
      and _rem_cfg_read.get("default_kit") == "merchant"
      and _rem_cfg_read.get("default_fog") is False
      and _rem_cfg_read.get("default_mortal") is True
      and _rem_cfg_read.get("default_horizon") == 321,
      _rem_cfg_read)
_rem2 = subprocess.run([sys.executable, os.path.join(HERE, "simulator.py")],
                       input="1\nb\nq\n", capture_output=True, text=True,
                       timeout=60, env=_rem_env)
check("...and the civilisation picker offers that remembered choice as its "
      "default the next time the wizard is opened",
      "default 1" in _rem2.stdout, _rem2.stdout[-800:])
_rem3 = subprocess.run([sys.executable, os.path.join(HERE, "simulator.py")],
                       input="1\n\n\n\n\n\n\n\nstate\nquit\n", capture_output=True,
                       text=True, timeout=120, env=_rem_env)
check("...and accepting every default (blank through all six questions) "
      "actually starts the remembered civilisation, not rome_100ad",
      "LATER HAN EMPIRE" in _rem3.stdout.upper(), _rem3.stdout[:2000])
# NOT A BARE 4,000: Han's own price index (0.75x Rome, printed on the WHERE
# AND WHEN screen) scales the merchant kit's nominal capital, so the honest
# check is "more than the poor_scholar default (400), a lot more" rather
# than the kit's own unscaled number.
import re as _re_rem
_rem3_capital = _re_rem.search(r"You arrive in \d+ AD with ([\d,]+)", _rem3.stdout)
check("...and the remembered kit (merchant, not poor_scholar) - far more "
      "starting capital than poor_scholar's 400, scaled by Han's own price "
      "index rather than a bare copy of the kit's nominal den figure",
      _rem3_capital and int(_rem3_capital.group(1).replace(",", "")) > 1000,
      _rem3.stdout[:2000])
check("...the remembered mortality (on)",
      "and ageing" in _rem3.stdout, _rem3.stdout[-900:])
check("...and the remembered horizon (321 years)",
      "421" in _rem3.stdout, _rem3.stdout[-900:])

# --- the in-game 'options' command (horizon, mortality mid-game) is
# untouched by any of the above - it is not part of the application's
# config file and was not moved.
check("the in-game options command still changes the horizon, unrelated to "
      "any of the application preferences above",
      "now ends in 250 AD" in _ig1.stdout, _ig1.stdout[-600:])

# --- the user: "I wanted agents to play under the play that we were just
# making". Everything built since the split went into the JSON protocol only,
# and `play` still understood six commands of its own. It must now reach the
# whole game, in typed words, and it must never answer a person in JSON.
_PLAY_DIR = "_playtest_tmp"
os.makedirs(os.path.join(ROOT, _PLAY_DIR), exist_ok=True)


def _play(lines, civ=None, extra=()):
    proc = subprocess.run([sys.executable, os.path.join(HERE, "simulator.py"), "play"]
                        + (["--civ", civ] if civ else []) + list(extra),
                        input="".join(line + "\n" for line in lines),
                        capture_output=True, text=True, timeout=240, cwd=ROOT)
    # BOTH STREAMS. A refusal printed on stderr is still a refusal the player
    # sees, and a check that reads only stdout silently passes a game that
    # started the wrong civilisation over the top of a save.
    return proc.stdout + proc.stderr, proc.returncode


_pl, _rc = _play(["state", "money", "labour", "risk", "policy", "available",
                  "hire smith 1", "step 1", "quit"])
check("typed play reaches the whole game, not six commands of its own",
      all(marker in _pl for marker in ("YEAR", "LEDGER", "ON YOUR STAFF", "AVAILABLE")) and _rc == 0,
      [marker for marker in ("YEAR", "LEDGER", "ON YOUR STAFF", "AVAILABLE") if marker not in _pl])
check("typed play never answers a person in JSON",
      '{"cmd"' not in _pl, [line for line in _pl.splitlines() if '{"cmd"' in line][:3])
_pl2, _ = _play(["available metallurgy", "quit"])
check("a typed narrowing of available works as the reply advertises it",
      "AVAILABLE" in _pl2 and "metallurgy" in _pl2.lower(), _pl2[:200])
_pl3, _ = _play(["frobnicate", "state", "quit"])
check("an unknown typed word is refused without ending the session",
      "no command called" in _pl3 and "YEAR" in _pl3, _pl3[:300])
_sess = "%s/typed.json" % _PLAY_DIR
# START FROM NOTHING. The first version of this check left its save behind, so
# the NEXT run of the suite resumed it and stepped three more years: it passed
# once and failed for ever after, on state left by itself.
if os.path.exists(os.path.join(ROOT, _sess)):
    os.remove(os.path.join(ROOT, _sess))
# --civ on the FIRST call, because that is the call that creates the game; the
# resume below deliberately omits it, which is the whole point of the check.
_pl4, _ = _play(["step 3", "quit"], civ="rome_100ad", extra=["--session", _sess])
_pl5, _ = _play(["state", "quit"], extra=["--session", _sess])
check("a typed game can be stopped and resumed from its own save file",
      "Resumed from" in _pl5 and "YEAR 103" in _pl5, _pl5[:300])
_pl6, _rc6 = _play(["state"])       # stdin ends without 'quit'
check("running out of input ends a typed game cleanly, not on a traceback",
      _rc6 == 0 and "Traceback" not in _pl6, _pl6[-200:])

# --- 3: `load` validates the file before touching the running game. `save`
# and `load` both refuse an absolute path (see the robustness checks above),
# so every file here lives in a relative scratch directory under ROOT, the
# same place a real player's save would land.
import shutil as _shutil
_LOADTEST_DIR = "_loadtest_tmp"
_loadtest_abs = os.path.join(ROOT, _LOADTEST_DIR)
os.makedirs(_loadtest_abs, exist_ok=True)


def _rel(name):
    return "%s/%s" % (_LOADTEST_DIR, name)


_good, _, _ = proto([{"cmd": "step", "years": 1}, {"cmd": "save", "file": _rel("sess.json")}])
check("a legitimate save from this game loads cleanly",
      _good[-1].get("ok") is True, _good[-1])

_bad_saves = {
    "not an object at all": "[1, 2, 3]",
    "an unrelated JSON object": json.dumps({"hello": "world"}),
    "missing required fields": json.dumps({"year": 100, "capital": 400}),
}
# Each iteration writes its OWN uniquely-named file (bad0.json, bad1.json, ...)
# before reading it back, so the file-writing stays sequential in this thread
# and only the three independent proto() reads - each a fresh session, each
# against its own file - are dispatched together under --jobs.
_bad_items = [(i, label, content) for i, (label, content) in enumerate(_bad_saves.items())]
_bad_names = []
for _i, _label, _content in _bad_items:
    _name = "bad%d.json" % _i
    open(os.path.join(_loadtest_abs, _name), "w").write(_content)
    _bad_names.append(_name)


def _load_bad(name):
    return proto([{"cmd": "state"}, {"cmd": "load", "file": _rel(name)}, {"cmd": "state"}])[0]


_bad_results = _par_map(_load_bad, _bad_names)
for (_i, _label, _content), _r in zip(_bad_items, _bad_results):
    ok_before, resp, ok_after = _r[0], _r[1], _r[2]
    check("load refuses %s with a clear message, not a crash" % _label,
          resp.get("ok") is False and "Traceback" not in resp.get("error", "")
          and len(resp.get("error", "")) < 400,
          resp)
    check("a refused load (%s) leaves the running game untouched" % _label,
          ok_before.get("year") == ok_after.get("year")
          and ok_before.get("capital") == ok_after.get("capital"),
          (ok_before.get("year"), ok_after.get("year")))

# a save for a civilisation other than the one currently running
_r, _, _ = proto([{"cmd": "save", "file": _rel("norse.json")}], civ="norse_900ad")
_r2, _, _ = proto([{"cmd": "load", "file": _rel("norse.json")}], civ="rome_100ad")
check("load refuses a save from a different civilisation",
      _r2[0].get("ok") is False and "civilisation" in _r2[0].get("error", ""), _r2[0])

# a save that refers to a node id the current tree does not have
_blob = json.load(open(os.path.join(_loadtest_abs, "sess.json")))
_blob["done"]["__set__"].append("this_node_does_not_exist_anymore")
json.dump(_blob, open(os.path.join(_loadtest_abs, "unknown_node.json"), "w"))
_r3, _, _ = proto([{"cmd": "state"}, {"cmd": "load", "file": _rel("unknown_node.json")}, {"cmd": "state"}])
check("load refuses a save that refers to a node the tree no longer has",
      _r3[1].get("ok") is False and "this_node_does_not_exist_anymore" in _r3[1].get("error", ""),
      _r3[1])
check("that refusal leaves the running game untouched too",
      _r3[0].get("year") == _r3[2].get("year"), (_r3[0].get("year"), _r3[2].get("year")))

# --- the Mexica break tester, six findings, one check each ------------------
# Every one of these was reproduced from the tester's own transcript before it
# was fixed; each check is the tester's repro, kept.

# 1. `work` earned wages as a chemist in a society whose `hire` and `labour`
#    both said chemists do not exist there.
_wk, _, _ = proto([{"cmd": "hire", "trade": "chemist", "n": 1},
                   {"cmd": "work", "trade": "chemist", "hours": 10},
                   {"cmd": "work", "trade": "scribe", "hours": 10}])
check("you cannot be paid for a trade this society does not have",
      _wk[0].get("ok") is False and _wk[1].get("ok") is False
      and _wk[2].get("ok") is True,
      [result.get("ok") for result in _wk])

# 2. Staff force-fired to zero with credit still to spare, and nothing logged.
# The tester's exact condition: staff on the books, capital NEGATIVE but only a
# third of the way into a credit line nobody has withdrawn. A household with
# credit left borrows and makes payroll; that is what credit is for.
# (a) A payroll the remaining credit COVERS costs you nobody but attrition.
s = sim(capital=6000.0)
s.policy["auto_hire"] = False
s.hire("smith", 2)
s.capital = -s.credit_limit() * 0.35
_before = sum(s.employees.values())
_room = s.capital + s.credit_limit() - (s.living_cost() - s.wage_bill())
s.step()
_after = sum(s.employees.values())
check("staff are not let go while there is still credit to pay them",
      _room > 0 and _after > _before * 0.95,
      "%.2f -> %.2f with %.0f still to spend against a %.0f payroll"
      % (_before, _after, _room, s.wage_bill()))

# (b) A payroll it only PARTLY covers costs you part of the staff, not all of
#     it. The tester's five went to zero in one step with two thirds of the
#     credit line untouched; what should happen is that you keep as many as
#     your remaining means will pay for.
s = sim(capital=6000.0)
s.policy["auto_hire"] = False
s.hire("smith", 5)
s.capital = -s.credit_limit() * 0.35
_b3 = sum(s.employees.values())
s.step()
check("an unaffordable payroll is trimmed to what you can pay, not emptied",
      0.5 < sum(s.employees.values()) < _b3,
      "%.2f -> %.2f" % (_b3, sum(s.employees.values())))

# ...and when they DO go, because there is genuinely no money left to borrow,
# it is said. The old code logged only in the branch that never happened.
s = sim(capital=6000.0)
s.policy["auto_hire"] = False
s.hire("smith", 5)
s.capital = -s.credit_limit() * 1.5
_b2 = sum(s.employees.values())
s.step()
check("losing staff you cannot pay is written in the log, never silent",
      sum(s.employees.values()) < _b2
      and any("cannot pay everyone" in message for _year, message in s.log),
      "%.2f -> %.2f, log %r" % (_b2, sum(s.employees.values()), s.log[-3:]))

# 3. state.living_cost was living_and_appearances PLUS the whole payroll, while
#    `money` reported the two separately, to the decimal.
_lc, _, _ = proto([{"cmd": "hire", "trade": "smith", "n": 3},
                   {"cmd": "state"}, {"cmd": "money"}])
_st, _mo = _lc[1], _lc[2]
_costs = (_mo.get("what_it_costs_you") or {})
check("state and money do not label the same money two different ways",
      abs(_st.get("living_cost", 0) - _costs.get("living_and_appearances", -1)) < 0.15
      and abs(_st.get("wage_bill", 0) - _costs.get("wages", -1)) < 0.15,
      "state %r / money %r" % ({field_name: _st.get(field_name) for field_name in ("living_cost", "wage_bill")},
                               {field_name: _costs.get(field_name) for field_name in ("living_and_appearances", "wages")}))

# 4. `path` under fog said "you have not discovered this" about a technology
#    the same session reported as done.
_pa, _, _ = proto([{"cmd": "path", "id": "identity_cover"}], fog=True)
check("path under fog gives the real reason, not a false one about discovery",
      _pa[0].get("ok") is False and "not been" in (_pa[0].get("error") or "")
      and "have not discovered" not in (_pa[0].get("error") or ""),
      _pa[0].get("error"))

# 5. The unknown-command hint named 10 of 27 real commands. (Fixed earlier;
#    kept because a hand-maintained list drifts again the moment one is added.)
_uc, _, _ = proto([{"cmd": "frobnicate"}])
check("the unknown-command hint names every command there is",
      all(command in (_uc[0].get("error") or "") for command in S.KNOWN_COMMANDS if command != "quit"),
      [command for command in S.KNOWN_COMMANDS if command not in (_uc[0].get("error") or "")])

# 6. 0.999 years was refused and 1.99 was silently floored to one.
_fy, _, _ = proto([{"cmd": "step", "years": 1.99}, {"cmd": "step", "years": 2}])
check("a fractional number of years is refused, not silently rounded",
      _fy[0].get("ok") is False and _fy[1].get("ok") is True,
      [result.get("ok") or result.get("error") for result in _fy])

# --- the Mexica play tester: a project's own accounting -----------------------
# Their three findings, each with the condition that produced it. All three need
# the SAME year to be short of a trade AND short of money, which is why none of
# them showed up in an ordinary run.


def _starved(cost_left, supply=0.02, arrears=0.8, capital=20000.0):
    """One project that cannot finish, in a year that is short of both the
    trade it needs and the money to pay for it."""
    starved_sim = sim(capital=capital)
    starved_sim.start_project("identity_cover")
    starved_sim.active["identity_cover"]["cost_left"] = cost_left
    _real = starved_sim.market_supply
    starved_sim.market_supply = lambda trade, _fallback=_real: _fallback(trade) * supply
    starved_sim.capital = -starved_sim.credit_limit() * arrears      # in arrears, inside the limit
    return starved_sim


# 1. Hours could be refunded twice - once for the trade shortage and again for
#    the money - and both refunds were worked out from the hours OFFERED rather
#    than the hours actually taken off. The tester's project ended with 581.5
#    hours left against a 450-hour total, which the display read out as "-67%
#    of your hours spent". Here: 612.5 against 500 before the fix.
s = _starved(9e5)
s.step()
_st = s.active.get("identity_cover") or {}
check("a project can never be given back more hours than it has spent",
      _st.get("ph_left", 0) <= NODES["identity_cover"]["ph"] + 1e-6,
      "%.1f left of a %.1f total" % (_st.get("ph_left", -1),
                                     NODES["identity_cover"]["ph"]))
check("an underfunded project says why it is underfunded",
      _st.get("underfunded_this_year") and "arrears" in (_st.get("why_underfunded") or ""),
      _st.get("why_underfunded"))

# 2. A shortage used to scale the PAYMENT rather than the instalment, so once
#    the balance was smaller than a year's instalment you paid a fraction of
#    what was left, every year, approaching zero without arriving - while
#    completion needs the bill under half a denarius. The tester watched one sit
#    at "71% done" for twenty-five years. Sixty years and 15.9 denarii still
#    owed, before the fix.
s = _starved(60.0, supply=0.001, arrears=0.0, capital=500000.0)
s.active["identity_cover"]["ph_left"] = 0.0
for _i in range(60):
    s.step()
    if "identity_cover" not in s.active:
        break
check("a small remaining bill is actually paid off, not approached for ever",
      "identity_cover" not in s.active,
      "%.4f den still owed after 60 years"
      % (s.active.get("identity_cover", {}).get("cost_left", 0.0)))

# --- the Mexica play tester: advice you cannot act on is not advice ----------
# They were told the answer to the Spanish was "walls, firearms, powerful
# friends, and copies of your work kept somewhere else", played 154 years with
# 269 startable things in view, and reported finding no hedge of any kind. The
# hedges were there. Nothing ever connected the words to the list.
# 11 SECONDS: forty-five years of a Mexica optimizer run before the advice it
# is checking even has anything to say. The three checks that share that setup
# move together, since re-running it for each would cost three times as much.
def _hazard_advice_names_hedges():
    hazard_sim = sim(civ="mexica_1500", manual=False)
    hazard_sim.fog = True
    hazard_sim.revealed = set()
    for _year in range(45):
        hazard_sim.step()
    counters = {node_id for node_id, _s2, _hazard_label in hazard_sim.HAZARD_COUNTERS["staff_loss"]}
    near = counters | {prereq_id for node_id in counters if node_id in NODES
                       for prereq_id in NODES[node_id]["pre"]}
    # Keep this focused on advice ordering rather than on which nodes the
    # revised civilization opening happens to reveal during the optimizer
    # run.  The player in the reported case had these candidate hedges in
    # view, so make that fixture condition explicit.
    hazard_sim.revealed.update(near)
    steps = (hazard_sim.hazard_advice("staff_loss")
             .get("you_could_begin_now_toward_it") or [])
    named = bool(steps) and all(
        step.get("id") and (step["can_begin_now"] or step.get("waiting_on"))
        for step in steps)
    ordered = [step["can_begin_now"] for step in steps] == sorted(
        (step["can_begin_now"] for step in steps), reverse=True)
    real = all(step["id"] in near for step in steps)
    return named and ordered and real, [
        (step["id"], step["can_begin_now"], (step.get("waiting_on") or "")[:40])
        for step in steps]

slow_check("a hazard names things in front of you that hedge against it, "
           "startable ones first, and every one really is a hedge",
           _hazard_advice_names_hedges)


# --- the England weird-play tester -------------------------------------------
# 1. The game printed its own resume command, `play --session england_1300.json`,
#    and then refused it: --civ defaulted to Rome and the save was England. A
#    save says what game it is; the command line should not have to.
_rs = "%s/resume.json" % _PLAY_DIR
if os.path.exists(os.path.join(ROOT, _rs)):
    os.remove(os.path.join(ROOT, _rs))
_r1, _ = _play(["step 2", "quit"], civ="england_1300", extra=["--session", _rs, "--fog"])
_r2, _ = _play(["state", "quit"], extra=["--session", _rs])       # no --civ, as printed
check("a save resumes without being told again which game it is",
      "Resumed from" in _r2 and "1302" in _r2, _r2[:400])
check("fog survives a save and reload, rather than opening the whole tree",
      "Fog of war is on" in _r2, [line for line in _r2.splitlines() if "og of war" in line])
_r3, _ = _play(["quit"], civ="rome_100ad", extra=["--session", _rs])
check("a --civ that contradicts the save is refused, not started over the top",
      "that save is a" in _r3 or "different civilisation" in _r3, _r3[:300])

# 2. Every documented three-word buy lost its material to the typed parser, so
#    the whole mining subsystem was unreachable from the front door.
_mq, _ = _play(["quote mine coal 500", "quote coal 500", "quit"], civ="england_1300")
check("the mining commands the help gives actually parse",
      _mq.count("to sink it") == 2, _mq[:400])

# --- the England break tester -------------------------------------------------
# 1. THE FOG EXPLOIT. `bounty` checked prerequisites before it checked whether
#    you had heard of the thing, so refusing a bounty on the goal printed the
#    goal's seven missing prerequisites by name. The tester crawled that error
#    recursively and recovered 134 hidden ids and the whole graph to the
#    transistor, in six rounds, with fog on throughout.
# GOAL, not a hardcoded node id: which node is the goal can change (the 1947
# device point_contact_transistor became a milestone on the way to the 1951
# one rather than the goal itself), and a check that names a node directly
# would then assert the goal's fog exception about a node that does not
# carry it.
_bt, _, _ = proto([{"cmd": "bounty", "id": GOAL},
                   {"cmd": "start", "id": GOAL},
                   {"cmd": "mothball", "id": GOAL},
                   {"cmd": "why", "id": GOAL}], fog=True)
# The PROPERTY, not the wording: no reply may contain the id of anything the
# player has not heard of. (`why` on the goal is answered now - the status line
# names the goal every turn - but it still may not name what the goal rests on.)
_GOAL_PRE = NODES[GOAL]["pre"]
_bt_text = json.dumps(_bt)
check("no command names a prerequisite of something you have not heard of",
      not any(prereq_id in _bt_text for prereq_id in _GOAL_PRE),
      [prereq_id for prereq_id in _GOAL_PRE if prereq_id in _bt_text])
check("...and only `why` answers about the goal at all; the rest still refuse",
      all(result.get("ok") is False for result in _bt[:3]) and _bt[3].get("ok") is True,
      [result.get("ok") for result in _bt])
check("...and what `why` says about the goal counts what it cannot name",
      "have not heard of" in json.dumps(_bt[3]), json.dumps(_bt[3])[:200])

# 2. The menu promises "Saved to X. Come back with ..."; a tester quit before
#    typing anything, found no file, followed the printed line, and landed in a
#    different civilisation's fresh game.
_sv = "%s/promised.json" % _PLAY_DIR
if os.path.exists(os.path.join(ROOT, _sv)):
    os.remove(os.path.join(ROOT, _sv))
_play(["quit"], civ="england_1300", extra=["--session", _sv])
check("a save the game promised exists even if you type nothing",
      os.path.exists(os.path.join(ROOT, _sv)), _sv)

# 3. state and the prompt both said 2,400 founder-hours free after 2,300 of
#    them had been sold, and then refused one more hour for having none.
# Derived from the pool, not a literal: this check hardcoded 2,300 hours and
# started failing the moment the founder's year came down to 2,000, because
# `work` correctly refused to sell hours that no longer existed.
_pool = sim().director_pool()
_sell = _pool - 100
_st2, _, _ = proto([{"cmd": "work", "trade": "scholar", "hours": _sell},
                    {"cmd": "state"}])
check("hours already sold for wages are not still reported as free",
      _st2[0].get("ok") is True and _st2[1]["founder_hours_available"] < 200,
      "%r free after selling %g of %g" % (_st2[1].get("founder_hours_available"),
                                          _sell, _pool))

# 4. auto_shed discards technologies you built - under fog the only score there
#    is - and it was on by default for a player.
check("nothing that deletes your work is on by default for a player",
      sim(manual=True).policy["auto_shed"] is False
      and sim(manual=False).policy["auto_shed"] is True,
      (sim(manual=True).policy["auto_shed"], sim(manual=False).policy["auto_shed"]))

# 5. You could sell every one of your 2,400 hours as a labourer and still
#    collect the full fee from a surgery you were demonstrably not in. The
#    practice is your own two hands; that was the same hours sold twice.
s = sim()
_rev_before = s.revenue()
_earned, _note = s.work_for_wages("labourer", s.director_pool())
check("hours sold as a labourer are not also spent practising medicine",
      _earned > 0 and _rev_before > 0 and s.revenue() < _rev_before * 0.05,
      "revenue %.1f -> %.1f having sold every hour" % (_rev_before, s.revenue()))
# ...and the player is told, rather than left to find it in the ledger. A
# tester measured a year of labour at 66 denarii against a 227 cost of living
# and a 259-a-year practice switched off, and called `work` self-destructive.
# It is, for a physician; the defect was that nothing said so.
check("selling your hours at a loss says so, and still happens",
      _note and "cost you" in _note, _note)
s2 = sim()
s2.work_for_wages("labourer", s2.director_pool() * 0.5)
check("selling half your hours costs you half the practice, not all of it",
      abs(s2.revenue() - _rev_before * 0.5) < _rev_before * 0.06,
      "%.1f against half of %.1f" % (s2.revenue(), _rev_before))

# 6. `buy mine` spent every denarius you had and handed back a fraction of the
#    mine you asked for, without asking. A command you typed is not a standing
#    order to spend everything.
_mn, _, _ = proto([{"cmd": "buy", "what": "mine", "material": "coal", "n": 500},
                   {"cmd": "state"}])
check("a mine you cannot pay for is refused, not part-bought with all your money",
      _mn[0].get("ok") is False and "Nothing was changed" in (_mn[0].get("error") or "")
      and _mn[1]["capital"] > 300,
      (_mn[0].get("error", "")[:80], _mn[1].get("capital")))

# --- the England normal-play tester -------------------------------------------
# 1. `train optician 1` destroyed the save. trades_created holds TRADE names and
#    was validated against the tech tree, so teaching any of the five trades
#    that gate chemistry, precision and electricity wrote a name the next load
#    refused as a missing technology. It cost that tester two runs and, by their
#    own measurement, 1,230 technologies.
_tr = "%s/trained.json" % _PLAY_DIR
if os.path.exists(os.path.join(ROOT, _tr)):
    os.remove(os.path.join(ROOT, _tr))
_play(["train optician 1", "quit"], civ="rome_100ad", extra=["--session", _tr])
_t2, _ = _play(["labour", "quit"], extra=["--session", _tr])
check("teaching a trade does not destroy the save",
      "Resumed from" in _t2 and "optician" in _t2 and "does not have" not in _t2,
      _t2[:300])

# 2. The one number that decides anything was the one `available` did not show.
#    The tester scripted 460 `why` calls to reconstruct revenue, upkeep and how
#    much rests on a node, and called competent play "writing a scraper".
_av, _, _ = proto([{"cmd": "available"}], fog=True)
_row = (_av[0].get("cheapest_six") or [{}])[0]
check("available shows what a thing earns, costs after, and what rests on it",
      all(field in _row for field in ("earns_per_year", "costs_per_year_after",
                              "how_much_rests_on_this")),
      sorted(_row))
check("available names the high-leverage things, not only the cheap ones",
      any(entry.get("id") in ("identity_cover", "units_standards")
          for entry in (_av[0].get("most_rests_on_these") or [])),
      [entry.get("id") for entry in (_av[0].get("most_rests_on_these") or [])])

# 3. Under fog the game said "there is no score but what you have built" while
#    an ending screen named a goal. The founder knows what a transistor is; fog
#    hides the society's tree, not the player's own intent. The NAME, never the
#    id - the id would hand back the prerequisite crawl.
_gh, _, _ = proto([{"cmd": "help"}, {"cmd": "state"}], fog=True)
_hw = json.dumps(_gh[0])
check("fog hides the road to the goal, not the goal",
      "transistor" in _hw.lower() and "point_contact_transistor" not in _hw
      and _gh[1].get("goal") is None and _gh[1].get("goal_in_words"),
      (_gh[1].get("goal"), _gh[1].get("goal_in_words")))

# 4. downstream_count is asked for once a row now, so it cannot be the old
#    per-call closure over all 2,831 nodes.
_t0 = time.time()
for _k in list(NODES)[:400]:
    S.downstream_count(NODES, _k)
check("what rests on a node is cheap enough to put in a table",
      time.time() - _t0 < 1.0, "%.2fs for 400" % (time.time() - _t0))

# 5. Losing a finished work was silent. A tester lost fourteen inside one
#    `step 12`, corpus_written and school_founded among them, with every
#    arrival named and no departure named.
s = sim(capital=-50000.0, manual=False)
s.done.add("fin_restaurant")
s.done.add("civ_road_paved")
s._done_changed()
_lost_before = set(s.done)
_ls, _, _ = proto([{"cmd": "start", "id": "hom_eraser_breadcrumb"},
                   {"cmd": "step", "years": 1}])
check("a step reports what left as well as what arrived",
      "lost" in _ls[-1], sorted(_ls[-1])[:12])

# 6. A quote read years ago is not what you pay: project_cost moves with
#    prices, the coinage and materials. The bill IS fixed when you start, and
#    nothing said what it was fixed at.
_q1, _, _ = proto([{"cmd": "why", "id": "hom_eraser_breadcrumb"},
                   {"cmd": "start", "id": "hom_eraser_breadcrumb"}])
check("starting something says what bill you have just taken on",
      _q1[1].get("the_bill_you_have_taken_on") is not None
      and _q1[0]["cost"].get("as_of_year"),
      (_q1[1].get("the_bill_you_have_taken_on"), _q1[0]["cost"].get("as_of_year")))

# 7. `suspicion` was replaced by `scandal` and then reported, unchanging, for
#    five hundred years. Two testers read a dead vestige as a broken mechanic.
_su, _, _ = proto([{"cmd": "state"}])
check("no dead field is reported every turn as though it were a mechanic",
      "suspicion" not in _su[0], [field_name for field_name in _su[0] if "susp" in field_name])

# --- the playtest-notes sweep -------------------------------------------------
# S1: every capital loss was written `capital *= x`, which is sign-blind. At
# minus a thousand denarii a sacking multiplied the DEBT by 0.4 and PAID the
# player six hundred, which made the deepest hole in the game the safest place
# to stand. Caught live twice in the notes: a Mexica sack -251 -> -100.5, an
# England thatch fire -629.2 -> -569.4.
s = sim()
s.capital = -1000.0
_gave = s.lose_capital(0.60)
check("a catastrophe never pays off a debt",
      s.capital == -1000.0 and _gave == 0.0,
      "capital %.1f, took %.1f" % (s.capital, _gave))
s.capital = 1000.0
s.lose_capital(0.60)
check("a catastrophe still takes its share of what you actually have",
      abs(s.capital - 400.0) < 1e-6, "%.1f" % s.capital)

# A1: hours_effective_this_year was `per - refunded`, and `per` is what was
# OFFERED, which may exceed what the project had left. The refunds are capped at
# spent_hours; this line was not, so a project reported 387.2 effective hours a
# year for four years while founder_hours_left never moved.
s = _starved(9e5)
_before_left = s.active["identity_cover"]["ph_left"]
s.step()
_st3 = s.active.get("identity_cover") or {}
check("hours reported as effective are hours that actually came off the work",
      _st3.get("hours_effective_this_year", 0)
      <= _before_left - _st3.get("ph_left", 0) + 1e-6,
      "reported %.1f, actually %.1f"
      % (_st3.get("hours_effective_this_year", -1),
         _before_left - _st3.get("ph_left", 0)))

# --- the strategy order must actually put first what the goal needs first ----
# Han China reached the transistor in 0% of runs, and the reason was never
# economic: a run sat at year 700 holding 3.37 MILLION denarii, 57 scholars and
# 99 artisans, having never built cap_heat_1100 - tier 0, 225 denarii, two
# artisans, a prerequisite of the goal, and startable at any moment. It was at
# index 589 in the order the optimizer works down, because topo_stable was told
# nothing about the 128 nodes the strategy names explicitly and so could never
# place anything that depended on them. 100% after the fix.
_lab_o, _order_o, _b_o = S.load_strategy("recommended", NODES, GOAL)
_idx_o = {node_id: i for i, node_id in enumerate(_order_o)}
_viol = [(node_id, prereq_id) for node_id in _order_o for prereq_id in NODES[node_id]["pre"]
         if _idx_o.get(prereq_id, -1) > _idx_o[node_id]]
check("no technology is ordered before something it requires",
      not _viol, "%d violations, e.g. %s" % (len(_viol), _viol[:3]))
_need_o = S.closure(NODES, GOAL)
_last = max(_idx_o[node_id] for node_id in _need_o if node_id in _idx_o)
check("everything the goal needs is near the front, not spread over the tree",
      _last < 400, "the last goal-critical node sits at index %d of %d"
                   % (_last, len(_order_o)))

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
# different reason. md2_sand_filtration has no prerequisite, is not
# auto-granted (its `ph` is not zero), and keeps real mining-establishment
# upkeep under the audit, so it is named directly rather than found.
s = sim(civ="england_1300", capital=50000.0)
_free = ["md2_sand_filtration"]
s.done.add(_free[0])
s._done_changed()
s.mothball_work(_free[0])
_cap = s.capital
s.restore_work(_free[0])
check("shutting a work down and reopening it is never free",
      _cap - s.capital >= NODES[_free[0]]["up"],
      "%s round trip cost %.0f against %.0f a year of upkeep"
      % (_free[0], _cap - s.capital, NODES[_free[0]]["up"]))

# S23/S24, both in the typed front end.
_tp, _ = _play(["why AG2_MARLING", "step 1; step 1", "state", "quit"],
               civ="england_1300")
check("a typed id is not case-sensitive when the game knows the right one",
      "COST:" in _tp, [line for line in _tp.splitlines() if "REFUSED" in line][:2])
check("two commands on one line are refused, not half-executed",
      "one command per line" in _tp and "YEAR 1300" in _tp, _tp[:200])

# S3. Naming a save file that is not there started a brand new default game
# and then wrote it over that filename. A tester nearly lost a forty-year
# England run to a mistyped path.
_missing, _rc_m = _play(["quit"], extra=["--session", "%s/no_such.json" % _PLAY_DIR])
check("a save file that is not there is a typo, not a new game",
      "do not know what game you meant" in _missing
      and not os.path.exists(os.path.join(ROOT, _PLAY_DIR, "no_such.json")),
      _missing[:200])

# A3. `why cap_heat_1300` on Han reported done:true and
# missing_prerequisites:["cap_heat_1100"] in the same object. Nothing a player
# reads should be able to say a thing they have is missing something.
_g3, _, _ = proto([{"cmd": "why", "id": "cap_heat_1300"}], civ="han_china_100ad")
check("nothing this society already has is also reported as missing something",
      _g3[0].get("done") is True and not _g3[0].get("missing_prerequisites")
      and _g3[0].get("held_without_building_it") is True,
      {field_name: _g3[0].get(field_name) for field_name in ("done", "missing_prerequisites",
                                  "held_without_building_it")})
# ...and the fix must NOT be to close the grant over its prerequisites, which
# would hand Tenochtitlan sextants and cementation steel for nothing, because
# maize hangs off "cross the Atlantic and found a trading post".
_mx = sim(civ="mexica_1500")
check("a society is not granted the route another society would take to it",
      "cementation_steel" not in _mx.done and "clock_pendulum" not in _mx.done
      and "fud_maize" in _mx.done,
      [node_id for node_id in ("fud_maize", "cementation_steel", "clock_pendulum")
       if node_id in _mx.done])

# --- knowing how, and actually running it ------------------------------------
# The user, on the deepest thing anyone said about this model: "you research
# the finance stuff and instantly make money -- but shouldn't that just unlock
# the ABILITY to do it? You research loans, now you can give out loans. What if
# you didn't give out any?" 1,337 nodes carried revenue and 1,256 of those also
# carried upkeep, so the tree already called them going concerns; the only
# thing missing was the act of opening the doors.
# Hire somebody first: a concern needs a pair of your hands to run it, which
# is the whole point of the staffing floor. Nobody runs a pawnshop alone from
# nowhere.
_v, _, _ = proto([{"cmd": "hire", "trade": "artisan", "n": 2},
                  {"cmd": "start", "id": "fin_restaurant"},
                  {"cmd": "step", "years": 6},
                  {"cmd": "money"},
                  {"cmd": "open", "id": "fin_restaurant"},
                  {"cmd": "money"}], kit="equestrian")
_before, _open, _after = _v[3], _v[4], _v[5]
check("working out how to do something does not by itself pay you",
      "fin_restaurant" not in (_before.get("where_the_money_comes_from") or {}),
      _before.get("where_the_money_comes_from"))
check("opening the doors is what pays you",
      _open.get("ok") is True
      and (_after.get("where_the_money_comes_from") or {}).get("fin_restaurant"),
      _after.get("where_the_money_comes_from"))

s2 = sim(capital=200000.0)
s2.hire("artisan", 2)
s2.done.add("fin_restaurant")
s2._done_changed()
_cap0 = s2.capital
s2.open_venture("fin_restaurant")
check("opening a concern costs stock and premises, not nothing",
      _cap0 - s2.capital >= NODES["fin_restaurant"]["up"],
      "%.0f to open against %.0f a year of running cost"
      % (_cap0 - s2.capital, NODES["fin_restaurant"]["up"]))

# You cannot run fifty businesses with three people.
s3 = sim(capital=1000000.0)
# BIG ENOUGH THAT ONE PERSON CANNOT RUN IT. The founder counts as a pair of
# hands now, so a small shop is exactly what they CAN open alone; the staffing
# rule is about scale, and this check has to test scale.
_heavy = [node_id for node_id in NODES if NODES[node_id]["rev"] >= 6000][:1]
if _heavy:
    s3.done.add(_heavy[0]); s3._done_changed()
    s3.artisans = 0.0
    _okh, _whyh = s3.open_venture(_heavy[0])
    check("a concern nobody is free to run cannot be opened",
          _okh is False and "nobody free" in (_whyh or ""), _whyh)

# Shutting it stops both sides and keeps the knowledge.
s4 = sim(capital=200000.0)
s4.hire("artisan", 2)
s4.done.add("fin_restaurant"); s4._done_changed()
s4.open_venture("fin_restaurant")
_rev_on, _up_on = s4.revenue(), s4.upkeep()
s4.mothball_work("fin_restaurant")
check("closing a concern stops what it earned and what it cost, both",
      s4.revenue() < _rev_on and s4.upkeep() < _up_on
      and "fin_restaurant" in s4.done,
      "rev %.0f->%.0f up %.0f->%.0f, still known %s"
      % (_rev_on, s4.revenue(), _up_on, s4.upkeep(), "fin_restaurant" in s4.done))

check("opening things for you is on for the optimizer and off for a player",
      sim(manual=True).policy["auto_open"] is False
      and sim(manual=False).policy["auto_open"] is True,
      (sim(manual=True).policy["auto_open"], sim(manual=False).policy["auto_open"]))

# What you run has to survive a save, or reloading quietly shuts your business.
_vs = "%s/ventures.json" % _LOADTEST_DIR
_rt, _, _ = proto([{"cmd": "hire", "trade": "artisan", "n": 2},
                   {"cmd": "start", "id": "fin_restaurant"},
                   {"cmd": "step", "years": 6},
                   {"cmd": "open", "id": "fin_restaurant"},
                   {"cmd": "save", "file": _vs},
                   {"cmd": "load", "file": _vs},
                   {"cmd": "state"}], kit="equestrian")
check("what you are running survives a save and reload",
      _rt[-1].get("concerns_you_run") == 1,
      "runs %r after a round trip" % _rt[-1].get("concerns_you_run"))

# --- a run that has stopped has to say so --------------------------------
# A weird-play tester's "most important finding": a run sat at exactly -924.5
# denarii for fifty years, completing nothing, while INSOLVENCY SETTLED fired
# once a decade for ever, and nothing anywhere said the run had effectively
# stopped or that it was escapable. It WAS escapable - they got out by working
# for wages - which is exactly why silence was the defect.
s = sim(civ="norse_900ad", capital=40000.0)
s.hire("smith", 3)
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
      sim(civ="norse_900ad").stall_diagnosis() is None,
      sim(civ="norse_900ad").stall_diagnosis())

# A one-character typo used to be answered with the words "did you mean: no idea".
_dm, _, _ = proto([{"cmd": "why", "id": "ag2_marlingg"}])
check("a typo in a name gets a real suggestion, not 'no idea'",
      "ag2_marling" in (_dm[0].get("error") or ""), _dm[0].get("error"))

# Two Roman-branded grants were still being handed free to every civilisation.
_ROMAN = ("_roman", "_rome", "annona", "insula", "societas", "collegium",
          "argentarii", "latifundi", "cursus", "pharos")
for _civ in ("han_china_100ad", "norse_900ad", "mexica_1500", "england_1300"):
    _sc = sim(civ=_civ)
    _bad = sorted(granted_name for granted_name in _sc.granted if any(roman_marker in granted_name for roman_marker in _ROMAN))
    check("%s is not handed Roman institutions for nothing" % _civ,
          not _bad, _bad)

# --- the Norse deadlock ------------------------------------------------------
# A Norse run ended at year 1500 with 31,068 denarii, 136 technologies and 1.6
# craftsmen, unable to build workshop_first because it needs 2 - while every
# institution that raises the staff ceiling (freedman_staff, collegium_licensed,
# school_founded) needs workshop_first first. You needed two craftsmen to build
# the place craftsmen work, and could never get to two. The Norse reached the
# goal in 0% of runs and it was never about money.
#
# The gate read self.artisans alone, so work you had already paid an outside
# shop to do did not count - and the refusal's own advice was to go and
# commission it.
s = sim(civ="norse_900ad", capital=100000.0)
# Prerequisites are tested before staff, so satisfy them: the point of this
# check is the staff gate, not the ladder above it.
for _p in NODES["workshop_first"]["pre"]:
    s.done.add(_p)
s._done_changed()
_ok0, _why0 = s.start_reason("workshop_first")
_blocked_on_staff = "craftsmen" in (_why0 or "")
s.commission("carpenter", 4000)
_ok1, _why1 = s.start_reason("workshop_first")
check("craftsmen you have under contract count toward what a project needs",
      _blocked_on_staff and "craftsmen" not in (_why1 or ""),
      "before: %s | after: %s" % ((_why0 or "")[:60], (_why1 or "")[:60]))
check("commission can unblock the gate whose own advice is to commission",
      s.craft_hands_available() >= 2.0,
      "%.2f craft hands from 4,000 contracted hours" % s.craft_hands_available())

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
for _ in range(60):
    s.step()
check("a long run never ends up running something it does not know",
      not _operating_subset_of_done(s), _operating_subset_of_done(s)[:5])

# The typo suggester searched the whole tree with fog on: `why transistor` gave
# back junction_transistor and point_contact_transistor, and the tester pointed
# out that two-letter prefixes would reconstruct the entire namespace.
_fg, _, _ = proto([{"cmd": "why", "id": "transistor"},
                   {"cmd": "why", "id": "vacuum"},
                   {"cmd": "why", "id": "semiconductor"}], fog=True)
check("a misspelling cannot be used to enumerate the tree through the fog",
      all("transistor" not in (result.get("error") or "").replace("'transistor'", "")
          and "vacuum_tube" not in (result.get("error") or "") for result in _fg),
      [result.get("error", "")[:80] for result in _fg])

# open/ventures are how technology turns into income and were missing from the
# command list; `open` on the founder's own practice denied it was theirs while
# `money` itemised it as their largest source of income.
_hc, _, _ = proto([{"cmd": "help", "topic": "commands"},
                   {"cmd": "open", "id": "med_cataract_couching"}],
                  civ="han_china_100ad")
check("every way of turning knowledge into income is in the command list",
      all(command in json.dumps(_hc[0]) for command in ("open", "ventures")),
      sorted((_hc[0].get("commands") or {}).keys())[:6])
check("the game does not deny that your own practice is yours",
      "already doing that" in (_hc[1].get("error") or ""), _hc[1].get("error"))

# --- round 5, the Han testers --------------------------------------------
# 1. THE WORST: resuming a save re-rolled the dice. Nothing saved the random
#    state, so a project sitting at its completion threshold re-rolled its
#    failure check on every resume: `start fin_bimetallism` then one `step`
#    per process oscillated 100%/60%/100%/60% for ever, burning hours and
#    money and never finishing. Reproduced 5 times out of 5. It also silently
#    re-drew every hazard and event a returning player would meet.
_rngdir = "%s/rng" % _PLAY_DIR
os.makedirs(os.path.join(ROOT, _rngdir), exist_ok=True)
_rs2 = "%s/dice.json" % _rngdir
if os.path.exists(os.path.join(ROOT, _rs2)):
    os.remove(os.path.join(ROOT, _rs2))


def _agent_session(cmds, first=False):
    argv = [sys.executable, os.path.join(HERE, "simulator.py"), "agent",
         "--session", _rs2]
    if first:
        argv += ["--civ", "han_china_100ad"]
    proc = subprocess.run(argv, input="\n".join(json.dumps(command) for command in cmds) + "\n",
                        capture_output=True, text=True, timeout=240, cwd=ROOT)
    return [json.loads(line) for line in proc.stdout.splitlines() if line.strip()]


_agent_session([{"cmd": "start", "id": "fin_bimetallism"}], first=True)
_finished_in = None
for _i in range(8):
    _o = _agent_session([{"cmd": "step", "years": 1}, {"cmd": "state"}])
    if "fin_bimetallism" not in (_o[-1].get("active") or {}):
        _finished_in = _i + 1
        break
check("a project finishes across resumes instead of oscillating for ever",
      _finished_in is not None,
      "still unfinished after 8 resumes" if _finished_in is None
      else "finished after %d" % _finished_in)

# 2. Founder hours could be spent twice: `train` wrote its own counter and
#    `work` read only the wage one, so 3,800 hours went into a 2,000-hour year.
_dh, _, _ = proto([{"cmd": "train", "trade": "machinist", "n": 2},
                   {"cmd": "train", "trade": "chemist", "n": 2},
                   {"cmd": "state"},
                   {"cmd": "work", "trade": "smith", "hours": 2000}],
                  civ="han_china_100ad", kit="equestrian")
check("hours spent teaching are not still available to sell",
      _dh[2]["founder_hours_available"] < 400 and _dh[3].get("ok") is False,
      "%r free, work accepted=%r" % (_dh[2].get("founder_hours_available"),
                                     _dh[3].get("ok")))

# 3. A bribe that buys nothing said so and charged 5,000 anyway.
_bb, _, _ = proto([{"cmd": "bribe", "amount": 5000},
                   {"cmd": "bribe", "amount": 5000},
                   {"cmd": "state"}], kit="equestrian")
check("a bribe that would buy nothing is refused, not charged",
      _bb[1].get("ok") is False and "Nothing was changed" in (_bb[1].get("error") or ""),
      _bb[1].get("error"))

# 4. Eleven ids carry capitals, among them the whole cap_pure_2N..9N purity
#    ladder on the critical path to germanium. Lowercasing what the player
#    typed made them unreachable from the typed front end.
_cap, _ = _play(["why cap_pure_2N", "why CAP_PURE_2N", "why AG2_MARLING", "quit"])
check("ids that carry capitals are reachable, and case is not the player's problem",
      _cap.count("COST:") == 3, [line for line in _cap.splitlines() if "REFUSED" in line][:2])

# 5. `available` truncated ids at 30 characters, so the longest could not be
#    copied out of the table that told you to use them.
_av, _ = _play(["available all", "quit"])
_longest = max(NODES, key=len)
check("no id is truncated in the table a player copies ids from",
      all(len(node_id) <= 30 or node_id in _av for node_id in [_longest]) or _longest not in _av,
      "longest id is %d chars" % len(_longest))

# 6. A year's hours must add up. Block 5b reused the name `pool`, clobbering
#    the project budget the report was computed against, and a year came to
#    2,900 hours out of 2,000.
s = sim(civ="rome_100ad", capital=400.0, manual=False, events=False)
for _ in range(4):
    s.step()
    _h = s.hours_this_year
    _tot = _h["wage_work"] + _h["teaching"] + _h["offered_to_projects"] + _h["unused"]
    check("a year's hours add up to a year (%d)" % s.year,
          _tot <= _h["available"] + 1.0, _h)

# 7. A project blamed the wrong resource for 275 years. `logarithms` sat at
#    "waiting on your hours" from 325 AD to the horizon with 1,900 idle founder
#    hours, while the real cause was 40,000 scribe-hours wanted from a society
#    that can field a few thousand. waiting_on was read off whatever the last
#    step happened to record instead of being worked out against today.
s = sim(civ="han_china_100ad", capital=500000.0)
for _p in NODES["logarithms"]["pre"]:
    s.done.add(_p)
s._done_changed()
s.hire("scholar", 2)
s.start_project("logarithms")
s.step()
_w = S._waiting_on(s, NODES, "logarithms", s.active["logarithms"], 0)
check("a stalled project names the resource actually stalling it",
      "scribe" in _w and "your hours" not in _w, _w)
check("...and says how far short the society is, in numbers",
      "can field" in _w or "booked" in _w, _w)

# A play tester watched their year grow from 2,000 hours to 6,090 with nothing
# saying why. It is deputies, not the founder working harder.
_hrs, _, _ = proto([{"cmd": "state"}])
check("state says where the founder's hours actually come from",
      (_hrs[0].get("where_your_hours_come_from") or {}).get("hours_each_deputy_adds"),
      _hrs[0].get("where_your_hours_come_from"))

# 8. `policy auto_hire on`, nothing else done at all, put a break tester into
#    ten years of debt bondage in ten steps - while the policy's own
#    description promises to "grow the staff toward what you can house and
#    pay". The whole careful affordability calculation was undone by a floor
#    beneath it: scale was max(0.10, ...), so a household with no surplus
#    still hired a tenth of its headroom.
s = sim(civ="han_china_100ad")
s.policy["auto_hire"] = True
for _ in range(10):
    s.step()
check("auto_hire on a poor household hires nobody and stays solvent",
      s.bondage_years_left == 0 and s.capital > 0,
      "capital %.0f, staff %.2f, bondage %s"
      % (s.capital, sum(s.employees.values()), s.bondage_years_left))
s = sim(civ="han_china_100ad", capital=100000.0)
s.policy["auto_hire"] = True
for _ in range(10):
    s.step()
check("...and on a rich one it actually hires",
      sum(s.employees.values()) > 1.0,
      "staff %.2f on 100,000" % sum(s.employees.values()))

# --- the persona is a persona, not a licence to do arithmetic ----------------
# The user, on identity_cover: "does anything building on it actually require
# it, or does it just make it so that you have social metrics that help? You
# could build a hot air balloon or bike without an identity, you are just more
# likely to be called a witch."
#
# They were right, and it was worse than that. identity_cover's whole
# implementation was +1.0 to the reputation floor and +400 to the credit
# limit; the "reduces all future suspicion" in its own description referred to
# a field that no longer exists. Its real function was to gate a quarter of
# the tree - and it was empirically the single node blocking England and
# Mexica from ever reaching the goal, because arithmetic_positional needs it
# and nothing else.
check("writing down zero does not require a respectable persona",
      "identity_cover" not in NODES["arithmetic_positional"]["pre"]
      and "identity_cover" not in NODES["scientific_method"]["pre"],
      (NODES["arithmetic_positional"]["pre"], NODES["scientific_method"]["pre"]))
check("...but being received by a patron, and publishing, still do",
      "identity_cover" in NODES["patron_local"]["pre"]
      and "identity_cover" in NODES["world_map"]["pre"],
      (NODES["patron_local"]["pre"], NODES["world_map"]["pre"]))


def _persona(has):
    persona_sim = sim(civ="england_1300")
    if has:
        run_it(persona_sim, "identity_cover")
    persona_sim.update_protection()
    return persona_sim


_no, _yes = _persona(False), _persona(True)
_n = NODES["hot_air_balloon"]
check("a persona makes the same strange work less alarming, as it says it does",
      _yes.alarm_of(_n) < _no.alarm_of(_n) * 0.85
      and _yes.protection > _no.protection,
      "alarm %.2f -> %.2f, protection %.3f -> %.3f"
      % (_no.alarm_of(_n), _yes.alarm_of(_n), _no.protection, _yes.protection))
check("...and you can still build the balloon without one",
      _no.alarm_of(_n) > 0 and "identity_cover" not in NODES["hot_air_balloon"]["pre"],
      NODES["hot_air_balloon"]["pre"])

# --- the history notes must not rebuild the wall ----------------------------
# Every dated hazard now carries a real historical note and England has
# fifteen of them. Embedded whole, they took one `state full` reply to nearly
# twenty thousand bytes and one `risk` reply to seventeen thousand - which is
# the exact wall this interface was broken up to stop producing.
# Three fresh, unrelated sessions (proto() never shares a session file), so
# dispatched together and checked in original civ order under --jobs.
_big_civs = ("england_1300", "mexica_1500", "rome_100ad")
_big_results = _par_map(
    lambda civ: proto([{"cmd": "state", "full": True}, {"cmd": "risk"}],
                      civ=civ, fog=True)[0], _big_civs)
for _civ_big, _sf in zip(_big_civs, _big_results):
    check("%s: state full stays readable" % _civ_big,
          len(json.dumps(_sf[0])) < 9000, "%d bytes" % len(json.dumps(_sf[0])))
    check("%s: risk stays readable" % _civ_big,
          len(json.dumps(_sf[1])) < 9000, "%d bytes" % len(json.dumps(_sf[1])))

# A hazard should report the harm it did to YOU, not the harm it would have
# done to somebody with something to lose: a tester with no staff and no money
# read "staff -45%, and 0 pence gone" three years running.
s = sim(civ="england_1300")
s.scholars = s.artisans = 0.0
s.employees = {}
s.capital = 0.0
s.year = 1348
s._shocks(1348)
_plague = [message for _year, message in s.log if "Black Death" in message]
check("a hazard that took nothing from you says so",
      not _plague or all("-45%" not in message or "nothing it could take" in message
                         for message in _plague),
      _plague)

# --- round 6, the England break tester ---------------------------------------
# 1. THE EXPLOIT THE VENTURE MODEL CREATED. `open` refused without supervisors
#    and then nothing ever looked again, so the tester hired five craftsmen,
#    opened eleven concerns in one turn, fired all six people and watched net
#    income RISE - seventeen concerns running against "EMPLOY: 0 people", and
#    the same loom still paying 435 a year in 1800 through the Black Death.
s = sim(civ="england_1300", capital=500000.0)
s.hire("artisan", 6)
_big = [node_id for node_id in NODES if 2000 <= NODES[node_id]["rev"] <= 9000][:4]
for _k in _big:
    s.done.add(_k)
s._done_changed()
_opened = [node_id for node_id in _big if s.open_venture(node_id)[0]]
_rev_staffed = s.revenue()
s.fire("artisan", 6)
s.step()
check("a concern nobody is left to watch stops trading",
      _opened and not s.operating and s.revenue() < _rev_staffed * 0.2,
      "revenue %.0f -> %.0f, still running %d"
      % (_rev_staffed, s.revenue(), len(s.operating)))
check("...and the game says which ones closed and why",
      any("nobody left to keep an eye on" in message for _year, message in s.log),
      [message for _year, message in s.log][-2:])

# 2. Failure risk fired correctly and announced nothing, so a tester watched
#    about 113 builds, expected nine failures and found no occurrence of
#    "fail", "abandon" or "lost" anywhere, and concluded the mechanic was dead.
s = sim(capital=5000000.0)
_risky = [node_id for node_id in NODES if NODES[node_id]["risk"] >= 0.15][:1][0]
_fails = 0
for _i in range(120):
    s.active[_risky] = dict(ph_left=0.0, yrs=99.0, spent=0.0, cost_left=0.0)
    s.done.discard(_risky)
    s._complete(_risky)
    if _risky in s.active:
        _fails += 1
        del s.active[_risky]
check("a failed attempt is announced, not silently absorbed",
      _fails > 0 and any("FAILED at" in message for _year, message in s.log),
      "%d failures in 120 at risk %.2f, logged %d"
      % (_fails, NODES[_risky]["risk"],
         sum(1 for _year, message in s.log if "FAILED at" in message)))

# 3. Three distinguishable refusals were themselves the tree: real-and-heard-of,
#    real-but-unheard-of, and nonexistent. Sixteen plain-English guesses
#    correctly classified ten real technologies and five invented ones.
_tri, _, _ = proto([{"cmd": "why", "id": "telescope"},
                    {"cmd": "why", "id": "zzzzznotathing"},
                    {"cmd": "why", "id": "dynamo"}],
                   civ="england_1300", fog=True)
_msgs = {(response.get("error") or "").split("Did you mean")[0].strip() for response in _tri}
check("a name you have not heard of and a name that does not exist read alike",
      len(_msgs) == 1, [message[:60] for message in _msgs])

# --- round 6, the England play tester ----------------------------------------
# 1. Bought people counted at full worth from the day of purchase, so the
#    training lag buy_slaves documents did nothing - and when a row finally
#    matured, step() added its capacity to self.artisans, which _resync_pools
#    then recomputed from scratch and threw away. A tester watched their
#    craftsmen fall from 35 to 3.8 at the moment the training finished.
s = sim(capital=500000.0)
run_it(s, "workshop_first", "freedman_staff")
s.buy_slaves(12)
_at_purchase = s.artisans
for _ in range(4):
    s.step()
_trained = s.artisans
s.manumit(12)
s._resync_pools()
check("people you buy are worth nothing until they have learned the work",
      _at_purchase < 0.5, "%.2f craftsmen the day 12 were bought" % _at_purchase)
check("...and are worth something once they have, and do not vanish",
      _trained > 7.0, "%.2f craftsmen after the training lag" % _trained)
check("freeing them is worth more than holding them, as the model claims",
      s.artisans > _trained * 1.3,
      "%.2f held -> %.2f freed" % (_trained, s.artisans))

# 2. arithmetic_positional wants 2,500 scribe-hours a year against a national
#    ceiling of 1,321, and sat at "81% spent" from 1309 to about 1440. The
#    engine knows this at start time.
_s_imp = sim(civ="england_1300")
for _p in NODES["arithmetic_positional"]["pre"]:
    _s_imp.done.add(_p)
_s_imp._done_changed()
_imp = S._agent_dispatch(_s_imp, NODES, {"cmd": "start", "id": "arithmetic_positional"})
check("starting work this society cannot staff says so at the time",
      _imp.get("ok") is True and "cannot supply the labour" in (_imp.get("but") or ""),
      _imp.get("but"))

# --- BREAK: the fix above ("Make the stated labour ceiling the real one")
# changed the TEST here to weigh commissioned hours - hours_you_can_call_on,
# market_supply plus contract_hours - but left the NUMBER PRINTED reading
# market_supply alone. A player who had commissioned any of the short trade
# saw `start` quote one ceiling for a project and `stuck` quote a higher one
# for the identical project a moment later: the exact disagreement that
# commit's own message said could not happen again ("the statement and the
# arithmetic cannot disagree"). Reproduced directly: commission 500 scribe-
# hours (the project is still short), then start logarithms.
s_lie = sim(capital=10000000.0)
for _p in NODES["logarithms"]["pre"]:
    s_lie.done.add(_p)
s_lie._done_changed()
s_lie.hire("scholar", 2)
s_lie.commission("scribe", 500.0)
_r_start = S._agent_dispatch(s_lie, NODES, {"cmd": "start", "id": "logarithms"})
_r_stuck = S._agent_dispatch(s_lie, NODES, {"cmd": "stuck"})
_but = _r_start.get("but") or ""
_stuck_why = ((_r_stuck.get("what_is_holding_you_up") or [{}])[0]
              .get("each_waiting_on", {}).get("logarithms", ""))
check("the ceiling `start` quotes for a short trade is the one `stuck` quotes a moment later",
      _but and _stuck_why and
      _but.split("field ")[1].split(" at most")[0]
      == _stuck_why.split("field ")[1].split(" at most")[0],
      (_but, _stuck_why))

# 3. The stat that ends the run had no warning and no help topic.
s = sim(capital=400.0)
s.eminence = s.cfg["eminence_danger"] * 0.9
s.step()
check("becoming conspicuous is said out loud before it kills you",
      any("BECOMING CONSPICUOUS" in message for _year, message in s.log),
      [message for _year, message in s.log][-2:])
_he, _, _ = proto([{"cmd": "help", "topic": "eminence"}])
check("...and there is a help topic for it",
      "eminence" in json.dumps(_he[0]).lower() and "no such topic" not in json.dumps(_he[0]),
      list(_he[0])[:4])

# Money is counted in the money of the place, and in ONE name for it. A break
# tester read "needs about 1959 pence, you have 612 den" in a single sentence:
# one clause localised from the payload, the next from the renderer.
_cur, _ = _play(["state", "money", "quote mine coal 500", "quit"], civ="england_1300")
check("an English game is counted in pence and never in denarii",
      " den " not in _cur and "denarii" not in _cur and "pence" in _cur,
      [line for line in _cur.splitlines() if " den " in line or "denarii" in line][:2])
_cur2, _ = _play(["state", "quit"], civ="han_china_100ad")
check("a Han game is counted in cash",
      "cash" in _cur2 and "denarii" not in _cur2,
      [line for line in _cur2.splitlines() if "denarii" in line][:2])

# The help shows {"cmd":"labour","trade":"smith"}, so `labour trade smith` is
# the obvious typed reading of it - and was answered "no such trade: trade".
_syn, _ = _play(["available subject metallurgy", "labour trade smith", "quit"],
                civ="england_1300")
check("the typed form of what the help shows actually works",
      "no such trade: trade" not in _syn and "AVAILABLE: 0 startable" not in _syn,
      [line for line in _syn.splitlines() if "REFUSED" in line][:2])

# `ventures` fell through to the generic dump and printed lists of dicts as
# raw Python.
_vr, _ = _play(["ventures", "quit"], civ="england_1300")
check("ventures is rendered as a table, not as raw Python",
      "CONCERNS" in _vr and "{'id':" not in _vr and "{\"id\":" not in _vr,
      [line for line in _vr.splitlines() if "{'" in line][:2])

# effective_scholars() has always counted the founder as one of the scholars;
# nothing counted them as a pair of hands, though the premise of the game is a
# person who knows how every one of these things is made. workshop_first wants
# two craftsmen, so a Norse run that could field one could never build the
# place craftsmen work.
s = sim(civ="norse_900ad")
check("the founder is one of the craftsmen as well as one of the scholars",
      s.craft_hands_available() >= 1.0 and s.effective_scholars() >= 1.0,
      "%.1f hands, %.1f scholars, with nobody hired"
      % (s.craft_hands_available(), s.effective_scholars()))
s2 = sim(civ="norse_900ad")
for _p in NODES["workshop_first"]["pre"]:
    s2.done.add(_p)
s2._done_changed()
s2.hire("carpenter", 1)
check("...so one hired hand is enough to raise your first workshop",
      s2.start_reason("workshop_first")[0],
      s2.start_reason("workshop_first")[1])

# --- BREAK: the pivot node of the entire game did nothing under --manual, the
# interactive protocol's only mode. school_founded's own text promises "+4
# scholars", _complete() added it with a bare self.scholars += 4, and the very
# next step() called _resync_pools() - unconditionally, every year - which has
# always recomputed self.scholars purely from self.employees and so overwrote
# the grant to whatever employees already held. A player who founded the
# school and then did anything else at all would have read a refusal a year
# later naming the same scholar shortfall the school was built to answer,
# with nothing saying why. Fixed by giving the grant its own durable record
# (_grant_staff) that _resync_pools adds back rather than discards.
s_gr = sim(capital=10000000.0, manual=True)
s_gr.done.add("school_founded")
s_gr._done_changed()
s_gr.operating.add("school_founded")
s_gr._grant_staff(scholars=4)
_after_grant = s_gr.scholars
s_gr.step()
check("founding the school still leaves you its scholars a year later",
      s_gr.scholars >= _after_grant - 1e-6,
      (_after_grant, s_gr.scholars))
check("...and a project that needed exactly what it granted can now start",
      s_gr.effective_scholars() >= 4.0,
      s_gr.effective_scholars())

# A break tester summed what the ledger listed - 7,101.9 - against a stated
# revenue of 6,738 and reported that the accounts do not add up. They were
# right: it showed the fifteen largest rows and nothing else, so smaller
# concerns, the workshop's own output, state funding and the market saturation
# that caps the whole figure were all invisible.
s = sim(civ="rome_100ad", manual=False)
for _ in range(120):
    s.step()
_src = s.revenue_sources()
check("the ledger's parts add up to the revenue it states",
      abs(sum(_src.values()) - s.revenue()) < 1.0,
      "rows %.1f against revenue %.1f" % (sum(_src.values()), s.revenue()))

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

# `quote` existed because a tester went from 38,151 denarii to zero on one
# unpriced mine command. A break tester then spent 27,500 - 68% of capital -
# on `buy forest 100`, with no price shown and no way to ask for one.
_qf, _, _ = proto([{"cmd": "quote", "what": "forest", "n": 100},
                   {"cmd": "quote", "what": "slaves", "n": 5}], kit="equestrian")
check("you can ask the price of a forest before you buy one",
      _qf[0].get("ok") is True and _qf[0].get("to_buy_it", 0) > 0,
      _qf[0].get("error") or _qf[0].get("to_buy_it"))
check("...and of people",
      _qf[1].get("ok") is True and _qf[1].get("to_buy_them", 0) > 0,
      _qf[1].get("error") or _qf[1].get("to_buy_them"))
s = sim(capital=100000.0)
_before_f = s.capital
_quoted = _qf[0]["to_buy_it"]
s.buy_forest(100)
check("the quoted price of a forest is the price you are charged",
      abs((_before_f - s.capital) - _quoted) < 1.0,
      "quoted %.1f, charged %.1f" % (_quoted, _before_f - s.capital))

# A taught trade still read "does not exist yet" alongside "exists here: True".
_tn, _, _ = proto([{"cmd": "train", "trade": "machinist", "n": 2},
                   {"cmd": "labour", "trade": "machinist"}], kit="equestrian")
_row = (_tn[1].get("trade") or {})
check("a trade you taught does not still say it does not exist",
      _row.get("exists_here") is True
      and "does not exist yet" not in (_row.get("note") or ""),
      (_row.get("exists_here"), (_row.get("note") or "")[:60]))

# "Zero-cost nodes gate whole ages and are invisible... twice one of them was
# the only thing between me and a branch." The two digest lists deduplicated
# the wrong way round: the leverage column dropped anything that was also in
# the cheapest six, and the spine of this game is precisely the nodes that are
# both - free, zero-revenue, and holding up an age.
_dg, _, _ = proto([{"cmd": "available"}], fog=True)
_lev = [x["id"] for x in (_dg[0].get("most_rests_on_these") or [])]
check("the leverage column is not emptied by things being cheap",
      len(_lev) >= 4, _lev)
_by_reach = sorted(_lev, key=lambda node_id: -S.downstream_count(NODES, node_id))
check("...and it really is the highest-leverage work available",
      _lev and S.downstream_count(NODES, _lev[0]) >= 50,
      [(node_id, S.downstream_count(NODES, node_id)) for node_id in _lev])

# A break tester multiplied out the factors `why` shows for clock_pendulum,
# got 4,747.6 against a stated 4,834, and called it the one card in the game
# whose arithmetic does not work. It was: project_cost multiplies in the
# scarce-material premium and the breakdown never listed it. A breakdown that
# omits a factor is worse than no breakdown, because it invites this exact
# check and then fails it.
_bad_math = []
for _civ_m in ("england_1300", "rome_100ad", "norse_900ad"):
    _sm = sim(civ=_civ_m)
    for _k in ("clock_pendulum", "hot_air_balloon", "blast_furnace", "lens_grinding"):
        if _k not in NODES:
            continue
        _e = S._node_explain(_sm, NODES, _k)["cost"]
        _prod = (_e["base_total"] * _e["civ_domain_factor"]
                 * _e["material_distance_factor"] * _e["opposition_factor"]
                 * _e["scarce_material_premium"] * _e["price_index"])
        if abs(_prod - _e["total"]) > max(2.0, _e["total"] * 0.005):
            _bad_math.append((_civ_m, _k, round(_prod, 1), _e["total"]))
check("every cost breakdown multiplies out to the total it states",
      not _bad_math, _bad_math[:3])

# --- round 7, the Rome weird-play tester -------------------------------------
# 1. `money`'s Net/yr omitted interest on arrears, with the interest RATE
#    printed two lines below it on the same screen. They read "+9.5 a year"
#    while capital fell 105, then 117, accelerating - a household in a debt
#    spiral being told it was recovering.
s = sim(civ="rome_100ad")
s.capital = -3000.0
_m = S._agent_dispatch(s, NODES, {"cmd": "money"})
check("the net counts interest on arrears, which is a cost like any other",
      _m["net_per_year"] < 0 and _m["what_it_costs_you"]["interest_on_arrears"] > 0,
      "net %.1f with %.1f of interest"
      % (_m["net_per_year"], _m["what_it_costs_you"]["interest_on_arrears"]))

# 2. "Told to my face I could take 6 more people, I took 7 with a different
#    verb." buy went round the feed/house/oversee cap that hire enforces.
s = sim(capital=1000000.0)
_room = s.household_room()
_ok_over = s.buy_slaves(int(_room) + 5)
check("buying people obeys the same household cap as hiring them",
      _ok_over == 0 and s.slaves == 0,
      "room %.2f, bought %s" % (_room, _ok_over))
check("...and buying within it still works",
      s.buy_slaves(max(1, int(_room) - 1)) > 0, "room %.2f" % _room)

# 3. Ten people bought showed as "ON YOUR STAFF: nobody" and "EMPLOY: 0
#    people" while the prompt said art 7, and IN TRAINING printed the trade as
#    the literal string "None" in fractions.
_hh, _ = _play(["buy slaves 5", "labour", "quit"], civ="rome_100ad",
               extra=["--kit", "equestrian"])
check("people you own appear in your household, not as nobody",
      "people you own" in _hh, [line for line in _hh.splitlines() if "STAFF" in line][:2])
check("a training row without a trade is not printed as None",
      "None x" not in _hh and "None" not in _hh.split("IN TRAINING")[-1][:200],
      _hh.split("IN TRAINING")[-1][:120])

# 4. `step abc` silently advanced a year while step 0 and step -5 were refused.
_sa, _ = _play(["step abc", "state", "quit"], civ="rome_100ad")
check("a step that is not a number is refused, not silently taken as one",
      "not a number" in _sa and "YEAR 100" in _sa,
      [line for line in _sa.splitlines() if "YEAR" in line][:2])

# 5. "A site is sacked" took 62% of a tester's money, restarted every project
#    and cut their people nearly in half, and printed only those five words -
#    against a player who owned no sites. The plague family had already been
#    taught to report the harm it actually did; this one had not.
s = sim(civ="mexica_1500", capital=50000.0)
s.year = 1519
for _ in range(6):
    s._shocks(s.year)
    s.year += 1
_sacks = [message for _year, message in s.log if "sacked" in message]
check("a sacking says what it took from you",
      _sacks and ("taken" in _sacks[0] or "nothing it could take" in _sacks[0]),
      _sacks[:1])
s2 = sim(civ="mexica_1500", capital=0.0)
s2.year = 1519
for _ in range(6):
    s2._shocks(s2.year)
    s2.year += 1
_sacks2 = [message for _year, message in s2.log if "sacked" in message]
check("...and says so plainly when it took nothing",
      not _sacks2 or "nothing it could take" in _sacks2[0], _sacks2[:1])

# 6. `bribe` sells protection, protection decides whether strange work reads as
#    learning or as sorcery, and it appeared on no screen and in no help topic.
_pr, _ = _play(["state", "bribe 700", "state", "quit"],
               civ="rome_100ad", extra=["--kit", "equestrian"])
_lines = [line for line in _pr.splitlines() if "STANDING:" in line]
check("protection is on the screen that shows your standing",
      len(_lines) >= 2 and "protection" in _lines[0] and _lines[0] != _lines[1],
      _lines[:2])
_hp, _, _ = proto([{"cmd": "help", "topic": "protection"}])
check("...and has a help topic of its own",
      "no such topic" not in json.dumps(_hp[0]), list(_hp[0])[:3])

_shutil.rmtree(_loadtest_abs, ignore_errors=True)
_shutil.rmtree(os.path.join(ROOT, _PLAY_DIR), ignore_errors=True)
