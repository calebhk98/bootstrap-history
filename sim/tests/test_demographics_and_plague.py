"""Population-wide mortality shocks (the Black Death, the Antonine
plague), the wage premium they leave behind, the food technologies that
slowly raise the population, and the save/load round-trip of the cohort
state all of this depends on.

Regrouped from test_round10.py - see CLAUDE.md's test-file reorganisation
note. Checks moved verbatim; each one's own comment explains the break it
guards.
"""
from .harness import *  # noqa: F401,F403


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
s = sim(civ="england_1300")
_normal_wage = s.wage_index
_pop_before = s.population.total
s.year = 1348
s._shocks(1348)
_pop_loss_fraction = 1.0 - s.population.total / _pop_before
check("the Black Death costs the whole society people, not only your own "
      "household",
      abs(_pop_loss_fraction - 0.45) < 1e-6, _pop_loss_fraction)

# --- your own quarantine (plague_preparedness) protects your own household
# - that is what hazard_relief already does to the personal staff_loss above
# - and must NOT also soften the society-wide figure: the rest of the world
# never built your hedge.
s2 = sim(civ="england_1300")
s2.done.add("plague_preparedness"); s2.operating.add("plague_preparedness")
s2._done_changed()
_pop2_before = s2.population.total
s2.year = 1348
s2._shocks(1348)
_pop2_loss_fraction = 1.0 - s2.population.total / _pop2_before
check("a hedge against plague shields your own staff, not the whole "
      "population's labour market",
      abs(_pop2_loss_fraction - 0.45) < 1e-6, _pop2_loss_fraction)

# --- scarcer labour is dearer labour immediately: the event and the economy
# screen must not disagree for the remainder of the year in which it fires.
_shock_wage = s.wage_index
check("wages rise immediately after a mortality shock, because the labour "
      "market just got smaller",
      _shock_wage > _normal_wage * 1.2, (_normal_wage, _shock_wage))
s.year = 1349
s._demographic_recovery(1349)
check("wages remain elevated the year after a mortality shock",
      s.wage_index > _normal_wage * 1.2, (_normal_wage, s.wage_index))
check("the wage cascade is LOGGED, so a player can see why their wage bill "
      "jumped instead of having to notice it in the accounts",
      any("running" in message and "above normal" in message for _year, message in s.log),
      [message for _year, message in s.log if "wage" in message.lower()])

# --- recovery is now EMERGENT from self.population's own vital rates
# (births and deaths on the surviving cohort structure) rather than a
# clock this engine sets - demography.py's own docstring says the model is
# not perfectly self-replicating even at exact subsistence, so a shocked
# population does not snap back to its pre-shock level; it resumes
# ordinary (near-zero net) growth from its new, smaller base. That is a
# real, checkable prediction of the demographic model, not a number this
# test can assert to a specific decade the way the old fixed 150-year
# clock could - so what this checks is only the SHAPE the old test's own
# brief asked for: the premium stays substantial for a long time (decades),
# it does not evaporate in a handful of years, and it never grows without
# bound either.
s4 = sim(civ="england_1300")
s4.year = 1348
s4._shocks(1348)
for _yr in range(1349, 1349 + 50):
    s4._demographic_recovery(_yr)
_mid_premium = s4.wage_index / _normal_wage - 1.0
for _yr in range(1349 + 50, 1349 + 150):
    s4._demographic_recovery(_yr)
_end_premium = s4.wage_index / _normal_wage - 1.0
check("fifty years on, the wage premium from the Black Death is still "
      "substantial, not gone in a handful of years",
      _mid_premium > 0.10, _mid_premium)
check("...and it has not grown without bound a century later either - this "
      "is a mortality shock working through births and deaths, not a "
      "runaway",
      _end_premium < _mid_premium * 2.0 + 0.10, (_mid_premium, _end_premium))

# --- a milder mortality event costs the society less than a more severe
# one, in proportion to its own severity, not some fixed effect regardless
# of size - the same relative-severity property the old _pop_recovery_years
# clock asserted via its own recovery horizon, now checked directly on the
# population loss itself, which is the number that actually drives
# wage_index under the new model.
s5 = sim(civ="rome_100ad")
_pop5_before = s5.population.total
for _yr in range(165, 181):
    s5.year = _yr
    s5._shocks(_yr)
    if s5.population.total < _pop5_before:
        break
_antonine_loss_fraction = 1.0 - s5.population.total / _pop5_before
check("the Antonine plague (28% of staff) costs the society a smaller "
      "population fraction than the Black Death's 45%, scaled to size",
      0 < _antonine_loss_fraction < 0.45, _antonine_loss_fraction)

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
s7 = sim(civ="england_1300")
_pop7_before = s7.population.total
s7.year = 1348
s7._shocks(1348)
_shocked_children = s7.population.children
_shocked_working_age = s7.population.working_age
_shocked_elderly = s7.population.elderly
check("the save/load round-trip test below actually exercises a real "
      "shock, not a no-op",
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
      "wage_index/_pop_scale_base trio had, live, because none of the nine "
      "attributes _demographic_recovery used were ever in SAVE_FIELDS",
      (s7_fresh.population.children == _shocked_children
       and s7_fresh.population.working_age == _shocked_working_age
       and s7_fresh.population.elderly == _shocked_elderly),
      (s7_fresh.population, (_shocked_children, _shocked_working_age, _shocked_elderly)))
