"""craftsmen_wording: regression checks, run individually with `--only craftsmen_wording`."""
from .harness import *  # noqa: F401,F403

# ===========================================================================
# "What does it mean when it says I need 2.13 craftsmen?" - wording only,
# no arithmetic changed anywhere below.
# ===========================================================================

# --- the standing-staff explanation (self.scholars/self.artisans/employees,
# a genuine headcount under a continuous attrition model) is written ONCE
# and read back identically by `state` and `labour`, never two answers to
# the same question.
s = sim(capital=1e6)
s.artisans, s.scholars = 1.6, 0.4
_st = S._agent_dispatch(s, NODES, {"cmd": "state", "full": True})
_lb = S._agent_dispatch(s, NODES, {"cmd": "labour"})
check("`state` explains a fractional standing-staff count as a continuous "
      "full-time-equivalent, not a chopped-up person",
      _st.get("staff_are_fractional_because")
      and "not a count of whole people" in _st["staff_are_fractional_because"],
      _st.get("staff_are_fractional_because"))
check("...and `labour` gives the identical explanation, word for word - "
      "one rule, not two that could disagree",
      _lb.get("staff_are_fractional_because") == _st.get("staff_are_fractional_because"),
      (_lb.get("staff_are_fractional_because"), _st.get("staff_are_fractional_because")))
s_whole = sim(capital=1e6)
s_whole.artisans, s_whole.scholars = 2.0, 1.0
_st_whole = S._agent_dispatch(s_whole, NODES, {"cmd": "state", "full": True})
check("...and says nothing at all when the staff genuinely is whole numbers "
      "- a footnote only where one is needed",
      _st_whole.get("staff_are_fractional_because") is None,
      _st_whole.get("staff_are_fractional_because"))

# --- the SEPARATE, and separately confusing, "2.13 craftsmen" a concern
# wants to stay open (venture_hands - a continuous share of a person's
# YEAR, scaled by revenue, not a headcount at all) is now named as such
# everywhere it is shown, not left for a player to read as a body count.
s_shut = sim(capital=10_000_000.0)
for _p in S.closure(NODES, "lens_grinding"):
    s_shut.done.add(_p)
s_shut.done.add("lens_grinding")
s_shut._done_changed()
_why_sg = S._agent_dispatch(s_shut, NODES, {"cmd": "why", "id": "lens_grinding"})
check("`why`'s staff_to_keep_it_open is still exactly venture_hands's own "
      "number - the wording fix changes nothing about what is computed",
      (_why_sg.get("staff_to_keep_it_open") or {}).get("artisans")
      == round(s_shut.venture_hands("lens_grinding")[1], 2),
      _why_sg.get("staff_to_keep_it_open"))
check("...and `why` now says outright that this is a share of a year, not "
      "a headcount, right beside the number that confused three players",
      _why_sg.get("these_are_a_share_of_their_year_not_a_headcount")
      and "not a headcount" in _why_sg["these_are_a_share_of_their_year_not_a_headcount"],
      _why_sg.get("these_are_a_share_of_their_year_not_a_headcount"))
_vent_sg = S._agent_dispatch(s_shut, NODES, {"cmd": "ventures"})
check("...and `ventures` - the other screen that shows venture_hands's "
      "numbers - carries the same explanation, not a different one",
      _vent_sg.get("these_are_a_share_of_their_year_not_a_headcount")
      == _why_sg.get("these_are_a_share_of_their_year_not_a_headcount"),
      _vent_sg.get("these_are_a_share_of_their_year_not_a_headcount"))

# --- the `stuck` advice sentence that measurably confused a player ("2.13
# craftsmen to supervise" with no explanation at all) keeps the exact words
# a prior regression already checks for, and now also says why.
_stuck_sg = S._agent_dispatch(s_shut, NODES, {"cmd": "stuck"})
_reason_sg = next((reason for reason in _stuck_sg["what_is_holding_you_up"]
                   if isinstance(reason, dict)
                   and reason.get("what", "").startswith("things you built")), None)
