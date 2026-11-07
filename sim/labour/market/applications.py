"""Hiring by applications and acceptances, round after round, with random separations (Complaint 473, 608).

Follows the matching protocol of Eurace@Unibi (NOTICE.md), Labour/ in the Eurace source, but leaves out its skill-specific
offers and its ranking of applicants by skill: hours of a trade are alike. Each round, a firm with
vacancies posts them with its offer (Firm_send_vacancies, Labour/Firm_Employer_Functions.c); every searching
household applies to a bounded number of the posters whose offer is at or above its reservation wage, chosen at random,
the household's own list being cut at random (Household_UNEMPLOYED_read_job_vacancies_and_send_applications,
Labour/Household_Employee_Functions.c); a firm sends offers to as many applicants as it has vacancies
(Firm_read_job_applications_send_job_offer_or_rejection); a household takes the highest offer it got
(Household_read_job_offers_send_response); one that got none cuts its reservation wage
(Household_read_application_rejection_update_wage_reservation). Before the round a firm dismisses a random share of its
workers and reposts the vacancies (Firm_send_random_redundancies). Hours stand for workers, so each step is the share
of a group of hours it happens to, not a draw.
"""
from dataclasses import dataclass
from typing import Dict, Optional, Sequence

import numpy as np

from sim.constants import declare

from . import hiring_kernel
from .asks import RESERVATION_CUT_PER_ROUND, SEARCH_ROUNDS_PER_YEAR, VACANCY_SHARE_THRESHOLD, WAGE_UPDATE_PER_ROUND

APPLICATIONS_PER_ROUND = declare(
    "APPLICATIONS_PER_ROUND", 3, kind="temporary_heuristic", unit="applications a searching household sends in a round",
    source=None, confidence="D",
    retire="Complaints/608: a wage method driven by the market\'s own state replaces this fixed fraction",
    why="Eurace's APPLICATIONS_PER_DAY, 3 in the shipped state its/0_after_2k_transient.xml; Household_UNEMPLOYED_"
        "read_job_vacancies_and_send_applications in Labour/Household_Employee_Functions.c. Not fitted.")

SEPARATION_SHARE_PER_ROUND = declare(
    "SEPARATION_SHARE_PER_ROUND", 0.05, kind="temporary_heuristic", unit="share of a firm's workers dismissed per round",
    source=None, confidence="D",
    retire="Complaints/608: a wage method driven by the market\'s own state replaces this fixed fraction",
    why="Eurace's random dismissals (Firm_send_random_redundancies, Labour/Firm_Employer_Functions.c): a share drawn "
        "evenly from LOWER_BOUND_FIRING to UPPER_BOUND_FIRING percent, 0 to 10 in the shipped state "
        "its/0_after_2k_transient.xml, so 5 percent on average; the C rounds the count of workers up, which "
        "hours do not. Not fitted.")


@dataclass
class HireJob:
    """One market's hiring rounds. `hired`, `kept` and `offers` (hours or wage per employer, one key set) change in place;
    `taken` is filled with the hours taken on per employer."""
    hired: Dict[str, float]
    kept: Dict[str, float]
    wanted: Dict[str, float]
    offers: Dict[str, float]
    pool: float
    ask: float
    floor: float
    ceilings: Optional[Dict[str, float]] = None
    taken: Optional[Dict[str, float]] = None


def hire_markets(jobs: Sequence[HireJob]) -> None:
    """Run the year's `SEARCH_ROUNDS_PER_YEAR` rounds of every job's market in one kernel call. Each market is packed
    into arrays (employers in sorted id order), run, and written back. The rounds: a firm's workers are dismissed
    into groups of searching hours (`SEPARATION_SHARE_PER_ROUND` of what it holds, asking the wage they were paid), groups
    apply to employers' offers, and groups that found nothing lower their ask (`RESERVATION_CUT_PER_ROUND`, not under the
    plot return `floor`); with `ceilings` an employer whose vacancies stay open raises its offer after each round, not
    past its ceiling (`WAGE_UPDATE_PER_ROUND`, while over `VACANCY_SHARE_THRESHOLD` of the hours wanted stay open).
    `offers` ends as the mean offer each employer paid the hours it took on (its last offer where it took none)."""
    keys = [sorted(job.hired) for job in jobs]
    offsets = np.zeros(len(jobs) + 1, np.int64)
    np.cumsum([len(each) for each in keys], out=offsets[1:])
    total = int(offsets[-1])

    def column(read) -> np.ndarray:
        return np.fromiter((read(job, employer) for job, employers in zip(jobs, keys) for employer in employers), np.float64, total)
    hired = column(lambda job, employer: job.hired[employer])
    kept = column(lambda job, employer: job.kept[employer])
    wanted = column(lambda job, employer: job.wanted[employer])
    offers = column(lambda job, employer: job.offers[employer])
    ceilings = column(lambda job, employer: 0.0 if job.ceilings is None else job.ceilings.get(employer, 0.0))
    taken_amount = np.zeros(total)
    taken_flag = np.zeros(total, np.bool_)
    hiring_kernel.hire_markets(
        offsets, hired, kept, wanted, offers, ceilings,
        np.array([job.pool for job in jobs], np.float64), np.array([job.ask for job in jobs], np.float64),
        np.array([job.floor for job in jobs], np.float64), np.array([job.ceilings is not None for job in jobs], np.bool_),
        taken_amount, taken_flag, SEARCH_ROUNDS_PER_YEAR, APPLICATIONS_PER_ROUND, SEPARATION_SHARE_PER_ROUND,
        RESERVATION_CUT_PER_ROUND, WAGE_UPDATE_PER_ROUND, VACANCY_SHARE_THRESHOLD)
    hired_list, kept_list, offers_list = hired.tolist(), kept.tolist(), offers.tolist()
    amounts, flags = taken_amount.tolist(), taken_flag.tolist()
    for job, employers, low in zip(jobs, keys, offsets.tolist()):
        job.taken = {}
        for index, employer in enumerate(employers, start=low):
            job.hired[employer] = hired_list[index]
            job.kept[employer] = kept_list[index]
            job.offers[employer] = offers_list[index]
            if flags[index]:
                job.taken[employer] = amounts[index]


def hire_through_rounds(hired: Dict[str, float], kept: Dict[str, float], wanted: Dict[str, float],
                        offers: Dict[str, float], pool: float, ask: float,
                        floor: float, ceilings: Optional[Dict[str, float]] = None) -> Dict[str, float]:
    """`hire_markets` for one market; returns the hours taken on per employer."""
    job = HireJob(hired, kept, wanted, offers, pool, ask, floor, ceilings)
    hire_markets([job])
    return job.taken
