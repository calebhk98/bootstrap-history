"""Which concerns a shortfall of people closes, and how many people a flagged concern is hired (Complaint 640): the
rules called on draws and totals built here, no game."""
QUICK_TOPIC = True

from .harness import *  # noqa: F401,F403
from sim.engine.staffing_choice import closures_for_shortfall, missing_when_opened, shortfalls_beyond, staffing_allowances
from sim.labour.labour_staff_controls import people_to_hire_for

# --- allowances
loose = staffing_allowances(["glassblower"], 4.0, 6.0, {"glassblower": 2.0}, 0.5)
strict = staffing_allowances(["glassblower"], 4.0, 6.0, {"glassblower": 2.0}, 0.5, strict=True)
check("a running concern is carried a half person of slack in scholars and craftsmen",
      loose["scholars"] == 4.5 and loose["craftsmen"] == 6.5, loose)
check("a foreman trade is carried what is held plus a sliver", abs(loose["glassblower"] - 2.01) < 1e-12, loose)
check("what `open` weighs carries no slack at all",
      strict == {"scholars": 4.0, "craftsmen": 6.0, "glassblower": 2.0}, strict)
check("a foreman trade nobody holds is allowed none", staffing_allowances(["smith"], 4.0, 6.0, {}, 0.5)["smith"] == 0.01)
check("the hand resources are not mistaken for foreman trades",
      set(staffing_allowances(["scholars", "craftsmen"], 1.0, 1.0, {}, 0.5)) == {"scholars", "craftsmen"})

# --- shortfalls
allowances = {"scholars": 4.5, "craftsmen": 6.5, "glassblower": 0.01}
short = shortfalls_beyond({"scholars": 5.0, "craftsmen": 6.5, "glassblower": 1.0}, allowances)
check("only what is held beyond the allowance is short",
      list(short) == ["glassblower", "scholars"] and abs(short["scholars"] - 0.5) < 1e-12
      and abs(short["glassblower"] - 0.99) < 1e-12, short)
check("holding exactly the allowance is not short", shortfalls_beyond({"craftsmen": 6.5}, allowances) == {})
check("a half person of shortfall inside the slack closes nothing",
      shortfalls_beyond({"craftsmen": 6.4}, allowances) == {})

# --- which concerns close
SCARCE = {"craftsmen": 5.0}


def shortfalls_of(totals):
    return shortfalls_beyond(totals, {"craftsmen": SCARCE["craftsmen"], "scholars": 100.0, "glassblower": 0.01})


draws = {"mill": {"craftsmen": 3.0}, "forge": {"craftsmen": 3.0}, "press": {"craftsmen": 3.0}}
worth = {"mill": 50.0, "forge": 10.0, "press": 30.0}
check("with enough people nothing closes", closures_for_shortfall(draws, worth, set(), lambda totals: {}) == [])
check("the concern earning least closes first, and only as many as cover the shortfall",
      closures_for_shortfall(draws, worth, set(), shortfalls_of) == ["forge", "press"],
      closures_for_shortfall(draws, worth, set(), shortfalls_of))
check("a concern flagged to stay staffed closes only after every unflagged one",
      closures_for_shortfall(draws, worth, {"forge"}, shortfalls_of) == ["press", "mill"],
      closures_for_shortfall(draws, worth, {"forge"}, shortfalls_of))
check("a tie in earnings breaks by name",
      closures_for_shortfall({"b": {"craftsmen": 3.0}, "a": {"craftsmen": 3.0}}, {"a": 1.0, "b": 1.0}, set(),
                             shortfalls_of) == ["a"])
refit = closures_for_shortfall({"a": {"craftsmen": 1.0}, "b": {"craftsmen": 4.0}, "c": {"craftsmen": 2.0}},
                               {"a": 1.0, "b": 2.0, "c": 3.0}, set(), shortfalls_of)
check("a concern chosen early that fits again once a later closure freed enough stays open", refit == ["b"], refit)
only_small = closures_for_shortfall({"big": {"craftsmen": 5.0}, "small": {"craftsmen": 1.5}},
                                    {"big": 90.0, "small": 1.0}, set(), shortfalls_of)
check("a shortfall one small concern covers closes only that one", only_small == ["small"], only_small)
check("a shortfall of a resource nothing holds closes nothing and does not loop",
      closures_for_shortfall({"mill": {"craftsmen": 1.0}}, {"mill": 1.0}, set(),
                             lambda totals: {"scholars": 1.0}) == [])
check("a shortfall of one resource closes only concerns holding it",
      closures_for_shortfall({"mill": {"craftsmen": 3.0}, "school": {"scholars": 3.0}}, {"mill": 1.0, "school": 0.0},
                             set(), lambda totals: {"craftsmen": 1.0} if totals["craftsmen"] > 0.5 else {}) == ["mill"])

# --- the hires a flagged concern gets
check("a flagged concern is hired what it is short, as whole people",
      people_to_hire_for({"glassblower": 1.0}, {"glassblower": 0.99}) == {"glassblower": 1})
check("...never more than the flagged concerns themselves hold",
      people_to_hire_for({"craftsmen": 2.0}, {"craftsmen": 7.0}) == {"craftsmen": 2})
check("...and a shortfall of a hundredth of a person hires nobody",
      people_to_hire_for({"craftsmen": 2.0}, {"craftsmen": 0.01}) == {})
check("...nor does a resource with no shortfall", people_to_hire_for({"craftsmen": 2.0}, {}) == {})
check("a part person over a whole one hires the next", people_to_hire_for({"craftsmen": 5.0}, {"craftsmen": 2.4}) == {"craftsmen": 3})


# --- what a shut concern lacks if it were opened now (Complaint 87's `state` list)
def strict_shortfalls(totals):
    return shortfalls_beyond(totals, {"craftsmen": 2.0, "scholars": 1.0, "glassblower": 0.0})


check("a concern whose people the household can field is missing nothing",
      missing_when_opened({"craftsmen": 1.0}, {"craftsmen": 1.0}, strict_shortfalls) == {})
check("a concern lacking a foreman trade names the trade and the full-time equivalent",
      missing_when_opened({}, {"glassblower": 0.25}, strict_shortfalls) == {"glassblower": 0.25})
check("what the running concerns already overdraw is not blamed on the shut one",
      missing_when_opened({"craftsmen": 3.0}, {"scholars": 0.5}, strict_shortfalls) == {})
check("only the overdraw the opening adds is missing",
      missing_when_opened({"craftsmen": 3.0}, {"craftsmen": 1.5}, strict_shortfalls) == {"craftsmen": 1.5})
check("less than a hundredth of a person over is not missing",
      missing_when_opened({"craftsmen": 2.0}, {"craftsmen": 0.004}, strict_shortfalls) == {})
held = {"craftsmen": 1.0}
missing_when_opened(held, {"craftsmen": 9.0}, strict_shortfalls)
check("the totals the caller passes are not changed", held == {"craftsmen": 1.0})
