"""Scenario: typed names, fog and `available` through a running game's command dispatch. The rules (name resolution, the
fog filter on candidates, sorting, paging and the heard-of search) are in test_names_and_fog."""
from .harness import *  # noqa: F401,F403


def ask(game, **command):
    return S._agent_dispatch(game, NODES, command)


def fogged_game():
    game = S.Sim(NODES, ORDER, random.Random(1), events=False, manual=True,
                 civ=S.load_civ("rome_100ad"), cfg={"start_kit": "poor_scholar"})
    game.goal, game.done_year = GOAL, {}
    game.fog, game.revealed = True, set()
    return game


game = sim()

# --- A typed name reaches the command as its id; an ambiguous one is refused with the real ids.
reply = ask(game, cmd="why", id="Reaper-Binder")
full_reply = ask(game, cmd="why", id="loom")
check("a typed name reaches `why` as its id, and an ambiguous name is refused with the real ids to choose between",
      reply.get("ok") and reply.get("id") == "ag2_reaper_binder"
      and not full_reply.get("ok") and full_reply.get("cause") == "ambiguous_name"
      and len(full_reply.get("choices", ())) >= 2 and "tex_horizontal_loom" in full_reply["choices"],
      (reply.get("error"), full_reply.get("error")))

# --- The printed `available` table keeps the JSON's order and carries its legend.
sorted_reply = ask(game, cmd="available", limit=10, sort="risk", reverse=True)
risks = [entry["risk"] for entry in sorted_reply["available"]]
pretty_sorted = _RP("available", sorted_reply)
first_id, last_id = sorted_reply["available"][0]["id"], sorted_reply["available"][-1]["id"]
check("the reply is sorted by risk, reversed, and the printed table keeps that order rather than re-sorting back to cost",
      risks == sorted(risks, reverse=True) and -1 < pretty_sorted.find(first_id) < pretty_sorted.find(last_id),   # presentation: the printed table
      (risks, first_id, last_id))
lines = _RP("available", ask(game, cmd="available", limit=3)).splitlines()
staff_header = next(i for i, line in enumerate(lines) if "STAFF" in line)
staff_legend = next((i for i, line in enumerate(lines) if "STAFF is the standing people" in line), None)
check("the STAFF column has its legend within a few lines of the table, not a screen away",   # presentation: layout
      staff_legend is not None and staff_legend - staff_header - sum(
          1 for line in lines[staff_header + 1:staff_legend] if line.startswith("   ") and line.strip()) < 15,
      (staff_header, staff_legend))

# --- Fog through dispatch: candidates, the goal's one exception, and did-you-mean.
fogged = fogged_game()
fog_ids = set(re.findall(r"(\w+) \(", ask(fogged, cmd="why", id="loom").get("error", "")))
full_ids = set(re.findall(r"(\w+) \(", full_reply.get("error", "")))
goal_why = ask(fogged, cmd="why", id=NODES[GOAL]["name"])
goal_start = ask(fogged, cmd="start", id=NODES[GOAL]["name"])
guess = ask(fogged, cmd="why", id="transistor")
check("under fog an ambiguous name offers fewer candidates than full visibility, and why on the goal's exact name is the "
      "one thing fog answers: not start, and not a vague guess",
      fog_ids and fog_ids < full_ids
      and goal_why.get("ok") and goal_why.get("id") == GOAL
      and not goal_start.get("ok") and goal_start.get("cause") == "never_heard_of"
      and not guess.get("ok") and guess.get("cause") == "never_heard_of" and GOAL not in guess.get("choices", ()),
      (sorted(fog_ids), sorted(full_ids), goal_why.get("error"), goal_start.get("error"), guess.get("error")))
unknown_reply = ask(fogged, cmd="why", id="aqueduct_survey")
suggestions = list(unknown_reply.get("choices") or [])
verified = [ask(fogged, cmd="why", id=suggestion) for suggestion in suggestions]
check("a near miss under fog gets a did-you-mean list that only ever suggests things the player has heard of",
      suggestions and all(each.get("cause") != "never_heard_of" for each in verified),
      [(suggestion, each.get("error")) for suggestion, each in zip(suggestions, verified)
       if each.get("cause") == "never_heard_of"] or unknown_reply.get("error"))

# --- Fog: `available`'s heard-of block respects `find` in a played game.
heard = sim(civ="rome_100ad", manual=False)
heard.fog = True
heard.revealed = set()
ask(heard, cmd="start", id="scientific_method")
for _ in range(2):
    heard.step()
nonsense = S._agent_available(heard, NODES, {"find": "zzzznonexistentxyz"})
unfiltered = S._agent_available(heard, NODES, {"limit": 50})
matching = S._agent_available(heard, NODES, {"find": "atomic"})
check("a search matching nothing does not dump the heard-of list, an unfiltered one still shows it, and a matching one shows its item",
      not nonsense.get("heard_of_but_cannot_begin") and unfiltered.get("heard_of_but_cannot_begin")
      and any(entry["id"] == "atomic_theory" for entry in matching.get("heard_of_but_cannot_begin") or []),
      (nonsense.get("heard_of_but_cannot_begin"), matching.get("heard_of_but_cannot_begin")))
