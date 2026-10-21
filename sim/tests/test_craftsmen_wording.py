"""craftsmen_wording: the diffusion and relief rules are called with figures built here (diffusion_rules, a fake hazard
mixin); what stays through a game is named "scenario" or marked presentation. Run with `--only craftsmen_wording`."""
from .harness import *  # noqa: F401,F403
from .plague_fixture import ANTONINE, BLACK_DEATH, with_hazard

from sim.engine.diffusion_rules import medical_relief, spread_share, weapons_relief
from sim.engine.hazard_relief import HazardReliefMixin

# ===========================================================================
# "What does it mean when it says I need 2.13 craftsmen?" - wording only,
# no arithmetic changed anywhere below.
# ===========================================================================

# --- a concern's staff_to_keep_it_open is venture_hands's own number.
s_shut = unopened_sim(capital=10_000_000.0)
for _p in S.closure(NODES, "lens_grinding"):
    s_shut.done.add(_p)
s_shut.done.add("lens_grinding")
s_shut._done_changed()
_why_sg = S._agent_dispatch(s_shut, NODES, {"cmd": "why", "id": "lens_grinding"})
check("scenario: `why`'s staff_to_keep_it_open is exactly venture_hands's own number",
      (_why_sg.get("staff_to_keep_it_open") or {}).get("artisans")
      == round(s_shut.venture_hands("lens_grinding")[1], 2),
      _why_sg.get("staff_to_keep_it_open"))

# --- the build-crew staffing refusal (craft_hands_available: staff PLUS
# hours already bought under contract) still refuses for the same reason
# and still says "craftsmen" (an existing regression checks this), and now
# explains the mixed count inline instead of implying a body count alone.
s_cc = unopened_sim(civ="rome_100ad", capital=1e6, manual=True, events=False)
s_cc.done.update(NODES["ag2_cold_store"]["pre"])  # prerequisites held, so only staffing can refuse
_ok_cc, _why_cc = s_cc.start_reason("ag2_cold_store", ignore_trade=True)
check("scenario: the craftsmen staffing refusal still refuses for the same reason, "
      "unchanged arithmetic",
      not _ok_cc and "craftsmen" in _why_cc, _why_cc)

# ONE NAME FOR THE FOUNDER'S OWN WORK. The wage-work reply once called it
# "the practice" and then "the surgery"; a Roman founder selling a year of a
# smith's labour has neither. It is a job and the reply says wage, not practice.
# presentation: the wage-work reply's wording (no practice or surgery)
_s_wg = unopened_sim()
_wg = S._agent_dispatch(_s_wg, NODES, {"cmd": "work", "trade": "labourer",
                                       "hours": 2000})
check("scenario: wage work states what a year of labourer's time paid, with no practice or surgery in the reply",
      (_wg.get("earned") or 0) > 0 and "practice" not in str(_wg).lower() and "surgery" not in str(_wg).lower(),
      _wg)

# =============================================================================
# THE COUNTRY CHANGES TOO, NOT ONLY THE FOUNDER'S OWN EXPOSURE TO IT. A
# player's own examples, stated plainly as the spec: New World crops and
# crop rotation raise the whole country's food and population within a few
# decades; cannon in the STATE's hands (not only the founder's workshop)
# changes whether the Gothic wars cost the country as much; a cure or
# vaccine diffused through the country turns the Black Death into a minor
# sickness. See SocietyMixin.civ_diffusion and everything built on it
# (society.py, just above diffusion_index). The household-risk mechanism
# from the PREVIOUS round (_resolve_hazard_condition, hazard `condition`
# blocks) is untouched by any of this - these are a second, independent
# layer, scaled by how far what the founder built has actually spread.
_FOOD_NODE, _MED_NODES, _MIL_NODES2, _INFO_NODE = (
    "crop_rotation",
    ["sanitation_antisepsis", "med_quarantine_sanitation", "germ_theory",
     "md2_vaccine_smallpox"],
    ["gunpowder", "mil_artillery_piece"],
    "printing_press",
)
check("the four diffusion categories this section reads are real nodes with "
      "the traits civ_diffusion keys off",
      NODES[_FOOD_NODE]["traits"].__contains__("food")
      and all("medical" in NODES[node_id]["traits"] for node_id in _MED_NODES)
      and all("military" in NODES[node_id]["traits"] for node_id in _MIL_NODES2)
      and "information" in NODES[_INFO_NODE]["traits"],
      (_FOOD_NODE, _MED_NODES, _MIL_NODES2, _INFO_NODE))

