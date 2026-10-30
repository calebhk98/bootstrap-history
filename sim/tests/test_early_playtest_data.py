"""What the first playtests found, read off the data with no game (Complaint 640): what each opening grants and cannot
start, the Rome-only phrases, the dated hazards, the policy switches. Every check reads the civilisation files, the tree
or a plain function."""
QUICK_TOPIC = True

from .harness import *  # noqa: F401,F403
from sim.diffusion.civ_cost import civ_cost_factor
from sim.engine.data import TECH_EFFECTS
from sim.knowledge.api import hard_pre
from sim.engine.seat_defaults import default_policy

ROME = S.load_civ("rome_100ad")
HAN = S.load_civ("han_china_100ad")
NORSE = S.load_civ("norse_900ad")
MEXICA = S.load_civ("mexica_1500")


def granted_at_start(civ):
    return set(civ["starting_techs"])


def waiting_on(civ, node_id):
    """The hard prerequisites of a node that its society does not hold at the start."""
    return sorted(set(hard_pre(NODES, node_id)) - granted_at_start(civ))


# --- what cannot be started on turn one
# (mil_general_staff and hot_air_balloon hold their prerequisites and are held back by a trade Rome lacks: the Rome
# scenario in test_early_playtest asks the game)
_ANACHRONISMS = ["mil_chemical_mustard", "mil_trench", "mil_trace_italienne",
                 "mil_conscription_reserve", "mil_observation_balloon", "mil_gunpowder_base"]
startable_turn_one = [node_id for node_id in _ANACHRONISMS if not waiting_on(ROME, node_id)]
check("no anachronistic weapon or doctrine can be started turn one: each waits on a prerequisite Rome lacks",
      not startable_turn_one, str(startable_turn_one))
check("chinampa agriculture waits on a prerequisite Norway lacks", bool(waiting_on(NORSE, "fud_chinampa")),
      waiting_on(NORSE, "fud_chinampa"))
check("chinampa agriculture is still free for the Mexica", "fud_chinampa" in granted_at_start(MEXICA))
check("gunpowder claims no saltpetre it has not earned via nitre_beds",
      "nitre_beds" in NODES["mil_gunpowder_base"]["pre"] and "nitre_beds" in NODES,
      str(NODES["mil_gunpowder_base"]["pre"]))

# --- a society is granted its own institutions and no other's
_ROMAN_INSTITUTIONS = ["civ_arch_roman", "fin_annona", "fin_argentarii",
                       "fin_collegium", "fin_societas", "hom_cosmetics_roman"]
foreign = [node_id for node_id in granted_at_start(HAN) if "_roman" in node_id or "annona" in node_id]
check("a society is not granted another society's institutions", not foreign, str(foreign[:4]))
norse_has_them_free = [node_id for node_id in _ROMAN_INSTITUTIONS if node_id in granted_at_start(NORSE)]
check("a Norse founder is not handed Rome's institutions for nothing", not norse_has_them_free, str(norse_has_them_free))
rome_missing = [node_id for node_id in _ROMAN_INSTITUTIONS if node_id not in granted_at_start(ROME)]
check("Rome is granted its own institutions through starting_techs", not rome_missing, str(rome_missing))
still_free = [node_id for node_id in _ROMAN_INSTITUTIONS if NODES[node_id]["cap"] == 0 and NODES[node_id]["ph"] == 0]
check("Rome's institutions are not free for whoever starts them", not still_free, str(still_free))

# --- a civilisation-specific cost, and a remedy that lifts a handicap
_furnace = NODES["blast_furnace"]
factor_of = {civ["id"]: civ_cost_factor(civ.get("cost_multipliers"), civ.get("handicap_remedies"), set(),
                                         _furnace.get("cat"), _furnace.get("traits") or ())
             for civ in (ROME, HAN, NORSE, MEXICA)}
