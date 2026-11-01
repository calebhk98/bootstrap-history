"""Hiring by applications and acceptances, round after round, with random separations (Complaint 473, 608).

Follows the matching protocol of Eurace@Unibi (NOTICE.md), Labour/ in the Eurace source. Each round, a firm with
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
import bisect
import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from sim.constants import declare

from .asks import RESERVATION_CUT_PER_ROUND, SEARCH_ROUNDS_PER_YEAR, VACANCY_SHARE_THRESHOLD, WAGE_UPDATE_PER_ROUND

APPLICATIONS_PER_ROUND = declare(
    "APPLICATIONS_PER_ROUND", 3, kind="temporary_heuristic", unit="applications a searching household sends in a round",
    source=None, confidence="D",
    retire="Complaints/608: a wage method driven by the market\'s own state replaces this fixed fraction",
    why="Eurace's APPLICATIONS_PER_DAY, 3 in the shipped state run-trans/0_after_2k_transient.xml; Household_UNEMPLOYED_"
        "read_job_vacancies_and_send_applications in Labour/Household_Employee_Functions.c. Not fitted.")

SEPARATION_SHARE_PER_ROUND = declare(
    "SEPARATION_SHARE_PER_ROUND", 0.05, kind="temporary_heuristic", unit="share of a firm's workers dismissed per round",
    source=None, confidence="D",
    retire="Complaints/608: a wage method driven by the market\'s own state replaces this fixed fraction",
    why="Eurace's random dismissals (Firm_send_random_redundancies, Labour/Firm_Employer_Functions.c): a share drawn "
        "evenly from LOWER_BOUND_FIRING to UPPER_BOUND_FIRING percent, 0 to 10 in the shipped state "
        "run-trans/0_after_2k_transient.xml, so 5 percent on average; the C rounds the count of workers up, which "
        "hours do not. Not fitted.")


@dataclass
class Searchers:
    """Hours looking for work, all asking the same wage."""
    hours: float
    ask: float


def _round(groups: List[Searchers], vacancies: Dict[str, float], offers: Dict[str, float]
           ) -> Tuple[List[int], Dict[int, Dict[str, float]]]:
    """(for each group, how many of the posting employers it can apply to, and for each such count the share of one
    hour of such a group that each employer takes on). Posters are ranked by offer, highest first, so a group asking
    `ask` can reach the first employers whose offer is at or above it; groups reaching the same employers behave alike."""
    ranked = sorted((employer for employer, vacant in vacancies.items() if vacant > 0.0),
                    key=lambda employer: (-offers[employer], employer))
    negated = [-offers[employer] for employer in ranked]
    reach = [bisect.bisect_right(negated, -group.ask) for group in groups]
    hours_reaching: Dict[int, float] = {}
    for group, count in zip(groups, reach):
        hours_reaching[count] = hours_reaching.get(count, 0.0) + group.hours
    applicants = {employer: 0.0 for employer in ranked}
    for count, hours in hours_reaching.items():
        for employer in ranked[:count]:
            applicants[employer] += hours * min(APPLICATIONS_PER_ROUND, count) / count
    offered = {employer: min(1.0, vacancies[employer] / applicants[employer]) if applicants[employer] > 0.0 else 0.0
               for employer in ranked}
    return reach, {count: _taken_by(1.0, ranked[:count], offered, offers) for count in hours_reaching}


def apply_round(groups: List[Searchers], vacancies: Dict[str, float], offers: Dict[str, float]) -> List[Dict[str, float]]:
    """Hours each group of searchers is taken on for by each employer in one round. A group applies to
    `APPLICATIONS_PER_ROUND` of the employers with vacancies whose offer is at or above its ask, chosen evenly; an
    employer offers as many hours as it has vacancies, evenly among its applicants; a group takes the highest offer."""
    reach, units = _round(groups, vacancies, offers)
    return [{employer: group.hours * share for employer, share in units[count].items()}
            for group, count in zip(groups, reach)]


def _taken_by(hours: float, firms: List[str], offered: Dict[str, float], offers: Dict[str, float]) -> Dict[str, float]:
    """Hours of a group that applies to `APPLICATIONS_PER_ROUND` of `firms` at random and takes the best offer it gets.
    The chance firm j is the best is: it is chosen, makes an offer, and each better-paying firm also chosen made none;
    the choices are counted with a polynomial over the better firms (exact for a draw of the applications without
    replacement). Firms paying the same share their tier's hours by their chance of an offer."""
    if not firms:
        return {}
    ranked = sorted(firms, key=lambda employer: (-offers[employer], employer))
    count, applied = len(ranked), min(APPLICATIONS_PER_ROUND, len(ranked))
    better = [1.0] + [0.0] * (applied - 1)      # better[m]: weight of m better firms chosen and silent
    shares: Dict[str, float] = {}
    for position, employer in enumerate(ranked, start=1):
        others = count - position
        weight = sum(better[m] * math.comb(others, applied - 1 - m) for m in range(applied) if applied - 1 - m <= others)
        shares[employer] = offered[employer] * applied / count * weight / math.comb(count - 1, applied - 1)
        better = [better[m] + (better[m - 1] * (1.0 - offered[employer]) if m else 0.0) for m in range(applied)]
    taken: Dict[str, float] = {}
    for pay in {offers[employer] for employer in ranked}:
        tier = [employer for employer in ranked if offers[employer] == pay]
        total, weights = sum(shares[employer] for employer in tier), sum(offered[employer] for employer in tier)
        for employer in tier:
            taken[employer] = hours * total * (offered[employer] / weights if weights > 0.0 else 0.0)
    return taken




