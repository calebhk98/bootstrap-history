"""Records: a Pathogen (read from data) and a Patch (people in one place, saved with the game)."""
import random
from dataclasses import dataclass, field
from typing import Any, Dict, Mapping, Optional, Tuple

from . import network


@dataclass(frozen=True)
class Pathogen:
    id: str
    name: str
    stages: Tuple[Mapping[str, Any], ...]
    transmissibility_per_day: float
    case_fatality: float
    immunity_permanent: bool
    immunity_duration_in_days: Optional[float]
    reproduction_number_range: Tuple[float, float] = (0.0, float("inf"))

    @classmethod
    def from_plain(cls, plain):
        immunity = plain.get("immunity") or {}
        return cls(id=plain["id"], name=plain.get("name", plain["id"]),
                   stages=tuple(dict(stage) for stage in plain["stages"]),
                   transmissibility_per_day=float(plain["transmissibility_per_day"]),
                   case_fatality=float(plain["case_fatality"]),
                   immunity_permanent=bool(immunity.get("permanent", True)),
                   immunity_duration_in_days=immunity.get("duration_in_days"),
                   reproduction_number_range=tuple(plain.get("reproduction_number_range") or (0.0, float("inf"))))


@dataclass
class Patch:
    """People in one place, by compartment, with the package's own seeded random generator."""
    counts: Dict[str, int]
    seed: int
    births_per_person_per_year: float = 0.0
    background_deaths_per_person_per_year: float = 0.0
    deaths_from_disease: int = 0
    deaths_background: int = 0
    births: int = 0
    owed_days: float = 0.0
    rng: random.Random = field(default=None, repr=False)

    def __post_init__(self):
        if self.rng is None:
            self.rng = random.Random(self.seed)

    @classmethod
    def naive(cls, pathogen, people, seed, **options):
        """Everyone susceptible: first contact."""
        counts = {name: 0 for name in network.compartment_ids(pathogen)}
        counts[network.SUSCEPTIBLE] = int(people)
        return cls(counts=counts, seed=seed, **options)

    @classmethod
    def endemic(cls, pathogen, people, seed, **options):
        """The immune share an endemic setting holds at equilibrium, where a case just replaces itself."""
        patch = cls.naive(pathogen, people, seed, **options)
        immune = round(people * network.herd_immunity_threshold(pathogen))
        patch.counts[network.SUSCEPTIBLE] -= immune
        patch.counts[network.RECOVERED] = immune
        return patch

    def living(self):
        return sum(self.counts.values())

    def infected_now(self):
        return sum(count for name, count in self.counts.items() if name not in (network.SUSCEPTIBLE, network.RECOVERED))

    def immune_share(self):
        return self.counts[network.RECOVERED] / self.living() if self.living() else 0.0

    def seed_infection(self, pathogen, people):
        """Move up to `people` susceptible people into the first stage (an introduction)."""
        moved = min(int(people), self.counts[network.SUSCEPTIBLE])
        self.counts[network.SUSCEPTIBLE] -= moved
        self.counts[network.infected_ids(pathogen)[0]] += moved
        return moved

    def to_plain(self):
        version, internal, gauss_next = self.rng.getstate()
        return {"counts": dict(self.counts), "seed": self.seed,
                "births_per_person_per_year": self.births_per_person_per_year,
                "background_deaths_per_person_per_year": self.background_deaths_per_person_per_year,
                "deaths_from_disease": self.deaths_from_disease, "deaths_background": self.deaths_background,
                "births": self.births, "owed_days": self.owed_days,
                "rng_state": [version, list(internal), gauss_next]}

    @classmethod
    def from_plain(cls, plain):
        version, internal, gauss_next = plain["rng_state"]
        rng = random.Random()
        rng.setstate((version, tuple(internal), gauss_next))
        fields = {key: value for key, value in plain.items() if key != "rng_state"}
        return cls(rng=rng, **fields)
