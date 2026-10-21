"""Population-wide mortality shocks (the Black Death, the Antonine plague) driven through a game, and the save/load
round trip of the cohort state they depend on.

The rules are called with figures in test_mortality_shock_rules (the exposure a hedge leaves, the wage premium, the
recovery shape, the classification and wording of a wave) and test_cross_system_invariants (the cohort cut). Three named
scenarios remain: a hazard fired through the engine (the society's loss, the wage premium that follows, the logged
cascade), a shocked game through a real save and resume, and the hazard line's structured facts at three levels of
defence.
"""
from .harness import *  # noqa: F401,F403
from sim.refusal import cause_of, facts_of
from .plague_fixture import ANTONINE, BLACK_DEATH, with_hazard


def plague_sim(civ, **options):
    return with_hazard(unopened_sim(civ=civ, **options), ANTONINE if civ == "rome_100ad" else BLACK_DEATH)


# --- JOB 2: A PLAGUE MOVES THE WHOLE SOCIETY, NOT JUST YOUR OWN HOUSEHOLD. A
# playtester watched the Black Death take a third of their own staff and
# nothing else happen anywhere in the game, and asked why a mortality event
# this size left the rest of the economy untouched - no dearer hiring, no
# dearer wages, nothing. self._apply_population_mortality_shock (core.py,
# fed by _shocks in society.py) is the fix: the hazard now also costs the
# whole labour market people, and a smaller labour market pays more to hire
# from.
#
# WIRING MILESTONE 4 (docs/architecture/WIRING_MILESTONE_4.md) REWRITE:
# these checks read self.population.total and the computed
# self.pop_scale/self.wage_index properties, not a scalar deficit
# (self.pop_deficit, self._pop_recovery_years) decaying on a hand-set
# exponential clock. sim/world/demography.py's own test suite FALSIFIES
# that scalar shape (see its module docstring): two populations losing an
# identical 30% in one year, one sparing working-age adults and one not,
# diverge afterward, which a clock that only knows a SIZE cannot
# reproduce. self.population (a demography.Population) is the cohort model
# that can - see core.py's own comment above pop_scale for the full
# account of what changed and why.
s = plague_sim("england_1300")
_normal_wage = s.wage_index
_pop_before = s.population.total
s.year = 1348
s._shocks(1348)
_pop_loss_fraction = 1.0 - s.population.total / _pop_before
check("scenario: the Black Death costs the whole society people, not only your own household",
      abs(_pop_loss_fraction - 0.45) < 1e-6, _pop_loss_fraction)

# --- your own quarantine (plague_preparedness) protects your own household
# - that is what hazard_relief already does to the personal staff_loss above
# - and must NOT also soften the society-wide figure: the rest of the world
# never built your hedge.
s2 = plague_sim("england_1300")
s2.done.add("plague_preparedness"); s2.operating.add("plague_preparedness")
s2._done_changed()
_pop2_before = s2.population.total
s2.year = 1348
s2._shocks(1348)
_pop2_loss_fraction = 1.0 - s2.population.total / _pop2_before
check("scenario: a hedge against plague shields your own staff, not the whole population's labour market",
      abs(_pop2_loss_fraction - 0.45) < 1e-6, _pop2_loss_fraction)

# --- scarcer labour is dearer labour immediately: the event and the economy
# screen must not disagree for the remainder of the year in which it fires.
_shock_wage = s.wage_index
check("scenario: wages rise immediately after a mortality shock, because the labour market just got smaller",
      _shock_wage > _normal_wage * 1.2, (_normal_wage, _shock_wage))
s.year = 1349
s._demographic_recovery(1349)
check("scenario: wages remain elevated the year after a mortality shock",
      s.wage_index > _normal_wage * 1.2, (_normal_wage, s.wage_index))
check("scenario: the wage cascade is logged, so a player can see why their wage bill jumped",
      any(cause_of(message) == "wage_cascade" and facts_of(message)["wage_premium_percent"] > 0
          for _year, message in s.log),
      [message for _year, message in s.log if "wage" in message.lower()])