# --- spread_share: zero at once, half after one half-life, bounded at all of it.
check("nothing has spread the instant a technology completes - diffusion takes time",
      spread_share(0.0, 25.0) == 0.0)
check("half is spread after one half-life, and a quarter remains after two",
      abs(spread_share(25.0, 25.0) - 0.5) < 1e-12 and abs(spread_share(50.0, 25.0) - 0.75) < 1e-12)
check("however long it has had, the share never exceeds one", spread_share(1.0e6, 25.0) <= 1.0)
check("a negative age (the clock before completion) spreads nothing", spread_share(-5.0, 25.0) == 0.0)

# --- SCENARIO (wiring): civ_diffusion reads the built node's age through the diffusion category's half-life, and is
# zero for a node outside the four categories.
s = unopened_sim(civ="rome_100ad")
check("scenario: civ_diffusion is zero for a technology nobody has built",
      s.civ_diffusion(_FOOD_NODE) == 0.0, s.civ_diffusion(_FOOD_NODE))
s.done.add(_FOOD_NODE); s.done_year[_FOOD_NODE] = s.year
s.year += 25   # one DIFFUSION_HALF_LIFE_YEARS["food"]
_half = s.civ_diffusion(_FOOD_NODE)
check("scenario: ...and about half-spread after the food half-life once built",
      0.45 < _half < 0.55, _half)
check("scenario: a node with none of the four diffusible traits never diffuses at all",
      s.civ_diffusion("workshop_first") == 0.0
      and not any(trait in ("food", "medical", "military", "information")
                  for trait in NODES["workshop_first"]["traits"]),
      NODES["workshop_first"]["traits"])

# --- military is the one category read from the state's own holdings: the
# government actor's know-how, not a curve over time (Complaint 287).
s_nopatron = unopened_sim(civ="rome_100ad")
for k in _MIL_NODES2:
    s_nopatron.done.add(k); s_nopatron.done_year[k] = s_nopatron.year
s_nopatron.year += 200
s_patron = unopened_sim(civ="rome_100ad")
run_it(s_patron, "patron_imperial")
for k in _MIL_NODES2:
    s_patron.done.add(k); s_patron.done_year[k] = s_patron.year
s_patron.year += 200
check("scenario: military technology the founder built never reaches the state's "
      "hands however long it has had, unless the government holds it",
      s_nopatron.state_military_diffusion() == 0.0
      and s_patron.state_military_diffusion() == 0.0, s_patron.state_military_diffusion())
s_patron.state_treasury().knowledge.update(_MIL_NODES2)
check("scenario: ...but once the government actor holds it, it genuinely has - the "
      "user's own 'give the Roman government cannons' scenario",
      s_patron.state_military_diffusion() > 0.5, s_patron.state_military_diffusion())

# =============================================================================
# DISEASE: the country is harder to kill wholesale, once ITS OWN medicine
# has spread - not only the founder's private, has()-gated hedge (`relief`
# in _shocks, unchanged by any of this). The user's own example: invent the
# cure or vaccine for a pandemic and it becomes a minor sickness.
def _plague_line2(civ, hazard_substr, med_nodes, years_before, capital=1e9):
    household = with_hazard(unopened_sim(civ=civ, capital=capital), ANTONINE if civ == "rome_100ad" else BLACK_DEATH)
    for node_id in med_nodes:
        household.done.add(node_id)
    household.scholars, household.artisans = 50.0, 200.0
    for trade in list(household.employees):
        household.employees[trade] = 50.0
    haz = next(hazard for hazard in household.civ["hazards"] if hazard_substr in hazard["name"])
    years_started = haz["years"][0]
    household.year = years_started
    household.done_year = {node_id: years_started - years_before for node_id in med_nodes}
    household.rng = random.Random(1)
    household._shocks(years_started)
    return next((message for _year, message in household.log if hazard_substr in message), "")


# presentation: the hazard log line's wording (whether it says the toll was softened)
_antonine_fresh = _plague_line2("rome_100ad", "Antonine plague", _MED_NODES, 0)
_antonine_old = _plague_line2("rome_100ad", "Antonine plague", _MED_NODES, 300)
check("scenario: medicine the founder has only JUST built gives the empire at large "
      "no relief yet - diffusion has not had time to happen",
      "Empire-wide, population -28%" in _antonine_fresh
      and "softer" not in _antonine_fresh,
      _antonine_fresh)
