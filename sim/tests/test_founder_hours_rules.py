"""The founder's own hours, and the gates on the people a project needs (Complaint 640): called on numbers and stubs built
here, no game. Hours sold twice, the cost note of a sale, the standing job's pay, the cap on buying people, the scholar and
craftsman gates (contracted hours count), and the hire advice sized to the deficit."""
QUICK_TOPIC = True

from types import SimpleNamespace

from .harness import check
from sim.refusal import cause_of, facts_of
from sim.engine.society_adoption import AdoptionMixin
from sim.projects.api import staff_gate
craftsmen_gate_text, scholar_gate_text = staff_gate.craftsmen_gate_text, staff_gate.scholar_gate_text
from sim.labour.buy_cap import over_room_refusal
from sim.labour.founder_hours import hours_committed, hours_free, hours_pool
from sim.labour.hands import contracted_hours_of, hands_available
from sim.labour.hours_sale_warning import sale_at_a_loss_note
from sim.labour.labour_job import StandingJobMixin
from sim.labour.staff_advice import staff_remedies

# --- the pool
check("a living founder's year is his own hours", hours_pool(True, 2000.0, False, 0.25, 0, 4000.0) == 2000.0)
check("a bonded founder keeps only the bonded share", hours_pool(True, 2000.0, True, 0.25, 0, 4000.0) == 500.0)
check("each deputy adds the hours of a deputy, the founder or not",
      hours_pool(True, 2000.0, False, 0.25, 2, 4000.0) == 10000.0 and hours_pool(False, 2000.0, False, 0.25, 2, 4000.0) == 8000.0)

# --- hours sold are hours spoken for, once
committed = hours_committed(100.0, None, 50.0, 1700.0)
check("teaching, moving, supervising and wage hours are all spoken for", committed == 1850.0, committed)
check("hours already sold for wages are not still free", hours_free(2000.0, committed) == 150.0)
check("more committed than the pool leaves none, not a negative", hours_free(2000.0, 2500.0) == 0.0)
check("selling every free hour leaves nothing to spend on projects",
      hours_free(2000.0, hours_committed(0.0, 0.0, 0.0, 2000.0)) == 0.0)

# --- the standing job sells the hours not spoken for, so a sale takes its pay from the job
def standing_job(sold):
    labour = SimpleNamespace(
        _world=SimpleNamespace(state=SimpleNamespace(founder=SimpleNamespace(founder_alive=True))),
        director_pool=lambda: 2000.0, director_hours_committed=lambda: sold,
        wage_for_hours=lambda trade, hours: hours * 0.5)
    labour.hours_for_sale = lambda: StandingJobMixin.hours_for_sale(labour)
    return StandingJobMixin.standing_job_pay(labour, "labourer")


check("selling every hour on request takes the whole standing job", standing_job(2000.0) == 0.0)
check("selling half the hours takes half the standing job", standing_job(1000.0) == 0.5 * standing_job(0.0))
check("a trade nobody holds earns the job nothing",
      StandingJobMixin.standing_job_pay(SimpleNamespace(), None) == 0.0)

# --- the cost note of a sale
# presentation: the sentence and its money format
note = sale_at_a_loss_note(66.0, 259.0, lambda amount: "%d d" % amount)
check("a sale that displaces a better-paid job says what it cost", note and "cost you 193 d" in note, note)
check("a sale that pays at least what it displaced carries no note", sale_at_a_loss_note(259.0, 259.0, str) is None)

# --- the cap on buying people is the room hire enforces
check("buying within the room is not refused", over_room_refusal(3, 3.0, lambda: "advice") is None)
refusal = over_room_refusal(7, 6.4, lambda: "hire fewer")
check("buying beyond the room is refused as a household_room refusal stating the room and the people asked for",
      refusal and cause_of(refusal) == "household_room" and facts_of(refusal) == {"room": 6.4, "people": 7}, refusal)
check("a negative room reads as none", facts_of(over_room_refusal(1, -2.0, lambda: ""))["room"] == 0.0)

# --- the staffing gates
HOURS_PER_YEAR = 2000.0
bare = hands_available(0.0, True, 0.0, HOURS_PER_YEAR)
check("the founder counts as a pair of hands", bare == 1.0, bare)
contracted = contracted_hours_of({"carpenter": 4000.0, "scribe": 2000.0}, lambda trade: trade == "carpenter")
check("hours bought under contract in a craft count as a person for each year",
      contracted == 4000.0 and hands_available(0.0, True, contracted, HOURS_PER_YEAR) == 3.0)
check("...so a project needing two craftsmen is no longer short once four thousand hours are commissioned",
      craftsmen_gate_text(2, bare, lambda deficit: "x") is not None
      and craftsmen_gate_text(2, hands_available(0.0, True, contracted, HOURS_PER_YEAR), lambda deficit: "x") is None)
check("one hired hand is enough beside the founder for a project needing two",
      scholar_gate_text(2, hands_available(1.0, True, 0.0, 1.0), lambda deficit: "x") is None)


def hire_advice(deficit):
    steps = staff_remedies("scholars", [("HIRE", "hire somebody")], deficit, set(), set(), lambda node: False,
                           lambda node: False, lambda node: False, lambda kind, count: AdoptionMixin.staff_hire_advice(None, kind, count))
    return steps[0][0]


asked = []
text = scholar_gate_text(2, 1.0, lambda deficit: asked.append(deficit) or hire_advice(deficit))
check("the gate hands the advice the people short", asked == [1.0], asked)
check("one scholar short says hire one, not two", text and '"n":1' in text and '"n":2' not in text, text)
check("two scholars short says hire two", '"n":2' in scholar_gate_text(3, 1.0, hire_advice))
people_asked_for = []
staff_remedies("scholars", [("HIRE", "hire somebody")], 0.4, set(), set(), lambda node: False, lambda node: False,
               lambda node: False, lambda kind, count: people_asked_for.append(count) or "")
check("a fraction short rounds up to the whole person", people_asked_for == [1], people_asked_for)
check("a project the staff cover has no gate", scholar_gate_text(2, 2.0, hire_advice) is None)
