"""SMOKE: early_playtest: the first playtests' regressions on unopened games, no year stepped.

The rules moved out of this file: the cost factor, hazard relief and trade availability are called with figures in
test_civ_cost_and_hazard_relief_rules; military leverage and war relief in test_military_leverage_rules; what each opening
grants, the dated hazards and the policy switches in test_early_playtest_data. What remains is one session of malformed
input answered by the dispatcher, and the Rome turn-one labour, mothball and commission steps; the Norse and fog replies follow.
"""
from .harness import *  # noqa: F401,F403
from sim.refusal import cause_of
from sim.projects.api import MothballWork
from sim.ventures.api import OpenVenture

def without_market(game):
    """`game` with the year's market close left out of its steps: nearly all of a step's cost. Only for checks on
    staff, projects, mines, raids and recovery; the founder's money does follow the market, so games whose checks
    read money keep it."""
    game.assembly.phase_handler("market")   # builds the phase table
    game.assembly._phase_handlers["market"] = lambda seats=None: None
    return game


# --- SCENARIO 1: the protocol surface. One agent session carries every malformed or hostile input
_SESSION = [
    ("bare_null", None), ("bare_number", 42), ("bare_string", "x"), ("bare_list", [1, 2]),
    ("state_first", {"cmd": "state"}),
    ("negative_buy", {"cmd": "buy", "what": "forest", "n": -5}),
    ("state_after_buy", {"cmd": "state"}),
    ("non_string_id", {"cmd": "why", "id": {"a": 1}}),
    ("help", {"cmd": "help"}),
    ("hire_banana", {"cmd": "hire", "trade": "smith", "n": "banana"}),
    ("bribe_lots", {"cmd": "bribe", "amount": "lots"}),
    ("state_after_refusals", {"cmd": "state"}),
    ("save_absolute", {"cmd": "save", "file": "/etc/should_not_happen.json"}),
    ("save_escape", {"cmd": "save", "file": "../../escape.json"}),
    ("save_wrong_extension", {"cmd": "save", "file": "notasave.txt"}),
    ("step_too_many", {"cmd": "step", "years": 100000}),
    ("step_true", {"cmd": "step", "years": True}),
    ("quote_mine", {"cmd": "quote", "what": "mine", "material": "gold", "n": 1}),
    ("state_last", {"cmd": "state"}),
]
_game = unopened_sim(capital=200000.0)
_game.end_year = _game.cfg["start_year"] + 200   # as the agent front end sets it
_replies = [S._agent_dispatch(_game, NODES, command) for _, command in _SESSION]
check("every input line, malformed or not, gets exactly one reply",
      len(_replies) == len(_SESSION) and all(isinstance(one_reply, dict) for one_reply in _replies), len(_replies))
reply = {label: one_reply for (label, _), one_reply in zip(_SESSION, _replies)}

check("negative buy quantity changes nothing",
      reply["state_first"]["capital"] == reply["state_after_buy"]["capital"]
      and reply["state_after_buy"]["forest_ha"] == 0,
      "capital %s -> %s" % (reply["state_first"]["capital"], reply["state_after_buy"]["capital"]))
check("state/help work before the first step",
      all(reply[label].get("ok") for label in ("state_first", "help")),
      str(reply["state_first"])[:90])
early_physics = ["sc2_physics_nuclear_fission", "sc2_physics_wave_mechanics",
                 "el2_sonar_acoustic_detection_ranging", "el2_photomultiplier_single_photon"]
offered = [node_id for node_id in early_physics if _game.view("start_check")(node_id, False, None, False)[0]]
check("no advanced physics is startable in year one", not offered, str(offered))
check("a quantity that is not a number is refused, not defaulted",
      not reply["hire_banana"].get("ok") and not reply["bribe_lots"].get("ok")
      and not reply["state_after_refusals"].get("employees"),
      str(reply["hire_banana"].get("error"))[:70])
check("a save cannot be written outside the game directory",
      all(not reply[label].get("ok") for label in ("save_absolute", "save_escape", "save_wrong_extension")),
      str([reply[label].get("ok") for label in ("save_absolute", "save_escape", "save_wrong_extension")]))
check("/etc was not written to", not os.path.exists("/etc/should_not_happen.json"))
check("step refuses more years than the game contains", not reply["step_too_many"].get("ok"),
      str(reply["step_too_many"])[:80])
check("step refuses true as a number of years", not reply["step_true"].get("ok"), str(reply["step_true"])[:80])
check("a mine can be priced before it is bought",
      reply["quote_mine"].get("ok") and reply["quote_mine"].get("to_sink_it", 0) > 0
      and reply["quote_mine"].get("every_year_it_stands", 0) > 0, str(reply["quote_mine"])[:90])

# --- SCENARIO 2: Rome, one game: turn-one state, and what a player can and cannot do
rome = unopened_sim(capital=200000.0)
_rome_staff = rome.view("staff")()
check("you arrive with no employees and no slaves",
      not _rome_staff["employees"] and _rome_staff["slaves"] == 0 and _rome_staff["freedmen"] == 0 and _rome_staff["artisans"] == 0.0,
      "employees %r artisans %.1f" % (_rome_staff["employees"], _rome_staff["artisans"]))

