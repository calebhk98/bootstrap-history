"""round8g_display through running games: four scenarios, each a command reaching a rule the quick tests
(test_round8g_display) hold on built inputs. (1) capability institutions are told apart from ordinary concerns in
`why`, `ventures` and `mothball`; (2) a project's `why` while active names the pace throttle, and `train` and `why`
say a taught trade needs hiring; (3) `path` joins the route to what is startable and warns when the route pays for
nothing; (4) a Mexica founder cannot start the animal-drawn vehicles on turn one."""
from .harness import *  # noqa: F401,F403

# --- (1) capability institutions are told apart from ordinary concerns
_s_cap = sim(civ="rome_100ad", capital=5000000.0)
_wr_cap = S._agent_dispatch(_s_cap, NODES, {"cmd": "why", "id": "workshop_first"})
_wr_plain = S._agent_dispatch(_s_cap, NODES, {"cmd": "why", "id": "scientific_method"})
check("why flags a capability institution as needing to stay OPEN, not only built, and does not flag an ordinary prerequisite",
      bool(_wr_cap.get("this_is_a_capability_you_must_keep_open"))
      and _wr_plain.get("this_is_a_capability_you_must_keep_open") is None,
      (_wr_cap.get("this_is_a_capability_you_must_keep_open"), _wr_plain.get("this_is_a_capability_you_must_keep_open")))

_s_cap.done.update(["identity_cover", "tex_horizontal_loom"])
_s_cap._done_changed()
_vt_cap = S._agent_dispatch(_s_cap, NODES, {"cmd": "ventures"})
_cap_ids = [entry.get("id") for entry in (_vt_cap.get("capabilities_you_know_how_to_run_but_have_not_opened") or [])
            if isinstance(entry, dict)]
_ord_ids = [entry.get("id") for entry in (_vt_cap.get("you_know_how_but_have_not_opened") or []) if isinstance(entry, dict)]
check("ventures puts an idle capability institution in its own list and an ordinary idle business in the ordinary one",
      "identity_cover" in _cap_ids and "identity_cover" not in _ord_ids
      and "tex_horizontal_loom" in _ord_ids and "tex_horizontal_loom" not in _cap_ids, (_cap_ids, _ord_ids))

_s_cap.done.add("identity_cover")
_s_cap._done_changed()
_s_cap.open_venture("identity_cover")
_mb_out = S._agent_dispatch(_s_cap, NODES, {"cmd": "mothball", "id": "identity_cover"})
_s_cap.open_venture("tex_horizontal_loom")
_mb_out2 = S._agent_dispatch(_s_cap, NODES, {"cmd": "mothball", "id": "tex_horizontal_loom"})
check("mothballing a capability institution says more than its upkeep stopped, and closing an ordinary business carries no such warning",
      _mb_out.get("ok") and bool(_mb_out.get("but")) and "capability" in _mb_out["but"]
      and _mb_out2.get("ok") and "but" not in _mb_out2, (_mb_out.get("but"), _mb_out2))

# --- (2) an active project's wait, and the two steps of a taught trade
_s_thr = sim(civ="han_china_100ad", capital=5000000.0)
_s_thr.done.update(NODES["sc2_method_negative_result"].get("pre", ()))
_s_thr._done_changed()
_ok_thr, _ = _s_thr.start_project("sc2_method_negative_result")
_s_thr.step()
_wr_thr = S._agent_dispatch(_s_thr, NODES, {"cmd": "why", "id": "sc2_method_negative_result"})
check("why on an ACTIVE project says what it is waiting on, and with abundant cash against a long calendar floor names the pace throttle",
      _ok_thr and bool(_wr_thr.get("waiting_on")) and "pace it can absorb money" in (_wr_thr.get("waiting_on") or ""),
      _wr_thr.get("waiting_on"))
_tr = S._agent_dispatch(_s_thr, NODES, {"cmd": "train", "trade": "machinist", "n": 1})
_wr_th = S._agent_dispatch(_s_thr, NODES, {"cmd": "why", "id": "ag2_baler"})
check("train's success says hiring is a second step, and why on a project needing the just-taught trade says nobody can do the work yet",
      bool(_tr.get("means")) and "hire" in _tr["means"]
      and "machinist" in (_wr_th.get("trades_taught_but_nobody_here_to_do_them_yet") or []),
      (_tr.get("means"), _wr_th.get("trades_taught_but_nobody_here_to_do_them_yet")))
