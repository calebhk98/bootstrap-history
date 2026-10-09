"""What a defence needs in hand: powder in a magazine and a garrison present (Complaint 245).

A `hazard_counters` entry may name a `magazine` ({material: units}, held in the stock ledger) and
`draws` ({material: units} spent in each year a threat it answers is live). A node may name a
`garrison` ({trade: people}) drawn from the labour market; an open concern holds its garrison the way
it holds a foreman (projects_staffing_shortfall.py). A node's `banks_output` ({material,
per_labour_hour}) makes a running work put that material into the ledger from its crew's hours. A
counter counts for the share of its magazine held and of its garrison present, and says which fell short.
Nothing here names a node or a material.
"""
from .hazard_window import hazards_not_yet_past


def counter_spec(nodes, node_id, kind, label):
    """The `hazard_counters` entry of `node_id` for this kind and label, else {}."""
    for counter in ((nodes[node_id].get("mechanics") or {}).get("hazard_counters") or ()):
        if counter["kind"] == kind and counter["label"] == label:
            return counter
    return {}


class DefenceStoresMixin:

    def venture_garrison(self, node_id, units=1.0):
        """{trade: people} an open concern holds as its garrison, at `units` times its founding size."""
        return {trade: people * units
                for trade, people in sorted((self.nodes[node_id].get("garrison") or {}).items())
                if people > 0.0}

    def garrison_claims(self):
        """{trade: people} claimed by every built garrison in force: a concern when open, a work with
        no doors to shut always."""
        projects = self.state.projects
        claims = {}
        for node_id in sorted(projects.done):
            node = self.nodes.get(node_id)
            if not node or not node.get("garrison"):
                continue
            if self.is_venture(node_id) and node_id not in projects.operating:
                continue
            for trade, people in self.venture_garrison(node_id).items():
                claims[trade] = claims.get(trade, 0.0) + people
        return claims

    def garrison_share(self, node_id):
        """(share of the garrison present, the trade most short or None): employed people of each
        trade against what every garrison in force claims of it, shared out evenly."""
        needed = self.venture_garrison(node_id)
        if not needed:
            return 1.0, None
        claims = self.garrison_claims()
        employed = self.state.household.employees
        share, short_trade = 1.0, None
        for trade, people in needed.items():
            claim = max(claims.get(trade, 0.0), people)
            present = min(1.0, employed.get(trade, 0.0) / claim)
            if present < share:
                share, short_trade = present, trade
        return share, short_trade

    def magazine_share(self, counter):
        """(share of the magazine held, the material most short or None)."""
        share, short_material = 1.0, None
        for material, units in sorted((counter.get("magazine") or {}).items()):
            held = min(1.0, self.stock_held(material) / units) if units > 0.0 else 1.0
            if held < share:
                share, short_material = held, material
        return share, short_material

    def counter_supply_gap(self, node_id, kind, label):
        """(share in force, words for what is short or None) of a counter's magazine and garrison."""
        magazine, material = self.magazine_share(counter_spec(self.nodes, node_id, kind, label))
        garrison, trade = self.garrison_share(node_id)
        if magazine <= garrison and material:
            return magazine, "its magazine of %s is %s" % (
                material, "empty" if magazine <= 0.0 else "short")
        if trade:
            return garrison, "no %s garrison is present" % trade if garrison <= 0.0 else (
                "its %s garrison is short" % trade)
        return 1.0, None

    def draw_defence_stores(self, year):
        """Spend each built counter's `draws` from the ledger in a year a threat of its kind is live."""
        live = {kind for hazard, _start, _end, in_progress in hazards_not_yet_past(self.civ, year)
                if in_progress for kind in hazard}
        for node_id in sorted(self.state.projects.done):
            for counter in ((self.nodes[node_id].get("mechanics") or {}).get("hazard_counters") or ()):
                if counter["kind"] not in live:
                    continue
                for material, units in sorted((counter.get("draws") or {}).items()):
                    self.change_stock(material, -min(units, self.stock_held(material)))

    def bank_works_output(self):
        """Put into the ledger what each running work that `banks_output` makes in a year from its
        crew's hours."""
        for node_id in self.running_with_mechanic("banks_output"):
            spec = self.mechanic(node_id, "banks_output")
            node = self.nodes[node_id]
            crew_hours = (node["sch"] + node["art"]) * self.HOURS_PER_PERSON_YEAR * self.institution_units(node_id)
            self.change_stock(spec["material"], crew_hours * spec["per_labour_hour"])

    def step_defence_stores(self):
        """The year's turn of the magazines: the threats of the year spend, then the works restock."""
        self.draw_defence_stores(self.state.scenario.year)
        self.bank_works_output()
