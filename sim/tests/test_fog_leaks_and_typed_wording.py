"""What fog may not leak (ids, prerequisites, enumeration through typos) and how typed commands are parsed and answered."""
from .harness import *  # noqa: F401,F403
from .agent_command_helpers import ask_agent, with_end_year, fogged_game, pristine_game
from sim.ui.proto.typed import parse_typed as _parse_typed

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

# 6. 0.999 years was refused and 1.99 was silently floored to one.
_fy_game = with_end_year(sim())
_fy = [ask_agent(_fy_game, cmd="step", years=1.99), ask_agent(_fy_game, cmd="step", years=1)]
check("a fractional number of years is refused, not silently rounded",
      _fy[0].get("ok") is False and _fy[1].get("ok") is True,
      [result.get("ok") or result.get("error") for result in _fy])

# --- the England weird-play tester -------------------------------------------
# 2. Every documented three-word buy lost its material to the typed parser, so
#    the whole mining subsystem was unreachable from the front door.
_mq = [_parse_typed("quote mine coal 500")[0], _parse_typed("quote coal 500")[0]]
check("the mining commands the help gives actually parse",
      all(command and command.get("material") == "coal" and command.get("n") == 500 for command in _mq), _mq)

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

# 4. downstream_count is asked for once a row now, so it cannot be the old
#    per-call closure over all 2,831 nodes.
_t0 = time.time()
for _k in list(NODES)[:400]:
    S.downstream_count(NODES, _k)
check("what rests on a node is cheap enough to put in a table",
      time.time() - _t0 < 1.0, "%.2fs for 400" % (time.time() - _t0))

# S23/S24, both in the typed front end.
_command, _error = _parse_typed("step 1; step 1")
check("two commands on one line are refused, not half-executed",
      _command is None and "one command per line" in (_error or ""), (_command, _error))
_upper = ask_agent(sim(civ="england_1300"), cmd="why", id=(_parse_typed("why AG2_MARLING")[0] or {}).get("id", "AG2_MARLING"))
check("a typed id is not case-sensitive when the game knows the right one",
      _upper.get("ok") is not False and "cost" in _upper, list(_upper)[:6])

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

# 4. Eleven ids carry capitals, among them the whole cap_pure_2N..9N purity
#    ladder on the critical path to germanium. Lowercasing what the player
#    typed made them unreachable from the typed front end.
_cap_game = sim()
_cap_replies = [ask_agent(_cap_game, cmd="why", id=(_parse_typed("why " + word)[0] or {}).get("id", word))
                for word in ("cap_pure_2N", "CAP_PURE_2N", "AG2_MARLING")]
check("ids that carry capitals are reachable, and case is not the player's problem",
      all(reply.get("ok") is not False and "cost" in reply for reply in _cap_replies),
      [reply.get("error") for reply in _cap_replies])

# --- the history notes must not rebuild the wall ----------------------------
# Every dated hazard now carries a real historical note and England has
# fifteen of them. Embedded whole, they took one `state full` reply to nearly
# twenty thousand bytes and one `risk` reply to seventeen thousand - which is
# the exact wall this interface was broken up to stop producing.
# Three fresh, unrelated sessions (proto() never shares a session file), so
# dispatched together and checked in original civ order under --jobs.
_big_civs = ("england_1300", "mexica_1500")
for _civ_big in _big_civs:
    _big_game = fogged_game(civ=_civ_big)
    _sf = [ask_agent(_big_game, cmd="state", full=True), ask_agent(_big_game, cmd="risk")]
    check("%s: state full stays readable" % _civ_big,
          len(json.dumps(_sf[0])) < 9000, "%d bytes" % len(json.dumps(_sf[0])))
    check("%s: risk stays readable" % _civ_big,
          len(json.dumps(_sf[1])) < 9000, "%d bytes" % len(json.dumps(_sf[1])))

# 3. Three distinguishable refusals were themselves the tree: real-and-heard-of,
#    real-but-unheard-of, and nonexistent. Sixteen plain-English guesses
#    correctly classified ten real technologies and five invented ones.
_tri_game = fogged_game(civ="england_1300")
_tri = [ask_agent(_tri_game, cmd="why", id=word) for word in ("telescope", "zzzzznotathing", "dynamo")]
_msgs = {(response.get("error") or "").split("Did you mean")[0].strip() for response in _tri}
check("a name you have not heard of and a name that does not exist read alike",
      len(_msgs) == 1, [message[:60] for message in _msgs])

# The help shows {"cmd":"labour","trade":"smith"}, so `labour trade smith` is
# the obvious typed reading of it - and was answered "no such trade: trade".
_syn_command, _syn_error = _parse_typed("labour trade smith")
check("the typed form of what the help shows actually works",
      _syn_error is None and (_syn_command or {}).get("trade") == "smith", (_syn_command, _syn_error))

# "Zero-cost nodes gate whole ages and are invisible... twice one of them was
# the only thing between me and a branch." The two digest lists deduplicated
# the wrong way round: the leverage column dropped anything that was also in
# the cheapest six, and the spine of this game is precisely the nodes that are
# both - free, zero-revenue, and holding up an age.
_dg = [ask_agent(fogged_game(), cmd="available")]
_lev = [x["id"] for x in (_dg[0].get("most_rests_on_these") or [])]
check("the leverage column is not emptied by things being cheap",
      len(_lev) >= 4, _lev)
_by_reach = sorted(_lev, key=lambda node_id: -S.downstream_count(NODES, node_id))
check("...and it really is the highest-leverage work available",
      _lev and S.downstream_count(NODES, _lev[0]) >= 50,
      [(node_id, S.downstream_count(NODES, node_id)) for node_id in _lev])

# 4. `step abc` silently advanced a year while step 0 and step -5 were refused.
_sa_command, _sa_error = _parse_typed("step abc")
check("a step that is not a number is refused, not silently taken as one",
      _sa_command is None and "not a number" in (_sa_error or ""), (_sa_command, _sa_error))
