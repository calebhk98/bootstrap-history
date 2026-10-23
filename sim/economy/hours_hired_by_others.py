"""Hours a labour market hired for employers that are not producers (the state, the mint, merchants' crews).

A producer's own hires are its plan's business; counting them again as other buyers' hours would keep
people for work a producer hired and did not turn into runs (a missing input left the hours idle).
"""
from typing import Container, Mapping


def beyond_producers(hired_by_employer: Mapping[str, float], producer_ids: Container[str]) -> float:
    """The hours the employers other than the producers hired."""
    return sum(hours for employer, hours in sorted(hired_by_employer.items()) if employer not in producer_ids)