check("the `stuck` advice still names craftsmen specifically (unchanged "
      "substring an earlier regression already relies on)",
      _reason_sg is not None and "craftsmen to supervise" in _reason_sg.get("why", ""),
      _reason_sg)
check("...and now also says this is a continuous share of their year, not "
      "a headcount, in the same sentence rather than a footnote elsewhere",
      _reason_sg is not None and "not a headcount" in _reason_sg.get("why", ""),
      _reason_sg)

# --- the build-crew staffing refusal (craft_hands_available: staff PLUS
# hours already bought under contract) still refuses for the same reason
# and still says "craftsmen" (an existing regression checks this), and now
# explains the mixed count inline instead of implying a body count alone.
s_cc = sim(civ="rome_100ad", capital=1e6, manual=True, events=False)
_ok_cc, _why_cc = s_cc.start_reason("ag2_cold_store", ignore_trade=True)
check("the craftsmen staffing refusal still refuses for the same reason, "
      "unchanged arithmetic",
      not _ok_cc and "craftsmen" in _why_cc, _why_cc)
check("...and now says the figure counts contracted hours as a share of "
      "one more craftsman, not only bodies on the payroll",
      "share of" in _why_cc, _why_cc)

# ONE NAME FOR THE FOUNDER'S OWN WORK. The wage-work explanation called it
# "the practice" and then "the surgery" fourteen words later; a Roman founder
# selling a year of a smith's labour has neither a surgery nor two of them.
_s_wg = sim()
_wg = S._agent_dispatch(_s_wg, NODES, {"cmd": "work", "trade": "labourer",
                                       "hours": 2000})
check("the wage-work explanation names the founder's own work one way, and "
      "does not call it a surgery",
      "surgery" not in json.dumps(_wg).lower()
      and "practice" in (_wg.get("why") or ""), _wg.get("why"))
check("...and it still says what selling a year of labourer's time actually "
      "cost, in figures that subtract",
      abs((_wg.get("earned") or 0) - (_wg.get("it_cost_your_own_practice") or 0)
          - (_wg.get("so_you_are_up") or 0)) < 0.051,
      (_wg.get("earned"), _wg.get("it_cost_your_own_practice"),
       _wg.get("so_you_are_up")))

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

# --- civ_diffusion itself: zero until done, zero the instant it is done,
# grows with age, bounded at 1.0, deterministic over a sorted sum.
s = sim(civ="rome_100ad")
check("civ_diffusion is zero for a technology nobody has built",
      s.civ_diffusion(_FOOD_NODE) == 0.0, s.civ_diffusion(_FOOD_NODE))
s.done.add(_FOOD_NODE); s.done_year[_FOOD_NODE] = s.year
check("...and zero the instant it completes - diffusion takes time, it is "
      "not a second instant effect layered on apply_tech_effects",
      s.civ_diffusion(_FOOD_NODE) == 0.0, s.civ_diffusion(_FOOD_NODE))
s.year += 25   # one DIFFUSION_HALF_LIFE_YEARS["food"]
_half = s.civ_diffusion(_FOOD_NODE)
s.year += 1000
_far = s.civ_diffusion(_FOOD_NODE)
check("diffusion is about half-spread after one half-life and never "
      "exceeds 1.0 however long it has had",
      0.45 < _half < 0.55 and _far <= 1.0 + 1e-9,
      (_half, _far))
check("a node with none of the four diffusible traits never diffuses at "
      "all - this mechanism has nothing to say about a lathe or a ledger",
      s.civ_diffusion("workshop_first") == 0.0
      and not any(trait in ("food", "medical", "military", "information")
                  for trait in NODES["workshop_first"]["traits"]),
      NODES["workshop_first"]["traits"])

# --- military is the one category gated on a patron: the state, not the
# founder's private arsenal, is what the user's cannon example is about.
s_nopatron = sim(civ="rome_100ad")
for k in _MIL_NODES2:
    s_nopatron.done.add(k); s_nopatron.done_year[k] = s_nopatron.year
