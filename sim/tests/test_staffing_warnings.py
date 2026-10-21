"""A warning before the staffing door shuts: which running concern the staffing rule would close next and how much slack stands
between (`staffing_warning_rows`, the arithmetic `Sim.staffing_closure_warnings` gathers its numbers for), and the sentences
the state screen makes of them. The rows are built from numbers handed in here; what the game feeds them and that every
screen renders on a rich game is test_staffing_warnings_scenario."""

QUICK_TOPIC = True

from .harness import check

from sim.engine.staffing_warning_rows import staffing_warning_rows
from sim.ui.proto.render_screen_state_blocks import _staffing_warning_sentences

SLACK, BAND, NO_SLACK_BAND = 0.5, 5.0, 1.0
CONCERNS = [
    {"id": "dear", "name": "Dear works", "revenue": 1000.0, "upkeep": 200.0, "hands": (0.0, 2.0)},   # 400 a year per craftsman
    {"id": "cheap", "name": "Cheap works", "revenue": 500.0, "upkeep": 100.0, "hands": (0.0, 4.0)},   # 100 a year per craftsman
]
CRAFTSMEN_IN_USE = 6.0


def rows(craftsmen_held, concerns=CONCERNS, scholars_held=40.0, scholars_used=0.0, hired_craftsmen=0.0, founder_fixed=False,
         craftsmen_used=CRAFTSMEN_IN_USE, limit=3):
    return staffing_warning_rows(
        concerns, scholars_held, craftsmen_held, 0.0, hired_craftsmen, scholars_used, craftsmen_used, founder_fixed,
        SLACK, BAND, NO_SLACK_BAND, limit, lambda kind: 'hire a %s: {"cmd":"hire","trade":"%s"}' % (kind, kind),
        lambda net: "%d den/year" % net)


check("comfortably staffed: no staffing warning at all", rows(craftsmen_held=40.0) == [])
check("no concerns running: no staffing warning", rows(craftsmen_held=6.0, concerns=[]) == [])

near = rows(craftsmen_held=8.0)   # 8 held + 0.5 allowed - 6 in use = 2.5 spare
check("within the band: a warning names a real running concern and how many craftsmen stand between here and its closure",
      bool(near) and near[0]["id"] in {"dear", "cheap"} and near[0]["of"] == "craftsmen" and near[0]["within"] == 2.5
      and "spare" in near[0]["headline"] and "closes" in near[0]["headline"], near)
check("the concern it names is the one the staffing rule would close first (the least a year for the craftsmen it ties up)",
      near[0]["id"] == "cheap" and [row["id"] for row in near] == ["cheap", "dear"], near)
check("within the band but not down to the last one: one_loss_closes_it is false",
      near[0]["one_loss_closes_it"] is False and "spare" in near[0]["headline"], near)
check("the warning carries held, in use and allowance, and the spare number is held plus allowance minus in use",
      (near[0]["held"], near[0]["in_use"], near[0]["allowance"]) == (8.0, 6.0, SLACK)
      and near[0]["within"] == near[0]["held"] + near[0]["allowance"] - near[0]["in_use"], near)
check("only as many warnings as the limit", len(rows(craftsmen_held=8.0, limit=1)) == 1)

more = rows(craftsmen_held=9.0)
check("hiring more staff moves the reported room UP", more[0]["within"] > near[0]["within"], (near[0]["within"], more[0]["within"]))

last = rows(craftsmen_held=5.6)   # 0.1 spare: one loss closes it
check("no slack at all: the warning says losing just one more closes it, not merely that it is within some number",
      last[0]["one_loss_closes_it"] and "losing just one more closes it outright" in last[0]["headline"], last)
check("...and names what that closure would cost in recurring income, and the command that fixes it",
      last[0]["recurring_income_at_risk"] == 400.0 and "400 den/year" in last[0]["headline"] and '"cmd":"hire"' in last[0]["fix"]
      and last[0]["fix"] in last[0]["headline"], last)

gone = rows(craftsmen_held=5.0)   # -0.5 spare
check("room exhausted: the warning says so plainly rather than quoting a negative number of craftsmen",
      gone[0]["within"] == 0.0 and "no craftsmen free this year" in gone[0]["headline"], gone)
check("...and is also costed and fixed", gone[0]["recurring_income_at_risk"] > 0 and '"cmd":"hire"' in gone[0]["fix"], gone)

# the two kinds of hands are told apart
scholars_only = [{"id": "school", "name": "School", "revenue": 900.0, "upkeep": 100.0, "hands": (3.0, 0.0)}]
check("a concern that only draws on scholars is not put on notice by a shortage of craftsmen",
      rows(craftsmen_held=5.0, concerns=scholars_only, scholars_held=40.0) == [])
short_scholars = rows(craftsmen_held=40.0, concerns=scholars_only, scholars_held=4.0, scholars_used=3.0)
check("...and is by a shortage of scholars, in scholars", short_scholars and short_scholars[0]["of"] == "scholars"
      and short_scholars[0]["within"] == 1.5, short_scholars)
both = [{"id": "both", "name": "Both works", "revenue": 900.0, "upkeep": 100.0, "hands": (3.0, 2.0)}]
check("a concern needing both is warned about whichever pool is scarcer",
      rows(craftsmen_held=6.0, concerns=both, scholars_held=4.0, scholars_used=0.0, craftsmen_used=4.0)[0]["of"] == "craftsmen"
      and rows(craftsmen_held=30.0, concerns=both, scholars_held=3.0, scholars_used=0.0, craftsmen_used=4.0)[0]["of"] == "scholars")

# a founder who cannot leave leaves only the hired people to lose
check("with a founder who cannot leave, room that survives losing every hired person is no risk",
      rows(craftsmen_held=8.0, hired_craftsmen=2.0, founder_fixed=True) == [])
check("...but room that does not survive it is",
      bool(rows(craftsmen_held=8.0, hired_craftsmen=3.0, founder_fixed=True)))
check("a mortal founder can leave, so the same room is a risk", bool(rows(craftsmen_held=8.0, hired_craftsmen=2.0, founder_fixed=False)))

inputs = [dict(concern) for concern in CONCERNS]
rows(craftsmen_held=8.0, concerns=inputs)
check("calling it changes nothing it was given", inputs == CONCERNS)

# ---- the sentences the state screen makes of them (presentation) --------------------------------------------------------
sentences = _staffing_warning_sentences(near)
check("each warning is a sentence on the state screen, and the arithmetic is explained once",
      any(row["headline"] in sentences or "Cheap works and Dear works" in " ".join(sentences) for row in near)
      and sum("full-time" in sentence for sentence in sentences) == 1, sentences)
check("a warning that is a bare string is passed through", _staffing_warning_sentences(["already a sentence"]) == ["already a sentence"])
check("no warnings, no sentences", _staffing_warning_sentences(None) == [])
