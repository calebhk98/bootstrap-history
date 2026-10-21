"""Scenario: people are whole, the scholar wall widens with institutions, fog cannot be rewound by a load, a command's
progress survives a closed pipe, and an England start warns of the credit it would use. The rules are in
test_people_attrition_scholars."""
from .harness import *  # noqa: F401,F403

# --- A played household: whole hires land exactly that many, and building the institutions auto_hire already
# credited widens the wall hire() enforces, which used to move only with literacy.
household = sim(capital=1e6)
ok_whole, _ = household.labour.hire("smith", 2)
widened = run_it(sim(capital=1e9), "interchangeable_parts", "power_grid")
check("a whole number of hires goes through and lands exactly that many, and building the institutions auto_hire already "
      "credited widens the scholar wall past what the tree's goal asks",
      ok_whole and household.employees.get("smith") == 2.0 and widened.labour.literate_capacity("scholar") > 20.0,
      (household.employees.get("smith"), widened.labour.literate_capacity("scholar")))

# --- SAVE INTEGRITY, JOB 2a: a load of an earlier save keeps everything this session has already seen, and a fresh
# resume sees only what the save recorded.
fogged = household
fogged.fog = True
fogged.revealed = {"identity_cover"}
fog_save = os.path.join(ROOT, _PLAY_DIR, "fog_rewind.json")
os.makedirs(os.path.dirname(fog_save), exist_ok=True)
S.save_state(fogged, fog_save)
fogged.reveal_from("workshop_first")        # something completes and reveals what it leads to
seen_after = set(fogged.revealed)
S.load_state(fogged, fog_save)              # the rewind to before paying
fresh = sim(civ="rome_100ad")
fresh.fog = True
fresh.revealed = set()
S.load_state(fresh, fog_save)
check("building under fog reveals what it leads to; loading an earlier save keeps it for this session, and a fresh "
      "resume sees only what the save file recorded",
      seen_after > {"identity_cover"} and seen_after <= fogged.revealed and fresh.revealed == {"identity_cover"},
      (sorted(seen_after), sorted(fogged.revealed), sorted(fresh.revealed)))

# --- SAVE INTEGRITY, JOB 2b: a command's progress is saved even when the reply cannot be delivered, against the real
# subprocess, a real closed pipe and a real file on disk.
pipe_session = os.path.join(ROOT, _PLAY_DIR, "closedpipe.json")
if os.path.exists(pipe_session):
    os.remove(pipe_session)
child = subprocess.Popen(
    [sys.executable, os.path.join(HERE, "simulator.py"), "agent", "--civ", "rome_100ad", "--seed", "1", "--session", pipe_session],
    stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, cwd=ROOT)
child.stdout.close()        # whatever the child writes from now on has nowhere to go
try:
    child.stdin.write(json.dumps({"cmd": "step", "years": 1}) + "\n")
    child.stdin.close()
except BrokenPipeError:
    pass
child.wait(timeout=60)
saved = json.load(open(pipe_session))
saved_year = saved.get("scenario", {}).get("year") if "scenario" in saved else saved.get("year")
check("a command's progress is saved even when the reply that describes it cannot be delivered because the reading "
      "end of the pipe is gone", saved_year == 101, saved_year)

# --- An England start that cannot be covered in cash says it would borrow; one that can says nothing; `why` states what
# a failure costs.
short = sim(civ="england_1300")
short.capital = 0.5 * short.project_cost("identity_cover")     # short of the project's bill, within the credit line
started = S._agent_dispatch(short, NODES, {"cmd": "start", "id": "identity_cover"})
on_credit = started.get("on_credit") or {}
money = S._agent_dispatch(short, NODES, {"cmd": "money"})
flush = sim(civ="england_1300")
flush.capital = 20 * flush.project_cost("identity_cover")
covered = S._agent_dispatch(flush, NODES, {"cmd": "start", "id": "identity_cover"})
why = S._agent_dispatch(short, NODES, {"cmd": "why", "id": "lead_metallurgy"})
check("a start short of cash reports the borrowing and `money` agrees no credit is in use yet; a start paid outright "
      "reports none; `why` says what a failure costs",
      started.get("ok") and on_credit.get("you_would_borrow", 0) > 0
      and money.get("of_that_limit_you_have_used") == "none"
      and covered.get("ok") and "on_credit" not in covered
      and why.get("failure_costs", 0) > 0 and abs(why["failure_costs"] - short.failure_bill("lead_metallurgy") * 0.4) < 1.0,
      (on_credit, money.get("of_that_limit_you_have_used"), sorted(covered), why.get("failure_costs")))