def lowered_ask(ask: float, floor: float) -> float:
    """The ask of a group that found nothing: cut by `RESERVATION_CUT_PER_ROUND`, not under `floor` (the plot return)."""
    return max(ask * (1.0 - RESERVATION_CUT_PER_ROUND), min(ask, floor))


def capped_asks(groups: List[Searchers], vacancies: Dict[str, float], offers: Dict[str, float]) -> List[Searchers]:
    """The groups with no ask over the best offer an employer with a vacancy posts: a seller does not ask more than any
    buyer is seen to pay (the rule `asks.record` applies to the market's ask), so hours that were paid more than the
    going offer do not sit idle waiting for the old wage. With no vacancy posted nothing is capped."""
    posted = [offers[employer] for employer, vacant in vacancies.items() if vacant > 0.0]
    best = max(posted) if posted else math.inf
    return [Searchers(group.hours, min(group.ask, best)) for group in groups]


def raised_offer(offer: float, ceiling: float, wanted: float, hired: float) -> float:
    """An employer's offer after a round: raised by `WAGE_UPDATE_PER_ROUND` while vacancies over `VACANCY_SHARE_THRESHOLD`
    of the hours it wants stay open (Firm_update_wage_offer, Eurace Labour/Firm_Employer_Functions.c), but not past
    `ceiling`, what its marginal hour is worth to it, and never lowered."""
    if wanted <= 0.0 or (wanted - hired) / wanted <= VACANCY_SHARE_THRESHOLD:
        return offer
    return max(offer, min(offer * (1.0 + WAGE_UPDATE_PER_ROUND), ceiling))


def hire_through_rounds(hired: Dict[str, float], kept: Dict[str, float], wanted: Dict[str, float],
                        offers: Dict[str, float], contracts: Dict[str, float], pool: float, ask: float,
                        floor: float, ceilings: Optional[Dict[str, float]] = None) -> Dict[str, float]:
    """Run the year's `SEARCH_ROUNDS_PER_YEAR` rounds over `hired` and `kept` (hours per employer, changed in place).
    `pool` hours ask `ask`; hours an employer dismisses, `SEPARATION_SHARE_PER_ROUND` of what it holds each round, ask
    the wage they were paid (a hired worker's reservation is reset to the wage, Household_receive_wage in
    Labour/Household_Employee_Functions.c): `contracts` for the hours it kept, `offers` for those it took on this year.
    With `ceilings` an employer whose vacancies stay open raises its offer after each round (`raised_offer`); `offers`
    ends as the mean offer each employer paid the hours it took on (its last offer where it took none). Returns the
    hours taken on per employer."""
    groups = [Searchers(pool, ask)]
    taken: Dict[str, float] = {}
    paid_sum: Dict[str, float] = {}
    for _ in range(SEARCH_ROUNDS_PER_YEAR):
        for employer in sorted(hired):
            held = hired[employer]
            if held <= 0.0:
                continue
            pay = (kept[employer] * contracts[employer] + (held - kept[employer]) * offers.get(employer, 0.0)) / held
            groups.append(Searchers(held * SEPARATION_SHARE_PER_ROUND, pay))
            hired[employer] = held * (1.0 - SEPARATION_SHARE_PER_ROUND)
            kept[employer] *= 1.0 - SEPARATION_SHARE_PER_ROUND
        vacancies = {employer: max(0.0, wanted[employer] - hired[employer]) for employer in wanted}
        groups = capped_asks(groups, vacancies, offers)
        reach, units = _round(groups, vacancies, offers)
        for group, count in zip(groups, reach):
            unit = units[count]
            for employer, share in unit.items():
                hired[employer] += group.hours * share
                taken[employer] = taken.get(employer, 0.0) + group.hours * share
                paid_sum[employer] = paid_sum.get(employer, 0.0) + group.hours * share * offers[employer]
            group.hours -= group.hours * sum(unit.values())
        groups = [Searchers(group.hours, lowered_ask(group.ask, floor)) for group in groups if group.hours > 1e-9]
        if ceilings is not None:
            for employer in wanted:
                offers[employer] = raised_offer(offers.get(employer, 0.0), ceilings.get(employer, 0.0),
                                                wanted[employer], hired[employer])
    for employer, hours in taken.items():
        if hours > 0.0:
            offers[employer] = paid_sum[employer] / hours
    return taken
