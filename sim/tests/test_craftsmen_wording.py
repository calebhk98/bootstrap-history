"""SCENARIO: craftsmen_wording: the wiring of civ diffusion, the state's military know-how, literacy and the supply of supervision
through a game. The diffusion rules called with figures built here are in test_diffusion_categories_rule. Run with
`--only craftsmen_wording`."""
from .harness import *  # noqa: F401,F403

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
# INFORMATION: printing diffused past one printer's workshop makes
# schooling itself teach faster - the mechanical home the brief pointed at
# (literacy is already a real ceiling on trades), not a new, separate
# effect invented from nothing.
def _literacy_after(info_done, years=1):
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
for _ in range(5):
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
    _s_soc = _soc_sims[_civ] = unopened_sim(civ=_civ)
    _soc_room[_civ] = (_s_soc.has("fin_societas"), _s_soc.labour.supervision_room())
check("scenario: Rome alone starts with a partnership, and so oversees more people in "
      "its first year than the four civilisations that must build one",
      _soc_room["rome_100ad"][0]
      and not any(_soc_room[civ_id][0] for civ_id in _soc_room if civ_id != "rome_100ad")
      and all(_soc_room["rome_100ad"][1] > _soc_room[civ_id][1]
              for civ_id in _soc_room if civ_id != "rome_100ad"), _soc_room)
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
