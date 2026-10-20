"""Country literacy is a view of its living strata, never another saved total."""
from copy import copy
from typing import Any, Iterable


class CountryLiteracy:
    def __init__(self, strata: Iterable[Any]) -> None:
        self.records = [actor.record for actor in strata
                        if actor.record.exited_year is None and actor.record.members > 0.0]

    def _population(self, field: str):
        if field == "literacy_general":
            return self.records
        if field == "literacy_elite":
            propertied = [record for record in self.records
                          if float(record.plan.get("property_share") or 0.0) > 0.0]
            return propertied or self.records
        raise ValueError("unknown literacy field %r" % field)

    def copy(self):
        preview = copy(self)
        preview.records = [copy(record) for record in self.records]
        return preview

    def teach(self, field: str, value: float, ceiling: float) -> None:
        """General schools teach the non-propertied; their readers still count in the national total."""
        if field != "literacy_general":
            self.set(field, value, ceiling)
            return
        learners = copy(self)
        learners.records = [record for record in self.records
                            if float(record.plan.get("property_share") or 0.0) <= 0.0]
        people = sum(record.members for record in self.records)
        pupils = sum(record.members for record in learners.records)
        if pupils:
            target = learners.get(field) + (value - self.get(field)) * people / pupils
            learners.set(field, target, ceiling)

    def school(self, field: str, fraction: float, ceiling: float) -> None:
        """Schools close the gap of the people they teach, independently of other schools."""
        learners = copy(self)
        learners.records = ([record for record in self.records
                             if float(record.plan.get("property_share") or 0.0) <= 0.0]
                            if field == "literacy_general" else self._population(field))
        current = learners.get("literacy_general")
        if current < ceiling:
            learners.set("literacy_general", current + fraction * (ceiling - current), ceiling)

    def get(self, field: str) -> float:
        records = self._population(field)
        people = sum(record.members for record in records)
        return (sum(record.members * record.literacy for record in records) / people
                if people else 0.0)

    def ceiling(self, common: float, propertied: float) -> float:
        """The national ceiling weights each group's own limit by its members."""
        people = sum(record.members for record in self.records)
        return (sum(record.members * (propertied if float(record.plan.get("property_share") or 0.0) > 0.0
                                      else common) for record in self.records) / people
                if people else 0.0)

    def set(self, field: str, value: float, ceiling: float = 1.0) -> None:
        """Distribute a change by the remaining learners, preserving differences between strata.

        Schooling and technology use the same bounded approach to a ceiling. A decrease
        removes the same share of readers from each stratum, including people who migrate.
        """
        records = self._population(field)
        current = self.get(field)
        target = max(0.0, min(max(current, ceiling), value))
        if target > current:
            people = sum(record.members for record in records)
            room = sum(record.members * max(0.0, ceiling - record.literacy) for record in records)
            share = min(1.0, (target - current) * people / room) if room else 0.0
            for record in records:
                record.literacy += share * max(0.0, ceiling - record.literacy)
        elif current > 0.0:
            for record in records:
                record.literacy *= target / current
