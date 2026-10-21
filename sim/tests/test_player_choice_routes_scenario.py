"""SCENARIO: in a game a player can start the school by the paid route and exclude work from rush and the automatic
policies (Complaints 225, 226, 228, 229, 230). The tree-data rules are in `test_player_choice_routes`.

229: the school has a paid-labour alternative to buying and freeing people.
230: a persistent exclusion list honoured by rush, rush preview and the automatic policies.
"""
from .harness import *  # noqa: F401,F403
from sim.ui.proto.typed import parse_typed
from sim.engine.saveload import load_state, save_state


def _dispatch(test_sim, line):
    cmd, refusal = parse_typed(line)
    check("typed %r parses" % line, cmd is not None, refusal)
    return S._agent_dispatch(test_sim, NODES, cmd) if cmd else {}


# --- 229: the school without buying people
school = NODES["school_founded"]
alternatives = [option for group in school.get("req_any") or [] if "freedman_staff" in (group.get("options") or {})
                for option in group["options"] if option != "freedman_staff" and option in NODES]

paid_route = unopened_sim(capital=2_000_000)
for prereq in school["pre"] + alternatives[:1]:
    paid_route.done.add(prereq)
paid_route._done_changed()
check("school_founded can start with the paid alternative and without freedman_staff",
      "freedman_staff" not in paid_route.done and paid_route.can_start("school_founded"),
      paid_route.start_reason("school_founded"))
no_route = unopened_sim(capital=2_000_000)
for prereq in school["pre"]:
    no_route.done.add(prereq)
no_route._done_changed()
check("with neither route the school stays closed", not no_route.can_start("school_founded"))

# --- 230: exclusions
excluding = unopened_sim(capital=2_000_000)
startable = [node_id for node_id in excluding.order if excluding.can_start(node_id)]
check("set-up: something is startable", len(startable) >= 2)
victim = startable[0]
victim_category = NODES[victim]["cat"]
reply = _dispatch(excluding, "exclude %s" % victim)
check("exclude <id> is accepted", reply.get("ok") is True, reply)
check("...and listed", victim in str(reply.get("excluded")), reply)
check("...and recorded on the saved projects state", victim in excluding.state.projects.excluded)
preview = _dispatch(excluding, "rush preview")
check("rush preview does not list the excluded node as started",
      victim not in [row["id"] for row in preview.get("would_start", [])], preview.get("would_start"))
check("rush preview says what it left out and why",
      victim in [row["id"] for row in preview.get("excluded", [])]
      and all(row.get("why") for row in preview.get("excluded", [])), preview.get("excluded"))
forced = _dispatch(excluding, "rush limit:50")
check("rush does not start the excluded node",
      victim not in excluding.active and victim not in [row["id"] for row in forced.get("started", [])])

by_category = unopened_sim(capital=2_000_000)
_dispatch(by_category, "exclude category:%s" % victim_category)
check("excluding a category blocks every node in it from rush",
      not any(NODES[row["id"]]["cat"] == victim_category
              for row in _dispatch(by_category, "rush preview").get("would_start", [])))

by_trait = unopened_sim(capital=2_000_000)
_dispatch(by_trait, "exclude trait:buys_people")
check("a trait exclusion is recorded", "trait:buys_people" in by_trait.state.projects.excluded)
check("freedman_staff reports an exclusion reason under that trait",
      by_trait.exclusion_reason("freedman_staff") is not None)

cleared = _dispatch(excluding, "include %s" % victim)
check("include removes it", cleared.get("ok") is True and victim not in excluding.state.projects.excluded, cleared)
check("an unknown name is refused", _dispatch(unopened_sim(), "exclude no_such_node_anywhere").get("ok") is False)

round_trip = unopened_sim(capital=2_000_000)
_dispatch(round_trip, "exclude %s" % victim)
saved = os.path.join(ROOT, "_loadtest_tmp_exclusions.json")
try:
    save_state(round_trip, saved)
    restored = unopened_sim(capital=2_000_000)
    load_state(restored, saved)
    check("the exclusion list is saved with the game", victim in restored.state.projects.excluded)
finally:
    if os.path.exists(saved):
        os.remove(saved)

# automatic policies honour it
open_sim = unopened_sim(capital=2_000_000)
venture = next((node_id for node_id in NODES if open_sim.is_venture(node_id)
                and NODES[node_id]["rev"] > NODES[node_id]["up"]), None)
open_sim.done.add(venture)
open_sim._done_changed()
open_sim.state.projects.excluded.add(venture)
open_sim.auto_open_ventures()
check("auto_open skips an excluded concern", venture not in open_sim.operating)
