"""Partial hands from a converted cohort before its apprenticeship ends (Complaint 644).

A person converted from a nearby trade already does the share of the new trade's tasks the source covers
(Gathmann and Schonberg: human capital carries over, weighted by task distance). Boulton and Watt put men on
narrow classes of work as soon as they could do them and took on more hands as these learned (Smiles, Lives of
Boulton and Watt, ch. on Soho). So a cohort is written as two training records: an early slice of
person-equivalents (covered share of the cohort) that joins the staff once the part of an apprenticeship even a
fully covered trade needs has passed, and the rest at the end of the full conversion time.
"""
import math
from typing import List

from .trade_formation import SOURCE_TASK_FLOOR_FRACTION


def starting_proficiency(uncovered: float) -> float:
    """The share of the new trade's work a converted person does at first hands: the covered share of its tasks."""
    return 1.0 - max(0.0, min(1.0, uncovered))


def capped_by_teacher(proficiency: float, teacher_proficiency: float) -> float:
    """A cohort starts no more proficient than its teacher is (learning_curve.proficiency of the teacher's own cumulative
    output of the trade; a teacher who holds the knowledge but has never practised starts at the floor)."""
    return min(max(0.0, proficiency), max(0.0, min(1.0, teacher_proficiency)))


def first_hands_years(full_apprenticeship_years: float) -> float:
    """Years until a converted person can do the covered tasks: the floor share of a full apprenticeship, the
    part (tools, pace, judgement) even a trade the source fully covers still needs."""
    return max(0.0, full_apprenticeship_years) * SOURCE_TASK_FLOOR_FRACTION


def prepaid_keep_years(conversion_years: float, full_apprenticeship_years: float, uncovered: float) -> float:
    """Years of keep paid up front: the whole conversion less the span the early slice is on the payroll instead."""
    first = min(first_hands_years(full_apprenticeship_years), conversion_years)
    return conversion_years - starting_proficiency(uncovered) * (conversion_years - first)


def cohort_rows(current_year: float, trade: str, count: float, conversion_years: float,
                full_apprenticeship_years: float, uncovered: float, teacher_proficiency: float = 1.0) -> List[list]:
    """Training records `[progress, ready year, trade, people]` for a cohort: an early slice of person-equivalents
    ready at first hands (no larger a share than the teacher's own proficiency allows), then the rest at the end. One record when no task is covered or first hands would come
    no sooner than the end."""
    first = first_hands_years(full_apprenticeship_years)
    early = count * capped_by_teacher(starting_proficiency(uncovered), teacher_proficiency)
    if early <= 0.0 or first >= conversion_years:
        return [[0.0, current_year + conversion_years, trade, float(count)]]
    return [[0.0, current_year + first, trade, early],
            [0.0, current_year + conversion_years, trade, float(count) - early]]


def year_joined(ready_year: float) -> int:
    """The calendar year a record ready at `ready_year` joins the staff: the apprenticeship step runs at the turn
    of each whole year and moves every record whose ready year has been reached, so a fractional ready year lands
    on the next whole one."""
    return int(math.ceil(ready_year - 1e-9))
