"""Deaths an epidemic model already counted (sim/disease), added to a year's other deaths by age band."""
from typing import Mapping, Tuple


def add_epidemic_deaths(deaths: Tuple[float, float, float], living: Tuple[float, float, float],
                        epidemic: Mapping[str, float]) -> Tuple[float, float, float]:
    """(children, working age, elderly) deaths with the epidemic's added: never more than the band's survivors."""
    children, working_age, elderly = deaths
    return (children + min(living[0] - children, epidemic.get("children", 0.0)),
            working_age + min(living[1] - working_age, epidemic.get("working_age", 0.0)),
            elderly + min(living[2] - elderly, epidemic.get("elderly", 0.0)))
