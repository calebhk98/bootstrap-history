"""The disease burden the technologies a nation holds leave, and the endemic death rates of the land it holds."""
from .burden_rules import burden_from_holdings


class Burden:

    def disease_burden_weights(self):
        """{node id: its population weight} for the technologies that make up the disease burden, in tree order."""
        effects = self.needs.tech_effects
        return {tech_id: effects[tech_id].get("population", 0.0) for tech_id in self.needs.mechanic["disease_burden"]}

    def disease_burden_held(self, node_id):
        """The share of a `disease_burden` node's weight that counts: all of it once built, or, for a work that
        declares `coverage`, the share of the people it serves while it is open."""
        if node_id not in self.needs.techniques_held():
            return 0.0
        return self.needs.coverage_share[node_id] if node_id in self.needs.coverage() else 1.0

    def disease_burden(self):
        """1.0 is the full pre-industrial infectious environment, 0.0 every technology that declares the
        `disease_burden` mechanic fully held (see `burden_from_holdings`); read fresh from what is held."""
        weights = self.disease_burden_weights()
        return burden_from_holdings(weights, {tech_id: self.disease_burden_held(tech_id) for tech_id in weights})

    def endemic_death_rates(self):
        """{band: excess deaths per head per year} from the endemic diseases of the tiles the nation holds."""
        return self.needs.endemic_people_loss(self.needs.tiles_listed_by(self.needs.civilisation()))
