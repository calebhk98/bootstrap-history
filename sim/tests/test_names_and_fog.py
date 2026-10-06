"""Typed names resolve to ids, fog limits what is suggested, and `available` sorts and pages."""
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

# --- Commands that act on a technology resolve a typed name to its id.
reply = ask(game, cmd="why", id="Reaper-Binder")
check("a typed name resolves to the id, case and punctuation folded",
      reply.get("ok") and reply.get("id") == "ag2_reaper_binder", reply.get("error") or reply.get("id"))

printed_name = ask(game, cmd="why", id="ag2_balanced_ration").get("name")
reply = ask(game, cmd="why", id=printed_name)
check("a name copied verbatim off another screen resolves the same way",
      reply.get("ok") and reply.get("id") == "ag2_balanced_ration", (printed_name, reply.get("error")))

full_reply = ask(game, cmd="why", id="loom")
check("an ambiguous name is refused with the real ids to choose between",
      not full_reply.get("ok") and full_reply.get("error", "").count("(") >= 2
      and "tex_horizontal_loom" in full_reply["error"], full_reply.get("error"))

# --- `available` can be sorted and paged all the way through.
sorted_reply = ask(game, cmd="available", limit=10, sort="risk", reverse=True)
risks = [entry["risk"] for entry in sorted_reply["available"]]
check("available can be sorted by risk, reversed, all the way through the page",
      risks == sorted(risks, reverse=True), risks)
pretty_sorted = _RP("available", sorted_reply)
first_id, last_id = sorted_reply["available"][0]["id"], sorted_reply["available"][-1]["id"]
check("the printed table keeps the JSON's sort order rather than re-sorting back to cost",
      -1 < pretty_sorted.find(first_id) < pretty_sorted.find(last_id), (first_id, last_id, pretty_sorted))
plain_reply = ask(game, cmd="available", limit=3)
check("a plain page still defaults to cheapest first",
      [entry["cost"] for entry in plain_reply["available"]]
      == sorted(entry["cost"] for entry in plain_reply["available"]),
      [entry["cost"] for entry in plain_reply["available"]])
lines = _RP("available", plain_reply).splitlines()
staff_header = next(i for i, line in enumerate(lines) if "STAFF" in line)
staff_legend = next((i for i, line in enumerate(lines) if "STAFF is the standing people" in line), None)
check("the STAFF column has its legend within a few lines of the table, not a screen away",
      staff_legend is not None and staff_legend - staff_header - sum(
          1 for line in lines[staff_header + 1:staff_legend] if line.startswith("   ") and line.strip()) < 15,
      (staff_header, staff_legend))

# --- Fog: an ambiguous-name list never offers more than full visibility would,
# and on a fresh game offers strictly less (or the filter does nothing).
fogged = fogged_game()
fog_reply = ask(fogged, cmd="why", id="loom")
full_ids = set(re.findall(r"(\w+) \(", full_reply.get("error", "")))
fog_ids = set(re.findall(r"(\w+) \(", fog_reply.get("error", "")))
check("under fog, an ambiguous name never offers more candidates than full visibility would",
      fog_ids and fog_ids < full_ids, (sorted(fog_ids), sorted(full_ids)))

# The goal's name gets the one exception its id already has on `why`, and nothing widens it.
goal_why = ask(fogged, cmd="why", id=NODES[GOAL]["name"])
goal_start = ask(fogged, cmd="start", id=NODES[GOAL]["name"])
guess = ask(fogged, cmd="why", id="transistor")
check("why on the goal's exact printed name is the one thing fog answers",
      goal_why.get("ok") and goal_why.get("id") == GOAL, goal_why.get("error"))
check("...but the exception does not widen to other commands on the same name",
      not goal_start.get("ok") and "never heard of" in goal_start.get("error", ""), goal_start.get("error"))
check("...and a vague guess does not silently resolve to the goal",
      not guess.get("ok") and GOAL not in guess.get("error", "") and "aiming at" not in guess.get("error", ""),
      guess.get("error"))

# Fog leak: did-you-mean suggestions under fog must all be things the player has heard of.
unknown_reply = ask(fogged, cmd="why", id="aqueduct_survey")
suggestion_text = re.split(r"did you mean:", unknown_reply.get("error", ""), flags=re.IGNORECASE)[-1] \
    if re.search(r"did you mean:", unknown_reply.get("error", ""), re.IGNORECASE) else ""
suggestions = [suggestion.strip() for suggestion in suggestion_text.split(",") if suggestion.strip()]
check("a near miss under fog still gets a did-you-mean list to check",
      suggestions, unknown_reply.get("error"))
verified = [ask(fogged, cmd="why", id=suggestion) for suggestion in suggestions]
check("the did-you-mean list under fog only ever suggests things the player has heard of",
      all("never heard of" not in reply.get("error", "") for reply in verified),
      [(suggestion, reply.get("error")) for suggestion, reply in zip(suggestions, verified)
       if "never heard of" in reply.get("error", "")])

# --- Fog leak: `available`'s heard-of block must respect `find`. Reveal
# something, then search for nonsense.
heard = sim(civ="rome_100ad", manual=False)
heard.fog = True
heard.revealed = set()
ask(heard, cmd="start", id="units_standards")
for _ in range(2):
    heard.step()
nonsense = S._agent_available(heard, NODES, {"find": "zzzznonexistentxyz"})
unfiltered = S._agent_available(heard, NODES, {"limit": 50})
check("a search matching nothing startable does not also dump the generic heard-of list",
      not nonsense.get("heard_of_but_cannot_begin"), nonsense.get("heard_of_but_cannot_begin"))
check("...but the same heard-of list still shows up unfiltered when no search was asked for",
      unfiltered.get("heard_of_but_cannot_begin"), "empty heard-of list with no search active")
matching = S._agent_available(heard, NODES, {"find": "corpus"})
check("...and a search that DOES match a heard-of item still shows it",
      any(entry["id"] == "corpus_written" for entry in matching.get("heard_of_but_cannot_begin") or []),
      matching.get("heard_of_but_cannot_begin"))