check("...and the wage premium that cohort state drives is therefore ALSO "
      "intact after the round-trip, not silently reset to baseline",
      s7_fresh.wage_index > s7_fresh._wage_index_base * 1.2, s7_fresh.wage_index)

# --- JOB 3: A FOOD TECHNOLOGY RAISES THE POPULATION, SLOWLY. Crop
# rotation, the three-field system, New World crops and the like should feed
# back into a bigger labour market eventually, but more food shows up in the
# headcount a generation later, not the season it is first sown - so
# apply_tech_effects must queue the gain rather than apply it the year the
# node completes.
#
# THE VEHICLE CANNOT BE A DISEASE TECHNOLOGY, such as `sanitation_
# antisepsis`: the eight DISEASE technologies (Sim.DISEASE_BURDEN_TECH_IDS)
# do not queue a scalar here at all - they drive `_disease_burden()` live,
# and the generational lag this ramp was imitating falls out of the cohort
# model instead - people stop dying the year the latrine opens, and the
# headcount answers over the following decades because that is how cohorts
# work. A hardcoded forty-year ramp is not needed where the simulation
# produces the lag itself (CLAUDE.md SS3.1), so for disease there is none,
# and test_disease_burden_wiring.py is what guards the mechanism that
# produces it.
# The five FOOD entries sharing the `population` field still queue exactly as
# before, which is what this job tests. `crop_rotation` carries the same 0.02
# weight `sanitation_antisepsis` did, so every number below is unchanged.
s6 = sim(civ="rome_100ad")
_base_pop = s6._pop_scale_base
s6.apply_tech_effects("crop_rotation")
check("a population-raising technology does not move the population the "
      "instant it completes",
      s6._pop_scale_base == _base_pop, s6._pop_scale_base)
for _yr in range(100, 100 + 40):
    s6._demographic_recovery(_yr)
check("...but it has fully landed by the end of its forty-year ramp",
      abs(s6._pop_scale_base - (_base_pop + 0.02)) < 1e-6, s6._pop_scale_base)
check("...and the gain stops growing once it has landed, rather than "
      "compounding forever",
      not s6._pop_tech_pending, s6._pop_tech_pending)
s6.apply_tech_effects("crop_rotation")
for _yr in range(140, 140 + 20):
    s6._demographic_recovery(_yr)
check("halfway through a SECOND such technology's ramp, only half of its "
      "own gain has landed - the ramp does not dump the total on year one",
      abs(s6._pop_scale_base - (_base_pop + 0.02 + 0.01)) < 1e-6,
      s6._pop_scale_base)

# =============================================================================
# SEVERITY HONESTY: the words attached to a dated hazard must match `loss`,
# the number the mitigation mechanic actually applied, never `raw`, the
# hazard's own historical unmitigated figure - a player whose sanitation and
# quarantine cut the Antonine plague's 28% down to a fraction of a percent
# still read "(would have been -28%: ...)" glued onto the same sentence and
# reasonably called it a catastrophe.
def _plague_line(mitigated_nodes):
    household = sim(civ="rome_100ad", capital=1000000.0)
    if mitigated_nodes:
        run_it(household, *mitigated_nodes)
    household.scholars, household.artisans = 50.0, 200.0
    for trade in list(household.employees):
        household.employees[trade] = 50.0
    household.rng = random.Random(1)          # a seed that rolls the 32% plague check
    household.year = 165
    household._shocks(165)
    return next((message for _year, message in household.log if "Antonine plague" in message), "")


_HEAVY = ["sanitation_antisepsis", "med_quarantine_sanitation", "germ_theory",
          "md2_isolation_hospital", "med_vaccination_progression",
          "md2_vaccine_smallpox", "md2_vaccine_plague", "md2_vaccine_typhoid",
          "md2_sand_filtration", "soap_hard", "med_nursing_profession",
          "plague_preparedness", "crop_rotation", "ag2_silage_silo",
          "fud_canning_appert_method"]
_line_none = _plague_line([])
_line_heavy = _plague_line(_HEAVY)
_line_some = _plague_line(["sanitation_antisepsis", "med_quarantine_sanitation"])
check("an unmitigated plague states its own historical rate plainly",
      "staff -28%" in _line_none, _line_none)
check("a heavily mitigated plague's OWN clause never re-quotes the "
      "historical -28% as if it were the outcome - only the near-zero "
      "figure the mechanic actually applied",
      "held off almost entirely" in _line_heavy
      and "would have been" not in _line_heavy
      and "staff -28%" not in _line_heavy.split(".")[0],
      _line_heavy)
check("a partially mitigated plague is 'softened', not 'held off almost "
      "entirely' and not silent about the hedge either",
      "softened by" in _line_some, _line_some)
check("the empire-wide toll is still told, in every case, as a separate "
      "fact explicitly not the household's own experience",
      all("Empire-wide, population -28%" in line and "either way" in line
          for line in (_line_none, _line_heavy, _line_some)),
      (_line_none, _line_heavy, _line_some))
