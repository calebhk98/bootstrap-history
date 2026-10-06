"""early_playtest: regression checks from the first playtests, run with `--only early_playtest`."""
from .harness import *  # noqa: F401,F403

# --- protocol robustness: one agent session carries every malformed or hostile input
_SESSION = [
    ("bare_null", None), ("bare_number", 42), ("bare_string", "x"), ("bare_list", [1, 2]),
    ("state_first", {"cmd": "state"}),
    ("negative_buy", {"cmd": "buy", "what": "forest", "n": -5}),
    ("state_after_buy", {"cmd": "state"}),
    ("non_string_id", {"cmd": "why", "id": {"a": 1}}),
    ("available_digest", {"cmd": "available"}),
    ("available_all", {"cmd": "available", "all": True}),
    ("help", {"cmd": "help"}),
    ("labour", {"cmd": "labour"}),
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
_replies, _raw, _return_code = proto([command for _, command in _SESSION])
check("every input line, malformed or not, gets exactly one reply and the session survives",
      _return_code == 0 and len(_replies) == len(_SESSION), (_return_code, len(_replies)))
reply = {label: one_reply for (label, _), one_reply in zip(_SESSION, _replies)}

check("negative buy quantity changes nothing",
      reply["state_first"]["capital"] == reply["state_after_buy"]["capital"]
      and reply["state_after_buy"]["forest_ha"] == 0,
      "capital %s -> %s" % (reply["state_first"]["capital"], reply["state_after_buy"]["capital"]))
check("state/available/help work before the first step",
      all(reply[label].get("ok") for label in ("state_first", "available_digest", "help")),
      str(reply["state_first"])[:90])
early_physics = {"sc2_physics_nuclear_fission", "sc2_physics_wave_mechanics",
                 "el2_sonar_acoustic_detection_ranging", "el2_photomultiplier_single_photon"}
offered = {entry["id"] for entry in reply["available_all"]["available"]} & early_physics
check("no advanced physics is startable in year one", not offered, str(offered))
sizes = {name: len(json.dumps(reply[label])) for name, label in
         (("state", "state_first"), ("available", "available_digest"), ("help", "help"), ("labour", "labour"))}
check("no ordinary reply is a wall of text", all(value < 6000 for value in sizes.values()), str(sizes))
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

# --- play must run a civilisation that does not start in 100 AD (its loop used to end at 100 + horizon)
_play = subprocess.run([sys.executable, os.path.join(HERE, "simulator.py"), "play", "--manual",
                        "--civ", "norse_900ad"],
                       input="n\nq\n", capture_output=True, text=True, timeout=120, cwd=ROOT)
check("play runs a civilisation that does not start in 100 AD",
      "900 AD" in _play.stdout and "Ended 900 AD" not in _play.stdout, _play.stdout[-120:])

# --- Rome, one game: turn-one state, and what a player can and cannot do
rome = sim(capital=200000.0)
check("you arrive with no employees and no slaves",
      not rome.employees and rome.slaves == 0 and rome.freedmen == 0 and rome.artisans == 0.0,
      "employees %r artisans %.1f" % (rome.employees, rome.artisans))
rome_why_cost = S._agent_dispatch(rome, NODES, {"cmd": "why", "id": "blast_furnace"})["cost"]["total"]

_ANACHRONISMS = ["mil_chemical_mustard", "mil_trace_italienne", "mil_general_staff",
                 "mil_conscription_reserve", "mil_trench", "hot_air_balloon",
                 "mil_observation_balloon", "mil_gunpowder_base"]
startable_turn_one = [node_id for node_id in _ANACHRONISMS if rome.can_start(node_id)]
check("no anachronistic weapon or doctrine is startable turn one",
      not startable_turn_one, str(startable_turn_one))

ok_hire, hire_error = rome.labour.hire("engineer", 1)
check("a trade this society does not have cannot be hired",
      not ok_hire and "no engineer" in (hire_error or "").lower(),
      "hire engineer -> %s / %s" % (ok_hire, hire_error))
rome.capital = 20000.0
ok_train, _ = rome.labour.train("machinist", 2)
check("you can teach a trade into existence",
      ok_train and "machinist" in rome.trades_created and not rome.labour.trade_available("chemist"),
      "trained %s created %r" % (ok_train, sorted(rome.trades_created)))
check("every automatic behaviour has a switch",
      set(rome.policy) >= {"auto_hire", "auto_buy_people", "auto_manumit", "auto_train",
                           "auto_mine", "auto_forest", "auto_mothball", "auto_shed",
                           "auto_bribe"},
      sorted(rome.policy))

# a finished work can be shut to stop its upkeep without forgetting how it worked
rome.labour.hire("artisan", 2)
rome.done.add("fin_restaurant")
rome._done_changed()
# Upkeep follows what you RUN, not what you know, so open the doors first.
_ok_open, _why_open = rome.open_venture("fin_restaurant")
up_before = rome.upkeep()
ok_mothball, _ = rome.mothball_work("fin_restaurant")
check("a finished work can be shut down to stop its upkeep",
      _ok_open and ok_mothball and up_before > 0 and rome.upkeep() < up_before,
      "open %s (%s), upkeep %.0f -> %.0f" % (_ok_open, _why_open, up_before, rome.upkeep()))
check("shutting a concern down does not make you forget how it worked",
      "fin_restaurant" in rome.done and "fin_restaurant" not in rome.operating,
      "done %s operating %s" % ("fin_restaurant" in rome.done, "fin_restaurant" in rome.operating))

# hazards must be answerable with technology
bare_relief, _ = rome.hazard_relief("staff_loss")
rome.done.add("sanitation_antisepsis")
rome.operating.add("sanitation_antisepsis")
rome.done.add("germ_theory")
better_relief, relief_why = rome.hazard_relief("staff_loss")
check("medicine blunts a plague", bare_relief == 1.0 and better_relief < 0.6 and relief_why,
      "%.2f -> %.2f %s" % (bare_relief, better_relief, relief_why))
rome.mines.append({"material": "gold", "capacity": 1.0, "opened_year": rome.year,
                   "capex_paid": 0.0, "intensity_yrs": 0.0})
gold_relief, _ = rome.hazard_relief("real_erosion")
check("your own gold mine blunts a debasement", gold_relief < 0.5, "%.2f" % gold_relief)

weights_before = rome.value_weights["w_magic_fear"]
rome.apply_tech_effects("scientific_method")
check("a technology changes the society that built it",
      rome.value_weights["w_magic_fear"] < weights_before,
      "%.2f -> %.2f" % (weights_before, rome.value_weights["w_magic_fear"]))

money_factor = rome.cost_money_factor()
rome.money_real = 0.005
check("a debased currency does not collapse prices",
      abs(rome.cost_money_factor() - money_factor) < 1e-9,
      "%.4f -> %.4f" % (money_factor, rome.cost_money_factor()))

rome.capital = 5000.0
capital_before_commission = rome.capital
employees_before_commission = dict(rome.employees)
ok_job, _ = rome.labour.commission("smith", 200)
check("you can buy a job without employing anybody",
      ok_job and rome.employees == employees_before_commission and rome.capital < capital_before_commission,
      "ok %s employees %r" % (ok_job, rome.employees))


# buying people then freeing them must not mint labour or skip the training lag
artisans_before = rome.artisans
rome.capital = 200000.0
rome.labour.buy_slaves(10)
rome.labour.manumit(10)
check("freeing untrained people does not skip the training lag",
      rome.artisans - artisans_before < 0.01, "instant gain %.2f" % (rome.artisans - artisans_before))

def spend(slices, per):
    spend_sim = sim(capital=1e9)
    # Buying respects the feed/house/oversee cap `hire` has, so make room first or this tests the cap.
    run_it(spend_sim, "workshop_first", "freedman_staff")
    starting_capital = spend_sim.capital
    for _ in range(slices):
        spend_sim.labour.buy_slaves(per)
    return starting_capital - spend_sim.capital


all_at_once, one_at_a_time = spend(1, 12), spend(12, 1)
check("buying in slices costs the same as buying at once",
      abs(all_at_once - one_at_a_time) < 1.0, "%.0f / %.0f" % (all_at_once, one_at_a_time))

# --- Han: a civilisation-specific cost, and no other society's institutions
han = sim(civ="han_china_100ad", manual=False)
han_why_cost = S._agent_dispatch(han, NODES, {"cmd": "why", "id": "blast_furnace"})["cost"]["total"]
check("why quotes a civilization-specific cost", rome_why_cost != han_why_cost,
      str((rome_why_cost, han_why_cost)))
han.step()
foreign = [node_id for node_id in han.granted if "_roman" in node_id or "annona" in node_id]
check("a society is not granted another society's institutions", not foreign, str(foreign[:4]))

# --- Norse: handicap remedies, no foreign institutions, no geography-locked crops, no sack-loss risk
norse = sim(civ="norse_900ad", capital=1000000.0)
_ROMAN_INSTITUTIONS = ["civ_arch_roman", "fin_annona", "fin_argentarii",
                       "fin_collegium", "fin_societas", "hom_cosmetics_roman"]
norse_has_them_free = [node_id for node_id in _ROMAN_INSTITUTIONS if node_id in norse.done]
check("a Norse founder is not handed Rome's institutions for nothing",
      not norse_has_them_free, str(norse_has_them_free))
check("chinampa agriculture is not startable in Norway", not norse.can_start("fud_chinampa"))
knowledge_risk = S._agent_dispatch(norse, NODES, {"cmd": "risk"})["knowledge_risk"]
check("no loss risk is reported where nothing sacks",
      knowledge_risk["expected_technologies_lost_per_sacking"] == 0.0, str(knowledge_risk)[:80])
cost_factor_before = norse.civ_cost_factor("blast_furnace")
norse.done.add("collegium_licensed")
cost_factor_after = norse.civ_cost_factor("blast_furnace")
check("building a remedy lifts the handicap", cost_factor_after < cost_factor_before,
      "%.2f -> %.2f" % (cost_factor_before, cost_factor_after))
norse.start_project("identity_cover")
for _ in range(4):
    norse.step()
norse.capital = -2.0 * norse.credit_limit()
for _ in range(2):
    norse.step()
check("an insolvency settlement never abandons a persona or institution",
      "identity_cover" in norse.done, "identity_cover was shed")

# --- Mexica: chinampa is theirs, and military technology blunts but never zeroes a sacking
mexica = sim(civ="mexica_1500")
check("chinampa agriculture is still free for the Mexica", "fud_chinampa" in mexica.done)
_spanish = next(hazard for hazard in mexica.civ["hazards"] if "Spanish" in hazard.get("name", ""))
check("the Spanish invasion still arrives on its historical date, unmoved "
      "by anything military technology does",
      _spanish["years"] == [1519, 1521], _spanish["years"])
check("the Spanish invasion hazard carries no staff_loss of its own, so military "
      "technology (which never touches staff_loss) cannot appear to cure contact epidemics",
      "staff_loss" not in _spanish, sorted(_spanish))
_MIL_NODES = sorted(node_id for node_id in NODES if "military" in (NODES[node_id].get("traits") or ()))
sack_bare, _ = mexica.hazard_relief("sack_chance")
for node_id in _MIL_NODES:
    mexica.done.add(node_id)
sack_armed, sack_why = mexica.hazard_relief("sack_chance")
check("a Mexica founder who had built firearms and fortification before "
      "the Spanish arrived would face a real, non-zero chance of a "
      "sacking still - the counterfactual is blunted, never zeroed",
      0.0 < sack_armed < sack_bare, (sack_bare, sack_armed, sack_why[:3]))

# --- the military branch matters, without swallowing the tree
check("the tree still has a real military branch to test against", len(_MIL_NODES) >= 100, len(_MIL_NODES))
unarmed = sim()
armed = sim()
founder_military_nodes = [node_id for node_id in _MIL_NODES if node_id not in armed.granted]
leverage_none = armed.military_leverage()
armed.done.add(founder_military_nodes[0])
leverage_first = armed.military_leverage()
for node_id in founder_military_nodes[:25]:
    armed.done.add(node_id)
leverage_some = armed.military_leverage()
for node_id in _MIL_NODES:
    armed.done.add(node_id)
leverage_all = armed.military_leverage()
check("military strength is zero for a founder who has built none of the "
      "branch, rises with the first node, and saturates well short of the "
      "whole branch (so the branch cannot be a strategy unto itself)",
      leverage_none == 0.0 and 0.0 < leverage_first < leverage_some == 1.0 and leverage_all == 1.0,
      (leverage_none, leverage_first, leverage_some, leverage_all))

unarmed.update_protection()
armed.update_protection()
check("a cannon foundry with nobody to sell to protects the founder not at "
      "all - the leverage is with a patron, not the hardware itself",
      abs(armed.protection - unarmed.protection) < 1e-9, (unarmed.protection, armed.protection))

output_unarmed, _ = unarmed.hazard_relief("output_factor")
output_armed, output_why = armed.hazard_relief("output_factor")
check("a war costs an armed empire's trade less than an unarmed one's - "
      "every output_factor hazard in these civilization files is a war or "
      "its administrative aftermath, and this is the branch's answer to it",
      output_armed < output_unarmed and any("military strength" in reason for reason in output_why),
      (output_unarmed, output_armed, output_why))
staff_unarmed, _ = unarmed.hazard_relief("staff_loss")
staff_armed, _ = armed.hazard_relief("staff_loss")
check("military technology gives no relief against staff loss - most "
      "staff_loss hazards in these civilizations are disease and famine, "
      "not war, and a founder with cannon should not cure the Antonine "
      "plague",
      staff_unarmed == staff_armed, (staff_unarmed, staff_armed))

run_it(unarmed, "patron_imperial")
run_it(armed, "patron_imperial")
unarmed.update_protection()
armed.update_protection()
check("an armourer with an imperial patron to arm is protected more than "
      "the same patron without the armoury, and the gain is a real fraction "
      "of a percent, not a rounding error or a dominant strategy on its own",
      0.02 < armed.protection - unarmed.protection < 0.12, (unarmed.protection, armed.protection))

unarmed.output_factor = 0.7
armed.output_factor = 0.7
unarmed.step()
armed.step()
check("an armed empire's trade recovers from a war faster than an unarmed "
      "one's, year over year, and the war still happened either way - this "
      "is recovery speed, not a rewrite of the event",
      armed.output_factor > unarmed.output_factor > 0.7, (unarmed.output_factor, armed.output_factor))

# --- fog hides the exact downstream count
fogged = sim()
fogged.fog = True
fogged.revealed = set()
fog_reply = S._agent_dispatch(fogged, NODES, {"cmd": "why", "id": "identity_cover"})
check("fog hides the exact downstream count",
      fog_reply.get("downstream_count") is None and fog_reply.get("how_much_rests_on_this"),
      "downstream %r band %r" % (fog_reply.get("downstream_count"), fog_reply.get("how_much_rests_on_this")))

# --- mines: topping up still delivers capacity, and a mine can be closed
mine_game = sim(capital=5e6)
for _ in range(6):
    mine_game.open_mine("coal", 200)
    mine_game.step()
    if mine_game.mine_capacity.get("coal", 0) > 0:
        break
check("topping up a mine still delivers capacity",
      mine_game.mine_capacity.get("coal", 0) > 0, str(mine_game.mine_capacity))
cost_open = S._agent_dispatch(mine_game, NODES, {"cmd": "state"}).get("mine_operating_cost", 0)
S._agent_dispatch(mine_game, NODES, {"cmd": "close", "material": "coal"})
cost_closed = S._agent_dispatch(mine_game, NODES, {"cmd": "state"}).get("mine_operating_cost")
check("a mine can be closed, and stops costing", cost_open > 0 and cost_closed == 0,
      "before %s after %s" % (cost_open, cost_closed))

# --- an unfunded project never completes, and manual play never buys people for you
unfunded = sim(capital=book_money(400.0), manual=True)
ok_start, start_why = unfunded.start_project("identity_cover")         # 1,580 den against 400
for _ in range(3):
    unfunded.step()
paid = unfunded.active.get("identity_cover", {}).get("spent", 0.0)
check("an unfunded project never completes",
      ok_start and "identity_cover" not in unfunded.done,
      "started=%s (%s) done=%s paid=%.0f" % (ok_start, start_why, "identity_cover" in unfunded.done, paid))
check("manual play never buys people for you", unfunded.slaves == 0 and unfunded.freedmen == 0,
      "slaves %d freedmen %d" % (unfunded.slaves, unfunded.freedmen))


# --- available stays a summary as the tree opens up.
# Constructed directly: `_agent_available` reads only done/operating/fog, and cutting an arbitrary
# slice of ORDER opens far more of the tree at once than a real run does, which is the harder case.
def _tree_opens_up():
    out = []
    for frac in (0.30, 0.55):
        tree_sim = sim(capital=1e6, manual=False)
        tree_sim.fog = True
        cut = int(len(ORDER) * frac)
        tree_sim.done.update(ORDER[:cut])
        tree_sim._done_changed()
        avail = S._agent_available(tree_sim, NODES)
        digest = len(json.dumps(avail))
        out.append((digest < 12000,
                    "%d bytes at %d%% of tree done with %d things startable"
                    % (digest, int(frac * 100), avail["count"])))
    return all(passed for passed, _ in out), "; ".join(detail for _, detail in out)


slow_check("available stays a summary as the tree opens up", _tree_opens_up)

# --- the unknown-command message names every command, and every command answers
answers = sim()
_unknown = S._agent_dispatch(answers, NODES, {"cmd": "definitely_not_a_command"}).get("error", "")
check("the unknown-command message advertises every command there is",
      all(command in _unknown for command in S.KNOWN_COMMANDS),
      "missing: %s" % [command for command in S.KNOWN_COMMANDS if command not in _unknown])
_dead = []
for _command in S.KNOWN_COMMANDS:
    if _command in ("quit", "save", "load", "finish", "step"):
        continue                  # need arguments, write files or end the run
    try:
        _answer = S._agent_dispatch(answers, NODES, {"cmd": _command})
    except Exception:
        continue                  # a crash is a different bug; this asks only whether the command is known
    if "unknown cmd" in str(_answer.get("error", "")):
        _dead.append(_command)
check("every advertised command is one the game answers to", not _dead, str(_dead))
_missing_id = S._agent_dispatch(answers, NODES, {"cmd": "why"}).get("error", "")
check("a missing id asks for one rather than naming a Python type",
      "NoneType" not in _missing_id and "available" in _missing_id, _missing_id[:90])

# --- data lints that cost no game
PUMP_PAYBACK_YEARS_FLOOR = 0.25
pumps = [node_id for node_id, node in NODES.items()
         if float(node.get("rev") or 0) > 0 and node["_total_cost"] > 0
         and node["_total_cost"] / float(node["rev"]) < PUMP_PAYBACK_YEARS_FLOOR]
check("no node repays its entire cost in under three months", not pumps,
      "%d pumps, e.g. %s" % (len(pumps), pumps[:3]))

check("debt bondage follows the society, and is a term of years",
      S.load_civ("rome_100ad").get("debt_bondage") is False
      and S.load_civ("han_china_100ad").get("debt_bondage") is True
      and S.load_civ("han_china_100ad").get("bondage_years", 0) > 0,
      "rome %r han %r" % (S.load_civ("rome_100ad").get("debt_bondage"),
                          S.load_civ("han_china_100ad").get("debt_bondage")))

civ_files = [filename for filename in os.listdir(os.path.join(ROOT, "data", "civilizations"))
             if filename.endswith(".json") and not filename.startswith("_")]
missing_lore = []
for civ_file in civ_files:
    civ_data = json.load(open(os.path.join(ROOT, "data", "civilizations", civ_file)))
    opening = civ_data.get("opening") or {}
    if not all(opening.get(field_name) for field_name in ("arrival", "what_you_can_see",
                                                          "what_is_missing", "what_is_coming")):
        missing_lore.append(civ_data.get("id", civ_file))
check("every civilisation has its opening written", not missing_lore, str(missing_lore))

# --- the setting is not Rome wearing a hat: notes must generalise
_ROME_TEMPLATES = ("ROME ALREADY HAS THIS", "ROME HAS THIS", "ROME POSSIBLY HAS THIS")
bare_rome_notes = [node_id for node_id, node in NODES.items()
                   if any(template in (node.get("note") or "") for template in _ROME_TEMPLATES)]
check("no node note bluntly claims 'Rome [already] has this'", not bare_rome_notes, str(bare_rome_notes[:5]))
bare_rome_prices = [trade_key for trade_key, value in PRICES["wage_rates_denarii_per_hour"].items()
                    if not trade_key.startswith("_") and isinstance(value, dict)
                    and ("Rome has" in (value.get("note") or "")
                         or "Rome already has" in (value.get("note") or ""))]
check("no wage-rate note bluntly claims 'Rome has these'", not bare_rome_prices, str(bare_rome_prices))
check("the cover identity is not named after one civilization's version",
      "Alexandrian" not in NODES["identity_cover"]["name"], NODES["identity_cover"]["name"])
rome_missing = [node_id for node_id in _ROMAN_INSTITUTIONS
                if node_id not in (S.load_civ("rome_100ad").get("starting_techs") or [])]
check("Rome is granted its own institutions through starting_techs", not rome_missing, str(rome_missing))
still_free = [node_id for node_id in _ROMAN_INSTITUTIONS if NODES[node_id]["cap"] == 0 and NODES[node_id]["ph"] == 0]
check("Rome's institutions are not free for whoever starts them", not still_free, str(still_free))

# --- five centuries, two events: Norse hazards must do something the engine reads
norse_hazards = S.load_civ("norse_900ad")["hazards"]
check("the Norse civilization has more than one dated hazard", len(norse_hazards) > 1, "only %d" % len(norse_hazards))
_EFFECT_FIELDS = ("staff_loss", "sack_chance", "output_factor", "real_erosion", "values")
inert = [hazard["name"] for hazard in norse_hazards if not any(field in hazard for field in _EFFECT_FIELDS)]
check("no Norse hazard is purely decorative (no effect field the engine reads)", not inert, str(inert))