check("the point-contact transistor's substitution gate clears with neither single_crystal nor silicon_path done",
      _s_thr.substitution_quality("point_contact_transistor") == (1.0, True))

# --- (3) path: the join with what is startable, and the money warnings
_s_pth = sim(civ="rome_100ad")
_rp = S._agent_dispatch(_s_pth, NODES, {"cmd": "path", "id": GOAL})
_av = S._agent_dispatch(_s_pth, NODES, {"cmd": "available", "all": True})
_av_ids = {entry["id"] for entry in (_av.get("available") or []) if isinstance(entry, dict)}
_path_startable_ids = {entry["id"] for entry in (_rp.get("startable_today_toward_this") or []) if isinstance(entry, dict)}
check("path names how many remaining nodes are startable today, and every one of them is genuinely on `available` too",
      isinstance(_rp.get("startable_today_count"), int) and _rp["startable_today_count"] >= 1
      and _path_startable_ids <= _av_ids, (_rp.get("startable_today_count"), _path_startable_ids - _av_ids))


def _knowledge_only_goal(game):
    """The goal whose route has the dearest startable nodes (at least two) among routes where none of them earns
    more than it costs to keep running: the all-knowledge opening, whose combined bill can pass what a poor household can raise."""
    startable_of = {}
    best, best_bill = None, 0.0
    for candidate in sorted(NODES):
        startable = [node_id for node_id in S.closure(NODES, candidate) if node_id not in game.done
                     and startable_of.setdefault(node_id, game.can_start(node_id))]
        if len(startable) >= 2 and not any(
                game.venture_real_earnings(node_id) > game.venture_upkeep_quote(node_id)["now"] for node_id in startable):
            bill = sum(game.project_cost(node_id) for node_id in startable)
            if bill > best_bill:
                best, best_bill = candidate, bill
    return best


_goal = _knowledge_only_goal(_s_pth)
_rp_pay = S._agent_dispatch(_s_pth, NODES, {"cmd": "path", "id": _goal})
check("on a fresh turn-one game some goal's startable route earns no more than it costs, and path says so outright",
      _goal is not None and bool(_rp_pay.get("this_route_pays_for_nothing")), _goal)
_s_poor = sim(civ="rome_100ad", capital=1.0)
_rp_poor = S._agent_dispatch(_s_poor, NODES, {"cmd": "path", "id": _goal})
_total = sum(_s_poor.project_cost(entry["id"]) for entry in _rp_poor["startable_today_toward_this"])
check("a household with almost nothing is told the combined cost of everything listed against what it can raise",
      "{:,.0f}".format(_total) in (_rp_poor.get("these_together_cost_more_than_you_can_raise") or ""),
      (_total, _rp_poor.get("these_together_cost_more_than_you_can_raise")))

# --- (4) a Mexica founder cannot start the animal-drawn vehicles on turn one
_GATED_VEHICLES = ("tr_hopper_wagon", "lnd_two_wheel_cart", "lnd_four_wheel_cart", "mil_artillery_carriage", "pwr_animal_treadmill")
_s_mex = sim(civ="mexica_1500")
check("a fresh Mexica founder cannot start any of them turn one, and the free tier-0 treadmill is not granted by the opening",
      not any(_s_mex.can_start(node_id) for node_id in _GATED_VEHICLES) and "pwr_animal_treadmill" not in _s_mex.done,
      [node_id for node_id in _GATED_VEHICLES if _s_mex.can_start(node_id)])
_s_mex.done.add("exp_import_draught_animals")
_s_mex._done_changed()
check("importing draught animals lifts the gate on all of them (needs_first clears; a vehicle may have other prerequisites)",
      all(_s_mex.needs_first(node_id)[0] is None for node_id in _GATED_VEHICLES),
      [(node_id, _s_mex.needs_first(node_id)) for node_id in _GATED_VEHICLES if _s_mex.needs_first(node_id)[0] is not None])
