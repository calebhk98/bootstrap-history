"""What the founder builds does not stay the founder's: how far each venture's edge and each category of knowledge has
spread through the society.

Needs: operating, tree, tree_nodes, done_year, venture_opened_year, year, corpus_diffusion_pace, literacy_references,
diffusion_traits, seat_holders, built_by_any_seat, earliest_done_year, state_knowledge."""
from typing import Any, Optional, Tuple

from . import constants, rules
from .adoption_share import held_share
from .diffusion_curve import knowledge_half_life, leaked_share
from .diffusion_rules import spread_share

CATEGORIES = ("food", "medical", "information")


class Spread:

    # ---- the founder's own ventures ----

    def diffusion_share(self, node_id: str) -> float:
        """0..VENTURE_DIFFUSION_CAP: how much of what running venture `node_id` earns has already leaked to
        competitors who watched it run. Zero for anything not operating and for anything with no revenue.
        A revenue formula spending it credits the wider economy with the matching gain through the goods' prices."""
        if node_id not in self.needs.operating():
            return 0.0
        node = self.needs.tree[node_id]
        if not node or node.get("rev", 0) <= 0:
            return 0.0
        year = self.needs.year()
        done_year_map = self.needs.done_year() or {}
        started = self.needs.venture_opened_year(node_id, done_year_map.get(node_id, year))
        return leaked_share(year - started, self.knowledge_half_life_years(), constants.VENTURE_DIFFUSION_CAP)

    def knowledge_half_life_years(self, country: Optional[str] = None) -> float:
        """Years for half of those who could copy a technique to have done so: faster with a written, dispersed
        corpus and with the country's general literacy."""
        return knowledge_half_life(
            constants.VENTURE_DIFFUSION_HALF_LIFE_YEARS, self.needs.corpus_diffusion_pace(),
            float(self.literacy("literacy_general", country)), self.needs.literacy_references()["reference_general"],
            constants.LITERACY_DIFFUSION_PACE_BASE, constants.LITERACY_DIFFUSION_PACE_SPAN,
            constants.LITERACY_DIFFUSION_PACE_CAP_RATIO, constants.DIFFUSION_PACE_FLOOR)

    def venture_diffusion_index(self) -> float:
        """The revenue-weighted average of diffusion_share across everything operated for a living; 0.0 when nothing
        is. Weighted by revenue so one huge ironworks and one new stall read as mostly caught up with."""
        operating = sorted(node_id for node_id in self.needs.operating()
                           if (self.needs.tree[node_id] or {}).get("rev", 0) > 0)
        if not operating:
            return 0.0
        total_weight = total = 0.0
        for node_id in operating:
            weight = self.needs.tree[node_id]["rev"]
            total_weight += weight
            total += weight * self.diffusion_share(node_id)
        return total / total_weight if total_weight > 0 else 0.0

    # ---- the country ----

    def diffusible_ids(self, category: str) -> Tuple[str, ...]:
        """The nodes of a diffusing category. Only the tree's traits decide membership, so it is built once."""
        if self._diffusible is None:
            self._diffusible = rules.diffusible_ids(self.needs.tree_nodes(), tuple(self.needs.diffusion_traits()))
        return self._diffusible.get(category, ())

    def category_half_life_years(self, category: str) -> float:
        """Bare half-life of a diffusion category: a number in its data entry, or the declared constant it names."""
        entry = self.needs.diffusion_traits()[category]
        if "half_life_years" in entry:
            return float(entry["half_life_years"])
        return getattr(constants, entry["half_life_constant"])

    def category_pace(self, category: str) -> float:
        """How much faster than the category's bare half-life it moves for this society now: text-paced categories
        gain from a written corpus and the country's literacy; military is what the government holds, and food
        needs nobody to read anything."""
        if not self.needs.diffusion_traits()[category].get("text_paced"):
            return 1.0
        return rules.text_category_pace(
            self.needs.corpus_diffusion_pace(), float(self.literacy("literacy_general")),
            self.needs.literacy_references()["reference_general"], constants.LITERACY_DIFFUSION_PACE_BASE,
            constants.LITERACY_DIFFUSION_PACE_SPAN, constants.LITERACY_DIFFUSION_PACE_CAP_RATIO)

    def civ_diffusion(self, node_id: str) -> float:
        """0..1: how much of the whole society has adopted technology `node_id`. Counted from when it is done, not
        operating: a country copies a crop whether or not the founder keeps a stall in it. Zero outside the diffusion
        categories. Military is not a curve: 1 when the government holds the node, else 0."""
        year = self.needs.year()
        if not self.needs.seat_holders(node_id):
            return 0.0
        node = self.needs.tree[node_id]
        if not node:
            return 0.0
        traits = self.needs.diffusion_traits()
        category = rules.diffusion_category(node.get("traits"), tuple(traits))
        if category is None:
            return 0.0
        if traits[category].get("government_held"):
            return 1.0 if node_id in self.needs.state_knowledge() else 0.0
        # the society copies from whichever seat finished it first
        age = max(0.0, year - self.needs.earliest_done_year(node_id, year))
        half_life = rules.category_half_life(self.category_half_life_years(category), self.category_pace(category),
                                             constants.DIFFUSION_PACE_FLOOR)
        return spread_share(age, half_life)

    def category_diffusion_index(self, category: str) -> float:
        """Plain average across every founder-built node in `category` (not revenue-weighted: a food category with
        one fully-spread crop and one just-introduced one is honestly half spread). Opening-state knowledge is
        already part of this society, so it does not count as the founder's to diffuse."""
        ids = sorted(self.needs.built_by_any_seat(self.diffusible_ids(category)))
        if not ids:
            return 0.0
        return sum(self.civ_diffusion(node_id) for node_id in sorted(ids)) / len(ids)

    def state_military_diffusion(self) -> float:
        """Share of the founder's military work the government actor holds."""
        held = self.needs.state_knowledge()
        ids = sorted(self.needs.built_by_any_seat(self.diffusible_ids("military")))
        return held_share(ids, held)

    def diffusion_index(self, kind: str) -> float:
        """How widely `kind` has spread: "venture" the founder's running ventures (revenue-weighted), a category
        ("food", "medical", "information") its plain average, "military" the share the state holds."""
        if kind == "venture":
            return self.venture_diffusion_index()
        if kind == "military":
            return self.state_military_diffusion()
        return self.category_diffusion_index(kind)

    def diffusion_report(self) -> Optional[Any]:
        """None while nothing the founder has built is spreading; else a snapshot of how far it has and what that is
        doing to the country. Never silent in a state variable."""
        return rules.diffusion_report(self.diffusion_index("food"), self.diffusion_index("medical"),
                                      self.diffusion_index("military"), self.diffusion_index("information"),
                                      lambda: self.diffusion_relief("medical"))
