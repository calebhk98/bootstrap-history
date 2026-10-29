"""Literacy: how far it can reach, how fast the open schools close the gap, and what research makes of it.

Needs: country_literacy_figure, country_literacy_ceiling, literacy_after_schooling, send (SchoolLiteracy), literacy_references, farm_share_of_hours, effect_terms, effect_values, running,
information diffusion (its own `diffusion_index`), school_node, done_year, year."""
from typing import Dict, Optional

from sim.actors.api import SchoolLiteracy
from sim.reporting.api import RecordEvent

from . import constants, literacy_rules, rules



class Literacy:

    def literacy(self, field: str, country: Optional[str] = None) -> float:
        return self.needs.country_literacy_figure(country, field)

    def research_productivity(self, country: Optional[str] = None) -> float:
        """Research uses the same lettered population ratio as scholar hiring."""
        references = self.needs.literacy_references()
        return max(0.0, min(references["factor_cap"],
                            self.literacy("literacy_elite", country) / references["reference_elite"]))

    def literacy_ceiling(self, field: str) -> float:
        """What the reading share `field` can reach: "literacy_general" the whole population's, "literacy_elite" the
        propertied class's, "common" the commoners who can attend school after the farms' call on their children."""
        if field == "common":
            return literacy_rules.common_ceiling(constants.UNABLE_TO_READ_SHARE, constants.FARM_CHILDREN_KEPT_FROM_SCHOOL,
                                                 self.needs.farm_share_of_hours())
        elite = 1.0 - constants.UNABLE_TO_READ_SHARE
        if field == "literacy_elite":
            return elite
        return self.needs.country_literacy_ceiling(None, self.literacy_ceiling("common"), elite)

    def schooling_flow(self, field: Optional[str] = None) -> float:
        """0 if no school is open here at all; otherwise a small positive number that grows, with diminishing
        returns, in how much school and academy capacity is actually running. Literacy is something a society is
        taught into, so with no school it never drifts upward."""
        running = self.needs.running
        terms = self.needs.effect_terms("schooling_flow")
        shut = any(spec.get("required") and not running[node_id] for node_id, spec in terms)
        # a school declares `reaches`, the literacy fields it teaches; one that names none teaches them all
        specs = dict(terms)
        return literacy_rules.schooling_flow([(value, specs[node_id].get("reaches"))
                                              for node_id, value in self.needs.effect_values("schooling_flow")], field, shut)

    def effective_schooling_flow(self, field: Optional[str] = None) -> float:
        """Schooling flow once diffused printing is counted; with `field`, only the schools that teach that figure."""
        flow = self.schooling_flow(field)
        if flow <= 0.0:
            return 0.0
        return literacy_rules.printing_boosted_flow(flow, constants.PRINTING_DIFFUSION_SCHOOLING_BOOST,
                                                    self.diffusion_index("information"))

    def literacy_next_year(self) -> Dict[str, float]:
        """The next schooling year's reading shares, without changing any stratum."""
        return self._school_literacy(preview=True)

    def _school_literacy(self, preview: bool = False) -> Dict[str, float]:
        if self.effective_schooling_flow() <= 0.0:
            return {}
        # each figure moves with the schools that teach it
        steps = tuple((field, rate * self.effective_schooling_flow(field), ceiling) for field, ceiling, rate in (
            ("literacy_elite", self.literacy_ceiling("literacy_elite"), constants.LITERACY_GROWTH_RATE_ELITE),
            ("literacy_general", self.literacy_ceiling("common"), constants.LITERACY_GROWTH_RATE_GENERAL)))
        before, after = (self.needs.literacy_after_schooling(None, steps) if preview else self.needs.send(SchoolLiteracy(steps)))
        return {field: after[field] for field, current in before.items() if abs(after[field] - current) > 1e-6}

    def advance_literacy(self, year: int) -> None:
        """Once a year: let running schools and academies close part of the gap between this society's literacy and
        what it could now reach. The increment shrinks as the gap does, so it never overshoots the ceiling."""
        changed = self._school_literacy()
        if not changed:
            return
        # census message at most once a generation, so small yearly gains stay quiet
        if year - self.world.literacy_said >= constants.GENERATION_YEARS:
            self.world.literacy_said = year
            school_phrase = literacy_rules.census_phrase(year, self.needs.done_year().get(self.needs.school_node()),
                                                         constants.GENERATION_YEARS)
            self.needs.send(RecordEvent.of("school_progress", "%s: %s" % (school_phrase, "; ".join(rules.census_bits(changed)))))