s_nopatron.year += 200
s_patron = sim(civ="rome_100ad")
run_it(s_patron, "patron_imperial")
for k in _MIL_NODES2:
    s_patron.done.add(k); s_patron.done_year[k] = s_patron.year
s_patron.year += 200
check("military technology the founder built never reaches the state's "
      "hands without a patron to hand it to, however long it has had",
      s_nopatron.state_military_diffusion() == 0.0, s_nopatron.state_military_diffusion())
check("...but WITH a patron, and enough time, it genuinely has - the "
      "user's own 'give the Roman government cannons' scenario",
      s_patron.state_military_diffusion() > 0.5, s_patron.state_military_diffusion())

# =============================================================================
# FOOD: the country eats better, and grows - on top of, never instead of,
# apply_tech_effects' own small instant population queue (see that
# mechanism's own regression checks elsewhere in this file).
s_food = sim(civ="rome_100ad")
s_food.granted.discard(_FOOD_NODE)
s_food.done.add(_FOOD_NODE); s_food.done_year[_FOOD_NODE] = s_food.year
_base0 = s_food._pop_scale_base
for i in range(1, 81):
    s_food.year += 1
    s_food.advance_society(s_food.year)
check("eighty years after New World-style crop rotation is done, the "
      "country's own baseline population has risen by a real, double-digit "
      "percentage - 'within a few decades ALL of Rome has significantly "
      "more food and a larger population', not a rounding error",
      s_food._pop_scale_base - _base0 > 0.08,
      s_food._pop_scale_base - _base0)
check("...and it is told in the log, not only in a state variable",
      any("no longer only on your own land" in message for _, message in s_food.log),
      [message for _, message in s_food.log if "no longer only on your own land" in message])

s_food_far = sim(civ="rome_100ad")
s_food_far.granted.discard(_FOOD_NODE)
s_food_far.done.add(_FOOD_NODE); s_food_far.done_year[_FOOD_NODE] = s_food_far.year
for i in range(1, 601):
    s_food_far.year += 1
    s_food_far.advance_society(s_food_far.year)
check("however long it has had, the food-diffusion population bonus never "
      "exceeds its own cap - this is bounded, not a runaway feedback loop",
      s_food_far._food_pop_bonus_applied <= s_food.FOOD_DIFFUSION_POP_BONUS_MAX + 1e-6,
      s_food_far._food_pop_bonus_applied)

s_nofood = sim(civ="rome_100ad")
for i in range(1, 81):
    s_nofood.year += 1
    s_nofood.advance_society(s_nofood.year)
check("a founder who never builds any food technology gets none of this - "
      "the bonus is earned, not a free drift",
      getattr(s_nofood, "_food_pop_bonus_applied", 0.0) == 0.0,
      getattr(s_nofood, "_food_pop_bonus_applied", 0.0))

# =============================================================================
# DISEASE: the country is harder to kill wholesale, once ITS OWN medicine
# has spread - not only the founder's private, has()-gated hedge (`relief`
# in _shocks, unchanged by any of this). The user's own example: invent the
# cure or vaccine for a pandemic and it becomes a minor sickness.
def _plague_line2(civ, hazard_substr, med_nodes, years_before, capital=1e9):
    household = sim(civ=civ, capital=capital)
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


_antonine_fresh = _plague_line2("rome_100ad", "Antonine plague", _MED_NODES, 0)
_antonine_old = _plague_line2("rome_100ad", "Antonine plague", _MED_NODES, 300)
check("medicine the founder has only JUST built gives the empire at large "
      "no relief yet - diffusion has not had time to happen",
      "Empire-wide, population -28%" in _antonine_fresh
      and "softer" not in _antonine_fresh,
      _antonine_fresh)
check("the SAME medicine, diffused through three centuries, visibly softens "
      "the empire-wide toll - the user's 'minor sickness' claim, answered "
      "against the empire's own figure, never against the founder's",
      "softer" in _antonine_old
      and "Empire-wide, population -28%" not in _antonine_old,
      _antonine_old)

