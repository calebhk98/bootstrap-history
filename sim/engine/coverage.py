"""Coverage: how much of the nation's people a repeated work serves, and rolling it out to a target share.

A work declares `mechanics.coverage = {"staff_hours_per_person_year": h, "serves": "pupils", "eligible_share": e}`.
One unit of it employs its `annual_labour_hours` a year, so it serves that many hours divided by `h` people; units run
times that, over the people who can use it (all of the nation's, or the share `e` of them, such as school-age
children), is the share covered. A rollout is more units of the same work (they are the places it is repeated
in) until the share asked for is reached or the nation can fill no more.
"""


class CoverageMixin:

    def coverage_nodes(self):
        """Ids of the works that declare `coverage`."""
        return self.nodes_with_mechanic("coverage")

    def disease_burden_held(self, node_id):
        """The share of a `disease_burden` node's weight that counts: all of it once built, or, for a work that
        declares `coverage`, the share of the people it serves while it is open."""
        if not self.has(node_id):
            return 0.0
        return self.coverage_share(node_id) if node_id in self.coverage_nodes() else 1.0

    def people_per_unit(self, node_id):
        """How many people one unit of the work serves: its yearly staff hours over the hours each person needs."""
        spec = self.mechanic(node_id, "coverage")
        hours = sum((self.nodes[node_id].get("annual_labour_hours") or {}).values())
        return hours / spec["staff_hours_per_person_year"]

    def people_who_can_use(self, node_id):
        """The people the work could serve: the nation's, or the share of them its `eligible_share` names."""
        return max(1.0, self.population.total * self.mechanic(node_id, "coverage").get("eligible_share", 1.0))

    def coverage_share(self, node_id):
        """The share of the people who can use the work that it serves while it is open, 0 to 1."""
        if not self.running(node_id):
            return 0.0
        people = self.institution_units(node_id) * self.people_per_unit(node_id)
        return min(1.0, people / self.people_who_can_use(node_id))

    def units_for_coverage(self, node_id, share):
        """The units that serve `share` of the people who can use the work."""
        return share * self.people_who_can_use(node_id) / self.people_per_unit(node_id)

    def coverage_row(self, node_id):
        """What the `rollout` listing says of one work."""
        spec = self.mechanic(node_id, "coverage")
        return {"id": node_id, "name": self.nodes[node_id]["name"], "serves": spec.get("serves", "people"),
                "units": round(self.institution_units(node_id), 3),
                "covered": round(self.coverage_share(node_id), 4),
                "people_per_unit": round(self.people_per_unit(node_id), 1),
                "units_for_everyone": round(self.units_for_coverage(node_id, 1.0), 1),
                "most_units_the_nation_can_fill": round(self.institution_unit_ceiling(node_id), 1)}

    def roll_out(self, node_id, share):
        """(ok, text): open more of the work, or open it, to cover `share` of the nation's people. The cost, the
        staff and the ceiling on units are the ordinary ones of opening or expanding a venture."""
        if node_id not in self.coverage_nodes() or node_id not in self.nodes:
            return False, "that is not a work that can be rolled out"
        if node_id not in self.state.projects.done:
            return False, "you have not worked out how to do that yet"
        wanted = self.units_for_coverage(node_id, share)
        have = self.institution_units(node_id)
        if wanted - have < 0.02:
            return False, "%s already covers %d%% of the people" % (
                self.nodes[node_id]["name"], round(100 * self.coverage_share(node_id)))
        ok, text = self.open_venture(node_id, units=wanted - have if have > 0.0 else wanted)
        if not ok:
            return False, text
        return True, "%s It now covers %d%% of the people." % (text, round(100 * self.coverage_share(node_id)))
