"""The excess deaths a place's endemic disease adds to one age band in a year."""


def endemic_excess_deaths(band_people: float, deaths_so_far: float, rate: float, disease_burden: float) -> float:
    """The band's excess deaths: its people times the place's endemic death rate, cut by the disease burden the
    nation has not yet removed; never more than the band's survivors."""
    return min(band_people - deaths_so_far, band_people * rate * disease_burden)