_black_death = _plague_line2("england_1300", "Black Death", _MED_NODES, 400)
check("diffused medicine four centuries deep can turn even the Black Death "
      "into a barely-registering empire-wide event - the user's example by "
      "name",
      "barely registers" in _black_death or "softer" in _black_death,
      _black_death)

check("medical diffusion relief is capped, never total - no amount of "
      "diffused medicine makes a dated epidemic do nothing at all",
      sim(civ="rome_100ad").MEDICAL_DIFFUSION_RELIEF_CAP < 1.0,
      sim(civ="rome_100ad").MEDICAL_DIFFUSION_RELIEF_CAP)

# --- and this never touches the founder's own, personal figure (`loss`),
# nor sack_chance/output_factor, which are a different category entirely.
s_med_mil = sim(civ="rome_100ad")
for k in _MED_NODES:
    s_med_mil.done.add(k); s_med_mil.done_year[k] = s_med_mil.year - 300
_out_nomed = sim(civ="rome_100ad").hazard_relief("output_factor")[0]
_out_med = s_med_mil.hazard_relief("output_factor")[0]
_sack_nomed = sim(civ="rome_100ad").hazard_relief("sack_chance")[0]
_sack_med = s_med_mil.hazard_relief("sack_chance")[0]
check("diffused medicine gives no relief against output_factor or "
      "sack_chance - those are war's categories, not medicine's, the same "
      "boundary the pre-existing 'military gives no relief against staff "
      "loss' check already holds in the other direction",
      _out_med == _out_nomed and _sack_med == _sack_nomed,
      (_out_nomed, _out_med, _sack_nomed, _sack_med))

# =============================================================================
# WAR: a state that is actually armed, not only a founder who privately is,
# loses less and is sacked less often. The user's cannon example, and the
# line the brief draws around it: the Gothic wars cost the country less -
# they do not stop happening, and nothing here ever deletes a hazard or
# moves its calendar.
s_bare_h = sim(civ="rome_100ad")
s_armed_h = sim(civ="rome_100ad")
run_it(s_armed_h, "patron_imperial")
for k in _MIL_NODES2:
    s_armed_h.done.add(k); s_armed_h.done_year[k] = s_armed_h.year - 200
_of_bare, _ = s_bare_h.hazard_relief("output_factor")
_of_armed, _of_why = s_armed_h.hazard_relief("output_factor")
_sk_bare, _ = s_bare_h.hazard_relief("sack_chance")
_sk_armed, _sk_why = s_armed_h.hazard_relief("sack_chance")
check("a state that has actually absorbed the founder's cannon loses less "
      "trade to a dated war...",
      _of_armed < _of_bare
      and any("state's own armies" in explanation for explanation in _of_why),
      (_of_bare, _of_armed, _of_why))
check("...and is measurably less likely to be sacked, which before this "
      "change was true of the founder's OWN walls and guns but never of "
      "the state's - this is the user's cannon example",
      _sk_armed < _sk_bare
      and any("state's own armies" in explanation for explanation in _sk_why),
      (_sk_bare, _sk_armed, _sk_why))
check("the relief is bounded on both fields, never enough on its own to "
      "erase a war's cost or a raid's chance entirely",
      0.0 < _of_armed and 0.0 < _sk_armed,
      (_of_armed, _sk_armed))

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
def _literacy_after(info_done, years=200):
    household = run_it(sim(civ="norse_900ad", capital=2000000.0), "school_founded")
    if info_done:
        household.done.add(_INFO_NODE); household.done_year[_INFO_NODE] = household.year - 150
    for i in range(1, years + 1):
        household.year += 1
        household.advance_society(household.year)
    return household.civ["literacy_general"]