check("scenario: the SAME medicine, diffused through three centuries, visibly softens "
      "the empire-wide toll - the user's 'minor sickness' claim, answered "
      "against the empire's own figure, never against the founder's",
      "softer" in _antonine_old
      and "Empire-wide, population -28%" not in _antonine_old,
      _antonine_old)

_black_death = _plague_line2("england_1300", "Black Death", _MED_NODES, 400)
check("scenario: diffused medicine four centuries deep can turn even the Black Death "
      "into a barely-registering empire-wide event - the user's example by "
      "name",
      "barely registers" in _black_death or "softer" in _black_death,
      _black_death)

check("medical diffusion relief has no fixed ceiling: full coverage with a capable state removes the epidemic entirely",
      medical_relief(1.0, 0.5, 1.0) >= 1.0)
check("...with no state the guidance is followed by the base share alone",
      abs(medical_relief(1.0, 0.5, 0.0) - 0.5) < 1e-12)
check("...no coverage, no relief; and relief never exceeds one", medical_relief(0.0, 0.5, 1.0) == 0.0
      and medical_relief(5.0, 0.5, 1.0) == 1.0)

# --- and this never touches the founder's own, personal figure (`loss`), nor sack_chance/output_factor, which are a
# different category entirely: no medical node is a counter of war's kinds (data, no game).
_medical_war_counters = [
    (node_id, counter["kind"]) for node_id, node in sorted(NODES.items()) if "medical" in node.get("traits", ())
    for counter in (node.get("mechanics") or {}).get("hazard_counters") or ()
    if counter["kind"] in ("output_factor", "sack_chance")]
s_bare_h = unopened_sim(civ="rome_100ad")   # only read below, shared with later read-only checks
check("diffused medicine gives no relief against output_factor or sack_chance: those are war's categories, not "
      "medicine's", not _medical_war_counters, _medical_war_counters)

# =============================================================================
# WAR: a state that is actually armed, not only a founder who privately is,
# loses less and is sacked less often. The user's cannon example, and the
# line the brief draws around it: the Gothic wars cost the country less -
# they do not stop happening, and nothing here ever deletes a hazard or
# moves its calendar.
class ArmedState(HazardReliefMixin):
    """Just what hazard_relief_entries reads: no node counters, the founder's own strength nil, a state holding weapons."""
    HAZARD_COUNTERS = {}
    STATE_MIL_RELIEF_PER_WEAPON_OUTPUT = 0.04
    STATE_MIL_RELIEF_PER_WEAPON_SACK = 0.06

    def __init__(self, weapons):
        self.weapons = weapons

    def _military_war_relief(self):
        return 1.0, None

    def _state_military_diffusion_relief(self, per_weapon):
        return weapons_relief(per_weapon, self.weapons)

    def _entry_words(self, entry):
        return entry["label"]


_of_bare, _ = ArmedState(0).hazard_relief("output_factor")
_of_armed, _of_why = ArmedState(2).hazard_relief("output_factor")
_sk_bare, _ = ArmedState(0).hazard_relief("sack_chance")
_sk_armed, _sk_why = ArmedState(2).hazard_relief("sack_chance")
check("a state that holds the founder's weapons loses less trade to a dated war, and says why",
      _of_bare == 1.0 and abs(_of_armed - (1 - 0.04) ** 2) < 1e-12
      and any("state's own armies" in explanation for explanation in _of_why),
      (_of_bare, _of_armed, _of_why))
check("...and is less likely to be sacked, by the sack share per weapon and not the output share",
      _sk_bare == 1.0 and abs(_sk_armed - (1 - 0.06) ** 2) < 1e-12
      and any("state's own armies" in explanation for explanation in _sk_why),
      (_sk_bare, _sk_armed, _sk_why))
check("the relief is bounded on both fields, never enough on its own to erase a war's cost or a raid's chance",
      0.0 < _of_armed < 1.0 and 0.0 < _sk_armed < 1.0 and 0.0 < ArmedState(1000).hazard_relief("sack_chance")[0])
check("each weapon removes its share of what is left, so the first removes more than the next",
      (1.0 - ArmedState(1).hazard_relief("sack_chance")[0]) > (ArmedState(1).hazard_relief("sack_chance")[0]
                                                           - ArmedState(2).hazard_relief("sack_chance")[0]))