# the two doctrines whose prerequisites Rome holds, and which a trade Rome lacks holds back (the rest wait on a prerequisite:
# test_early_playtest_data)
_ANACHRONISMS = ["mil_general_staff", "hot_air_balloon"]
startable_turn_one = [node_id for node_id in _ANACHRONISMS if rome.view("start_check")(node_id, False, None, False)[0]]
check("no anachronistic doctrine is startable turn one, even with its prerequisites held",
      not startable_turn_one, str(startable_turn_one))

ok_hire, hire_error = rome.view("legacy_labour")().hire("engineer", 1)
check("a trade this society does not have cannot be hired",
      not ok_hire and cause_of(hire_error) == "trade_absent",
      "hire engineer -> %s / %s" % (ok_hire, hire_error))
rome.state.household.capital = 20000.0
ok_train, _ = rome.view("legacy_labour")().train("machinist", 2)
check("you can teach a trade into existence",
      ok_train and "machinist" in rome.view("trade_spread")()["created"] and not rome.view("legacy_labour")().trade_available("chemist"),
      "trained %s created %r" % (ok_train, sorted(rome.view("trade_spread")()["created"])))
# a finished work can be shut to stop its upkeep without forgetting how it worked
rome.view("legacy_labour")().hire("artisan", 2)
rome.state.projects.done.add("fin_restaurant")
rome._done_changed()
# Upkeep follows what you RUN, not what you know, so open the doors first.
_ok_open, _why_open = rome.send(OpenVenture("fin_restaurant", None))
up_before = rome.view("upkeep")()
ok_mothball, _ = rome.send(MothballWork("fin_restaurant"))
check("a finished work can be shut down to stop its upkeep",
      _ok_open and ok_mothball and up_before > 0 and rome.view("upkeep")() < up_before,
      "open %s (%s), upkeep %.0f -> %.0f" % (_ok_open, _why_open, up_before, rome.view("upkeep")()))
check("shutting a concern down does not make you forget how it worked",
      "fin_restaurant" in rome.state.projects.done and "fin_restaurant" not in rome.state.projects.operating,
      "done %s operating %s" % ("fin_restaurant" in rome.state.projects.done, "fin_restaurant" in rome.state.projects.operating))

rome.state.household.capital = 5000.0
capital_before_commission = rome.state.household.capital
employees_before_commission = dict(rome.view("staff")()["employees"])
ok_job, _ = rome.view("legacy_labour")().commission("smith", 200)
check("you can buy a job without employing anybody",
      ok_job and rome.view("staff")()["employees"] == employees_before_commission and rome.state.household.capital < capital_before_commission,
      "ok %s employees %r" % (ok_job, rome.view("staff")()["employees"]))


# buying people then freeing them must not mint labour or skip the training lag
artisans_before = rome.view("staff")()["artisans"]
rome.state.household.capital = 200000.0
rome.view("legacy_labour")().buy_slaves(10)
rome.view("legacy_labour")().manumit(10)
check("freeing untrained people does not skip the training lag",
      rome.view("staff")()["artisans"] - artisans_before < 0.01, "instant gain %.2f" % (rome.view("staff")()["artisans"] - artisans_before))

def spend(slices, per):
    spend_sim = unopened_sim(capital=1e9)
    # Buying respects the feed/house/oversee cap `hire` has, so make room first or this tests the cap.
    run_it(spend_sim, "workshop_first", "freedman_staff")
    starting_capital = spend_sim.state.household.capital
    for _ in range(slices):
        spend_sim.view("legacy_labour")().buy_slaves(per)
    return starting_capital - spend_sim.state.household.capital


all_at_once, one_at_a_time = spend(1, 12), spend(12, 1)
check("buying in slices costs the same as buying at once",
      abs(all_at_once - one_at_a_time) < 1.0, "%.0f / %.0f" % (all_at_once, one_at_a_time))

# --- SCENARIO 3: the Han, Norse and Mexica openings through a game
# Norse: no sack-loss risk where nothing sacks
norse = unopened_sim(civ="norse_900ad", capital=1000000.0)
knowledge_risk = S._agent_dispatch(norse, NODES, {"cmd": "risk"})["knowledge_risk"]
check("no loss risk is reported where nothing sacks",
      knowledge_risk["expected_technologies_lost_per_sacking"] == 0.0, str(knowledge_risk)[:80])

# --- (scenario 1 again) fog hides the exact downstream count, and the digest stays a summary as the tree opens up
fogged = unopened_sim()
fogged.fog = True
fogged.state.projects.revealed = set()
fog_reply = S._agent_dispatch(fogged, NODES, {"cmd": "why", "id": "identity_cover"})
check("fog hides the exact downstream count",
      fog_reply.get("downstream_count") is None and fog_reply.get("how_much_rests_on_this"),
      "downstream %r band %r" % (fog_reply.get("downstream_count"), fog_reply.get("how_much_rests_on_this")))