_lit_no_info = _literacy_after(False)
_lit_with_info = _literacy_after(True)
check("a diffused printing press measurably speeds up how fast a running "
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
_wd_start, _wd_out, _wd_rc = proto([{"cmd": "state", "full": True}],
                                   civ="rome_100ad", fog=True)
check("'world_diffusion' is not merely null but genuinely ABSENT from "
      "`state full` at the start of a run - zero added bytes against an "
      "already nearly-full byte budget",
      "world_diffusion" not in _wd_start[0], sorted(_wd_start[0]))

s_cli = sim(civ="rome_100ad")
s_cli.done.add(_FOOD_NODE); s_cli.done_year[_FOOD_NODE] = s_cli.year
for i in range(1, 91):
    s_cli.year += 1
    s_cli.advance_society(s_cli.year)
check("once something has genuinely diffused, world_diffusion_report is no "
      "longer None and names the population it has already added",
      s_cli.world_diffusion_report() is not None
      and s_cli.world_diffusion_report()["population_this_has_already_added"] > 0,
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
for _ in range(150):
    s.advance_society(s.year)
    s.year += 1
print(repr((round(s.food_diffusion_index(), 12),
            round(s.medical_diffusion_index(), 12),
            round(s.state_military_diffusion(), 12),
            round(s.information_diffusion_index(), 12),
            round(s._pop_scale_base, 12))))
"""


def _diffusion_snapshot(seed_env):
    result = subprocess.run([sys.executable, "-c", _DIFFUSION_SNAPSHOT_SRC],
                        capture_output=True, text=True, timeout=60, cwd=ROOT,
                        env=dict(os.environ, PYTHONHASHSEED=seed_env))
    return result.stdout.strip() or ("ERROR: " + result.stderr[-300:])


_dif_a, _dif_b = _par_map(_diffusion_snapshot, ("0", "24680"))
check("the whole diffusion mechanism - food, medical, military, "
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
for _civ in ("rome_100ad", "han_china_100ad", "norse_900ad", "england_1300",
             "mexica_1500"):
    _s_soc = sim(civ=_civ)
    _soc_room[_civ] = (_s_soc.has("fin_societas"), _s_soc.supervision_room())
check("Rome alone starts with a partnership, and so oversees more people in "
      "its first year than the four civilisations that must build one",
      _soc_room["rome_100ad"][0]
      and not any(_soc_room[civ_id][0] for civ_id in _soc_room if civ_id != "rome_100ad")
      and all(_soc_room["rome_100ad"][1] > _soc_room[civ_id][1]
              for civ_id in _soc_room if civ_id != "rome_100ad"), _soc_room)
check("...and the four without it all start level with each other, so this is "
      "the one technology doing it and not a population effect",
      len({round(_soc_room[civ_id][1], 3) for civ_id in _soc_room
           if civ_id != "rome_100ad"}) == 1, _soc_room)

# AND IT IS NOT SILENT. The breakdown names the partnership, and it is the
# same walk supervision_room sums, so it cannot drift from the total.
_s_soc_r = sim(civ="rome_100ad")
_soc_cap = S._agent_dispatch(_s_soc_r, NODES, {"cmd": "capacity"})
_soc_sc = _soc_cap.get("spare_capacity") or {}
_soc_rows = _soc_sc.get("and_where_that_comes_from") or []
check("the capacity screen says where the headroom comes from, and names the "
      "partnership rather than leaving a Roman player to wonder",
      any(source_row.get("source") == "fin_societas" for source_row in _soc_rows), _soc_rows)
check("...and the rows add up to exactly the figure they explain, for every "
      "civilisation, so the breakdown cannot drift from the total",
      all(abs(sum(source_row["people"] for source_row in sim(civ=civ_id).supervision_room_from())
              - sim(civ=civ_id).supervision_room()) < 1e-9
          for civ_id in ("rome_100ad", "han_china_100ad", "norse_900ad",
                     "england_1300", "mexica_1500")),
      [(civ_id, sum(source_row["people"] for source_row in sim(civ=civ_id).supervision_room_from()),
        sim(civ=civ_id).supervision_room())
       for civ_id in ("rome_100ad", "norse_900ad")])

# HOW A SCRIPT DRIVES THIS GAME, said where a script author will find it. Every
# AI agent that has played built a tmux or FIFO harness to hold the process
# open, because the one place that explained otherwise was filed under
# "sittings" - a word about a person at a keyboard over several evenings.
_s_sit = sim()
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