_rome_gothic = _hazard("rome_100ad", "Adrianople and the Gothic settlement")
check("the Gothic settlement hazard itself still has no `condition` and no "
      "change to its `years` - the war still happens on the historical "
      "date; only what it costs moves, never whether or when",
      "condition" not in _rome_gothic and _rome_gothic["years"] == [376, 405],
      _rome_gothic)

# =============================================================================
# INFORMATION: printing diffused past one printer's workshop makes
# schooling itself teach faster - the mechanical home the brief pointed at
# (literacy is already a real ceiling on trades), not a new, separate
# effect invented from nothing.
def _literacy_after(info_done, years=60):
    household = run_it(unopened_sim(civ="norse_900ad", capital=2000000.0), "school_founded")
    if info_done:
        household.done.add(_INFO_NODE); household.done_year[_INFO_NODE] = household.year - 150
    for i in range(1, years + 1):
        household.year += 1
        household.advance_society(household.year)
    return household.literacy("literacy_general")


_lit_no_info = _literacy_after(False)
_lit_with_info = _literacy_after(True)
check("scenario: a diffused printing press measurably speeds up how fast a running "
      "school raises general literacy, holding the school itself fixed - "
      "the user's fourth point given the mechanical home the brief named",
      _lit_with_info > _lit_no_info,
      (_lit_no_info, _lit_with_info))

# =============================================================================
# TOLD TO THE PLAYER, AND INSPECTABLE - not only a state variable. Gated to
# absent (not merely null) while dormant, because `state full` already sits
# within a few bytes of its own "stays readable" budget at the very start
# of a run (see that check elsewhere in this file) and a field present on
# every single call, even as null, would break it outright.
_wd_fresh = unopened_sim(civ="rome_100ad")
_wd_fresh.fog = True
_wd_start = S._agent_dispatch(_wd_fresh, NODES, {"cmd": "state", "full": True})
check("scenario: 'world_diffusion' is not merely null but genuinely ABSENT from "
      "`state full` at the start of a run - zero added bytes against an "
      "already nearly-full byte budget",
      "world_diffusion" not in _wd_start, sorted(_wd_start))

s_cli = unopened_sim(civ="rome_100ad")
s_cli.done.add(_FOOD_NODE); s_cli.done_year[_FOOD_NODE] = s_cli.year
for i in range(1, 31):
    s_cli.year += 1
    s_cli.advance_society(s_cli.year)
check("scenario: once something has genuinely diffused, world_diffusion_report is no "
      "longer None and names how much of farming the country has adopted",
      s_cli.world_diffusion_report() is not None
      and s_cli.world_diffusion_report()["food_and_farming_the_country_has_adopted"] > 0,
      s_cli.world_diffusion_report())

# =============================================================================
# DETERMINISM: civ_diffusion and everything built on it iterate self.done (a
# set) only through a fixed, sorted list of category ids, never a float sum
# whose order depends on PYTHONHASHSEED.
_DIFFUSION_SNAPSHOT_SRC = """
import sys
import random
from sim import simulator as S

T, P, N, W, G = S.load()
_l, O, _b = S.load_strategy('recommended', N, T['meta']['goal_node'])
s = S.Sim(N, O, random.Random(1), events=False, manual=True,
          civ=S.load_civ('rome_100ad'))
s.goal, s.done_year = T['meta']['goal_node'], {}
s.done.add('patron_imperial'); s.operating.add('patron_imperial')
for k in ('crop_rotation', 'sanitation_antisepsis', 'med_quarantine_sanitation',
          'germ_theory', 'gunpowder', 'mil_artillery_piece', 'printing_press'):
    s.done.add(k)
    s.done_year[k] = s.year
s._done_changed()
s.state_treasury().knowledge.update(('gunpowder', 'mil_artillery_piece'))
for _ in range(60):
    s.advance_society(s.year)
    s.year += 1
print(repr((round(s.food_diffusion_index(), 12),
            round(s.medical_diffusion_index(), 12),
            round(s.state_military_diffusion(), 12),
            round(s.information_diffusion_index(), 12))))
"""


def _diffusion_snapshot(seed_env):
    result = subprocess.run([sys.executable, "-c", _DIFFUSION_SNAPSHOT_SRC],
                        capture_output=True, text=True, timeout=60, cwd=ROOT,
                        env=dict(os.environ, PYTHONHASHSEED=seed_env))
    return result.stdout.strip() or ("ERROR: " + result.stderr[-300:])