check("the blast furnace costs a civilisation-specific factor", len(set(factor_of.values())) > 1, factor_of)
_remedies = NORSE.get("handicap_remedies") or {}
_remedy_nodes = sorted({remedy["node"] for remedy in _remedies.values() if isinstance(remedy, dict)})
_lifted = civ_cost_factor(NORSE.get("cost_multipliers"), _remedies, set(_remedy_nodes),
                          _furnace.get("cat"), _furnace.get("traits") or ())
check("building the Norse remedies lifts the handicap on the blast furnace",
      _lifted < factor_of["norse_900ad"], (factor_of["norse_900ad"], _lifted, _remedy_nodes))
check("the Norse remedy the first playtest built is one of the Norse remedies",
      "collegium_licensed" in _remedy_nodes, _remedy_nodes)

# --- the dated hazards
_spanish = next(hazard for hazard in MEXICA["hazards"] if "Spanish" in hazard.get("name", ""))
check("the Spanish invasion still arrives on its historical date, unmoved by anything military technology does",
      _spanish["years"] == [1519, 1521], _spanish["years"])
check("the Spanish invasion hazard carries no staff_loss of its own, so military technology (which never touches "
      "staff_loss) cannot appear to cure contact epidemics", "staff_loss" not in _spanish, sorted(_spanish))
norse_hazards = NORSE["hazards"]
check("the Norse civilization has more than one dated hazard", len(norse_hazards) > 1, "only %d" % len(norse_hazards))
_EFFECT_FIELDS = ("staff_loss", "sack_chance", "output_factor", "real_erosion", "values")
inert = [hazard["name"] for hazard in norse_hazards if not any(field in hazard for field in _EFFECT_FIELDS)]
check("no Norse hazard is purely decorative (no effect field the engine reads)", not inert, str(inert))

# --- the military branch is real without swallowing the tree, and no defence zeroes a harm
_MIL_NODES = sorted(node_id for node_id in NODES if "military" in (NODES[node_id].get("traits") or ()))
check("the tree still has a real military branch to test against", len(_MIL_NODES) >= 100, len(_MIL_NODES))
_over_one = [(node_id, counter["kind"], counter["share"]) for node_id, node in NODES.items()
             for counter in (node.get("hazard_counters") or []) if not 0.0 < counter["share"] < 1.0]
check("every node's hazard counter takes a share strictly between none and all of a harm",
      not _over_one, str(_over_one[:4]))

# --- the setting
check("a technology that reduces fear of the inexplicable lowers the weight of magic fear",
      TECH_EFFECTS["scientific_method"]["w_magic_fear"] < 0.0, TECH_EFFECTS["scientific_method"])
check("every automatic behaviour has a switch",
      set(default_policy(True)) >= {"auto_hire", "auto_buy_people", "auto_manumit", "auto_train", "auto_mine",
                                    "auto_forest", "auto_mothball", "auto_shed", "auto_bribe"},
      sorted(default_policy(True)))
check("a player who plays by hand starts with the people-buying and hiring automations off",
      not default_policy(True)["auto_buy_people"] and not default_policy(True)["auto_hire"]
      and default_policy(False)["auto_hire"])

check("debt bondage follows the society, and is a term of years",
      ROME.get("debt_bondage") is False and HAN.get("debt_bondage") is True and HAN.get("bondage_years", 0) > 0,
      "rome %r han %r" % (ROME.get("debt_bondage"), HAN.get("debt_bondage")))

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

# --- the command registry: every advertised command is one the game answers to
from sim.ui.proto import command_registry

_unhandled = [name for name, entry in command_registry.COMMANDS.items() if entry["handler"] is None]
check("every advertised command has a handler, but help, which dispatch answers before the table",
      _unhandled == ["help"], _unhandled)
_unknown = command_registry.unknown_command_error("definitely_not_a_command")
check("the unknown-command message advertises every command there is",
      all(name in _unknown for name in command_registry.COMMANDS),
      "missing: %s" % [name for name in command_registry.COMMANDS if name not in _unknown])
check("the unknown-command message names the word that was not a command",
      "definitely_not_a_command" in _unknown)