# --- JOB 2b: THE LIVE SAVE/LOAD BUG WIRING MILESTONE 4 FIXES.
# docs/architecture/WIRING_MILESTONE_4.md SS3: none of the nine attributes
# the OLD scalar model used were ever in SAVE_FIELDS, so a demographic
# shock's wage premium was silently wiped the moment a --session game was
# resumed in a fresh process (cli.py reconstructs a brand-new Sim from the
# civilisation file on every invocation, then load_state()s the save over
# it - CLAUDE.md SS5's "every single command is a save followed by a load"
# describes exactly this sequence). self.population's three cohort counts
# are now in SAVE_FIELDS (proto/saveload.py) via the pop_children/
# pop_working_age/pop_elderly forwarding properties (core.py) - this drives
# a hazard through the REAL save/reload cycle cli.py actually uses, the one
# gap every existing demography-adjacent test left open (none of them
# drove a hazard through save_state/load_state in the same process).
s7 = plague_sim("england_1300")
_pop7_before = s7.population.total
s7.year = 1348
s7._shocks(1348)
_shocked_children = s7.population.children
_shocked_working_age = s7.population.working_age
_shocked_elderly = s7.population.elderly
check("scenario: the save/load round trip below exercises a real shock, not a no-op",
      s7.population.total < _pop7_before * 0.99, s7.population.total)
_save7 = os.path.join(HERE, "_test_wiring_milestone4_pop_save.json")
S.save_state(s7, _save7)
# A FRESH Sim, built the way cli.py's --session resume really does it
# (Sim(...) from the civilisation file, THEN load_state over it) - not the
# same object with its cohorts merely re-read, which would pass even if
# SAVE_FIELDS were still missing every one of these three names.
s7_fresh = S.Sim(NODES, ORDER, random.Random(1), events=False, manual=True,
                 civ=S.load_civ("england_1300"))
s7_fresh.goal, s7_fresh.done_year = GOAL, {}
S.load_state(s7_fresh, _save7)
os.remove(_save7)
check("a demographic shock's cohort counts survive a real save/reconstruct/"
      "load cycle bit-for-bit - the exact failure mode the OLD pop_deficit/"
      "wage_index/pop-scale trio had, live, because none of the nine "
      "attributes _demographic_recovery used were ever in SAVE_FIELDS",
      (s7_fresh.population.children == _shocked_children
       and s7_fresh.population.working_age == _shocked_working_age
       and s7_fresh.population.elderly == _shocked_elderly),
      (s7_fresh.population, (_shocked_children, _shocked_working_age, _shocked_elderly)))
check("...and the wage premium that cohort state drives is therefore ALSO "
      "intact after the round-trip, not silently reset to baseline",
      s7_fresh.wage_index > s7_fresh._wage_index_base * 1.2, s7_fresh.wage_index)

# =============================================================================
# SEVERITY HONESTY: the words attached to a dated hazard must match `loss`,
# the number the mitigation mechanic actually applied, never `raw`, the
# hazard's own historical unmitigated figure - a player whose sanitation and
# quarantine cut the Antonine plague's 28% down to a fraction of a percent
# still read "(would have been -28%: ...)" glued onto the same sentence and
# reasonably called it a catastrophe.
def _plague_line(mitigated_nodes):
    household = plague_sim("rome_100ad", capital=1000000.0)
    if mitigated_nodes:
        run_it(household, *mitigated_nodes)
    household.scholars, household.artisans = 50.0, 200.0
    for trade in list(household.employees):
        household.employees[trade] = 50.0
    household.rng = random.Random(1)          # a seed that rolls the 32% plague check
    household.year = 165
    household._shocks(165)
    return next(message for _year, message in household.log
                if getattr(message, "kind", None) == "hazard_hit" and message.facts.get("hazard") == "Antonine plague")


_HEAVY = ["sanitation_antisepsis", "med_quarantine_sanitation", "germ_theory",
          "md2_isolation_hospital", "med_vaccination_progression",
          "md2_vaccine_smallpox", "md2_vaccine_plague", "md2_vaccine_typhoid",
          "md2_sand_filtration", "soap_hard", "med_nursing_profession",
          "plague_preparedness", "crop_rotation", "ag2_silage_silo",
          "fud_canning_appert_method"]
_line_none = _plague_line([])
_line_heavy = _plague_line(_HEAVY)
_line_some = _plague_line(["sanitation_antisepsis", "med_quarantine_sanitation"])
check("scenario: an unmitigated plague is told with no defence, and the empire-wide toll as a separate fact",
      _line_none.kind == "hazard_hit" and _line_none.facts["defence"] == "plain"
      and _line_none.facts["national_toll_percent"] == 28, _line_none.facts)
check("scenario: a heavily mitigated plague is told as held off, and the toll is still the empire's",
      _line_heavy.facts["defence"] == "held_off" and _line_heavy.facts["national_toll_percent"] == 28,
      _line_heavy.facts)
check("scenario: a partly mitigated plague is told as softened, and the toll is still the empire's",
      _line_some.facts["defence"] == "softened" and _line_some.facts["national_toll_percent"] == 28,
      _line_some.facts)