_dif_a, _dif_b = _par_map(_diffusion_snapshot, ("0", "24680"))
check("scenario: the whole diffusion mechanism - food, medical, military, "
      "information and the population bonus it drives - gives identical "
      "results under a different PYTHONHASHSEED",
      _dif_a == _dif_b and not _dif_a.startswith("ERROR"), (_dif_a, _dif_b))


# A STARTING TECHNOLOGY IS SUPPOSED TO MATTER. fin_societas was left
# deliberately unwired on the grounds that Rome grants it in starting_techs,
# so any effect would be "a silent day-one buff to every Rome run, not a
# player choice". That reasoning was wrong: the starting_techs list is the
# mechanism by which these five civilisations differ, and Rome beginning with
# a legally recognised partnership while a Norse or Mexica founder must build
# one is the asymmetry, not a side effect of it. The legitimate half of the
# objection was the word "silent", so the advantage is attributed.
_soc_room = {}
_soc_sims = {}
for _civ in ("rome_100ad", "han_china_100ad", "norse_900ad", "england_1300",
             "mexica_1500"):
    _s_soc = _soc_sims[_civ] = s_bare_h if _civ == "rome_100ad" else unopened_sim(civ=_civ)
    _soc_room[_civ] = (_s_soc.has("fin_societas"), _s_soc.labour.supervision_room())
check("scenario: Rome alone starts with a partnership, and so oversees more people in "
      "its first year than the four civilisations that must build one",
      _soc_room["rome_100ad"][0]
      and not any(_soc_room[civ_id][0] for civ_id in _soc_room if civ_id != "rome_100ad")
      and all(_soc_room["rome_100ad"][1] > _soc_room[civ_id][1]
              for civ_id in _soc_room if civ_id != "rome_100ad"), _soc_room)
check("scenario: ...and the four without it all start level with each other, so this is "
      "the one technology doing it and not a population effect",
      len({round(_soc_room[civ_id][1], 3) for civ_id in _soc_room
           if civ_id != "rome_100ad"}) == 1, _soc_room)

# AND IT IS NOT SILENT. The breakdown names the partnership, and it is the
# same walk supervision_room sums, so it cannot drift from the total.
_s_soc_r = _soc_sims["rome_100ad"]
# presentation: the capacity screen names its source
_soc_cap = S._agent_dispatch(_s_soc_r, NODES, {"cmd": "capacity"})
_soc_sc = _soc_cap.get("spare_capacity") or {}
_soc_rows = _soc_sc.get("and_where_that_comes_from") or []
check("scenario: the capacity screen says where the headroom comes from, and names the "
      "partnership rather than leaving a Roman player to wonder",
      any(source_row.get("source") == "fin_societas" for source_row in _soc_rows), _soc_rows)
check("scenario: ...and the rows add up to exactly the figure they explain, for every "
      "civilisation, so the breakdown cannot drift from the total",
      all(abs(sum(source_row["people"] for source_row in _soc_sims[civ_id].labour.supervision_room_from())
              - _soc_sims[civ_id].labour.supervision_room()) < 1e-9
          for civ_id in _soc_sims),
      [(civ_id, sum(source_row["people"] for source_row in _soc_sims[civ_id].labour.supervision_room_from()),
        _soc_sims[civ_id].labour.supervision_room())
       for civ_id in ("rome_100ad", "norse_900ad")])

# HOW A SCRIPT DRIVES THIS GAME, said where a script author will find it. Every
# AI agent that has played built a tmux or FIFO harness to hold the process
# open, because the one place that explained otherwise was filed under
# "sittings" - a word about a person at a keyboard over several evenings.
# presentation: the help pages' wording
_s_sit = s_bare_h
for _alias in ("script", "agent", "batch", "oneshot", "non-interactive"):
    _h = S._agent_dispatch(_s_sit, NODES, {"cmd": "help", "topic": _alias})
    check("'help %s' reaches the page that explains one command per "
          "invocation" % _alias,
          "invocation" in json.dumps(_h).lower()
          and "--session" in json.dumps(_h), _alias)
_h_sit = S._agent_dispatch(_s_sit, NODES, {"cmd": "help", "topic": "sittings"})
check("...and it gives the actual command line, not only the idea of it",
      "simulator.py play --session" in json.dumps(_h_sit), _h_sit)
_welcome = S._agent_dispatch(_s_sit, NODES, {"cmd": "help"})
check("and the opening briefing says it too, since that is the one screen "
      "every player reads before building a harness",
      "hold this process open" in json.dumps(_welcome).lower(),
      sorted((_welcome.get("welcome") or {}).keys())[:12])
