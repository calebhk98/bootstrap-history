"""SMOKE (five unopened games, no year run): the civilisation files in a whole game: each society's own prices reach its living cost and revenue,
the player-facing replies carry the civilisation's own words, a refused start in the Valley of Mexico is hidden from
what could begin today, and no goal is already met on turn one. The rules are in test_civilisation_data_integrity."""
from .harness import *  # noqa: F401,F403

from sim.engine.win_condition_rule import win_condition_met

_CIVS = ("rome_100ad", "han_china_100ad", "norse_900ad", "mexica_1500", "england_1300")
_games = {_cid: unopened_sim(civ=_cid) for _cid in _CIVS}

# --- the advertised price index touched nothing a player feels: revenue and living costs were identical in every civ.
_lc, _rv = {}, {}
for _cid, _s in _games.items():
    _rv[_cid] = round(_s.revenue(), 2)
    _lc[_cid] = round(_s.household_bill_per_person(), 4)   # the economy's need floors at this society's prices
check("scenario: living costs and revenue follow this society's own prices, and every society pays something for its needs",
      len(set(_lc.values())) == 5 and len(set(_rv.values())) == 5 and all(bill > 0.0 for bill in _lc.values()), (_lc, _rv))

# --- the reply carries the civilisation's words (the swap itself is a rule in the data-integrity topic).
_why = [S._agent_dispatch(_games["han_china_100ad"], NODES, {"cmd": "why", "id": _node_id})
        for _node_id in ("corpus_written", "patron_senatorial")]
check("scenario: a `why` reply in Han China is not handed Rome's own words",
      "Greek and Latin" not in json.dumps(_why) and "Senatorial patronage" not in json.dumps(_why), json.dumps(_why)[:120])

# --- the gate reaches the refusal and the menu of what could begin today.
_mex = _games["mexica_1500"]
_ok_h, _why_h = _mex.start_reason("horse_collar")
check("scenario: in the Valley of Mexico a draught-animal start is refused naming what would open it, and is not on today's menu",
      not _ok_h and "exp_import_draught_animals" in _why_h
      and not any(entry["id"] == "horse_collar" for entry in S._agent_available(_mex, NODES, {"all": True})["available"]),
      _why_h)

# --- nothing free arrives on turn one: no goal's win condition is already met by the opening state, in any society
# (a goal met at the start is completed by the first year's check without the founder doing anything).
_met_at_start = {}
for _cid, _s in _games.items():
    _met_at_start[_cid] = sorted(
        _node_id for _node_id in _s._win_condition_keys
        if _node_id not in _s.done and _s.nodes[_node_id]["win_condition"]
        and win_condition_met(_s.nodes[_node_id]["win_condition"], _s._win_condition_value(_s.nodes[_node_id]["win_condition"])))
check("scenario: no civilisation opens with a goal already met, so none hands you anything free on turn one",
      not any(_met_at_start.values()), _met_at_start)
