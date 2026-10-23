"""Scenario (Complaint 640): what a fogged game may not leak (ids, prerequisites, enumeration through typos), answered through the agent protocol.

The typed-line parsing rules are in test_typed_front_end.py; a step of a fraction of a year is refused in
test_step_whole_years_rule. The size of a reply and the count of the leverage column were bounds tuned to one opening and
are not tested."""
from .harness import *  # noqa: F401,F403
from .agent_command_helpers import ask_agent, fogged_game, pristine_game

# 4. `path` under fog said "you have not discovered this" about a technology
#    the same session reported as done.
_pa = [ask_agent(fogged_game(), cmd="path", id="identity_cover")]
check("path under fog gives the real reason, not a false one about discovery",
      _pa[0].get("ok") is False and "not been" in (_pa[0].get("error") or "")
      and "have not discovered" not in (_pa[0].get("error") or ""),
      _pa[0].get("error"))

# 5. The unknown-command hint named 10 of 27 real commands. (Fixed earlier;
#    kept because a hand-maintained list drifts again the moment one is added.)
_uc = [ask_agent(pristine_game(), cmd="frobnicate")]
check("the unknown-command hint names every command there is",
      all(command in (_uc[0].get("error") or "") for command in S.KNOWN_COMMANDS if command != "quit"),
      [command for command in S.KNOWN_COMMANDS if command not in (_uc[0].get("error") or "")])

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
_bt_game = fogged_game()
_bt = [ask_agent(_bt_game, cmd="bounty", id=GOAL), ask_agent(_bt_game, cmd="start", id=GOAL),
       ask_agent(_bt_game, cmd="mothball", id=GOAL), ask_agent(_bt_game, cmd="why", id=GOAL)]
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

# 2. The one number that decides anything was the one `available` did not show.
#    The tester scripted 460 `why` calls to reconstruct revenue, upkeep and how
#    much rests on a node, and called competent play "writing a scraper".
_av = [ask_agent(fogged_game(), cmd="available")]
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
_gh_game = fogged_game()
_gh = [ask_agent(_gh_game, cmd="help"), ask_agent(_gh_game, cmd="state")]
_hw = json.dumps(_gh[0])
check("fog hides the road to the goal, not the goal",
      "transistor" in _hw.lower() and "point_contact_transistor" not in _hw
      and _gh[1].get("goal") is None and _gh[1].get("goal_in_words"),
      (_gh[1].get("goal"), _gh[1].get("goal_in_words")))

# A3. `why cap_heat_1300` on Han reported done:true and
# missing_prerequisites:["cap_heat_1100"] in the same object. Nothing a player
# reads should be able to say a thing they have is missing something.
_g3 = [ask_agent(sim(civ="han_china_100ad"), cmd="why", id="cap_heat_1300")]
check("nothing this society already has is also reported as missing something",
      _g3[0].get("done") is True and not _g3[0].get("missing_prerequisites")
      and _g3[0].get("held_without_building_it") is True,
      {field_name: _g3[0].get(field_name) for field_name in ("done", "missing_prerequisites",
                                  "held_without_building_it")})
# A one-character typo used to be answered with the words "did you mean: no idea".
_dm = [ask_agent(pristine_game(), cmd="why", id="ag2_marlingg")]
check("a typo in a name gets a real suggestion, not 'no idea'",
      "ag2_marling" in (_dm[0].get("error") or ""), _dm[0].get("error"))

# The typo suggester searched the whole tree with fog on: `why transistor` gave
# back junction_transistor and point_contact_transistor, and the tester pointed
# out that two-letter prefixes would reconstruct the entire namespace.
_fg_game = fogged_game()
_fg = [ask_agent(_fg_game, cmd="why", id=word) for word in ("transistor", "vacuum", "semiconductor")]
check("a misspelling cannot be used to enumerate the tree through the fog",
      all("transistor" not in (result.get("error") or "").replace("'transistor'", "")
          and "vacuum_tube" not in (result.get("error") or "") for result in _fg),
      [result.get("error", "")[:80] for result in _fg])

# 3. Three distinguishable refusals were themselves the tree: real-and-heard-of,
#    real-but-unheard-of, and nonexistent. Sixteen plain-English guesses
#    correctly classified ten real technologies and five invented ones.
_tri_game = fogged_game(civ="england_1300")
_tri = [ask_agent(_tri_game, cmd="why", id=word) for word in ("telescope", "zzzzznotathing", "dynamo")]
_msgs = {(response.get("error") or "").split("Did you mean")[0].strip() for response in _tri}
check("a name you have not heard of and a name that does not exist read alike",
      len(_msgs) == 1, [message[:60] for message in _msgs])
