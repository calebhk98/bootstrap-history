"""What the founder does with an invention: keep it secret, license it, or publish it."""
from sim.agents import SimWorld, licence

DISCLOSURE_MODES = ("default", "secret", "license", "publish")


class DisclosureMixin:

    def disclosure_of(self, node_id):
        """The founder's choice for an invention; `default` is how it spreads with no choice made."""
        record = self.state.projects.disclosures.get(node_id)
        if record is None:
            return {"mode": "default", "published_year": None, "licensees": {}}
        return record

    def copy_difficulty(self, node_id):
        """How hard the know-how is to copy from sight: the trades and the materials it needs, at least one."""
        node = self.nodes[node_id]
        trades = [trade for trade, hours in (node.get("lab") or {}).items() if hours > 0]
        materials = [material for material, amount in (node.get("mat") or {}).items() if amount]
        return max(1, len(trades) + len(materials))

    def _disclosure_record(self, node_id):
        records = self.state.projects.disclosures
        if node_id not in records:
            records[node_id] = {"mode": "default", "published_year": None, "licensees": {}}
        return records[node_id]

    def disclose(self, node_id, mode, licensee=None, fee=0.0, royalty=0.0):
        """Choose what to do with an invention you made. Returns {"ok", "error" or "note"}."""
        projects = self.state.projects
        if node_id not in self.nodes or node_id not in projects.done or node_id in projects.granted:
            return {"ok": False, "error": "you can only choose for an invention you have made yourself"}
        if mode not in DISCLOSURE_MODES[1:]:
            return {"ok": False, "error": "choose secret, license or publish"}
        current = self.disclosure_of(node_id)
        if current["mode"] == "publish":
            return {"ok": False, "error": "it is already published; that cannot be taken back"}
        if mode == "license":
            return self._license(node_id, licensee, float(fee or 0.0), float(royalty or 0.0))
        record = self._disclosure_record(node_id)
        record["mode"] = mode
        if mode == "publish":
            if record["published_year"] is None:
                record["published_year"] = self.state.scenario.year
                household = self.state.household
                household.reputation = min(self.REPUTATION_CEILING,
                                           household.reputation + self.reputation_gain_of(self.nodes[node_id]))
            return {"ok": True, "note": "published: anyone may copy it, and your name is on it"}
        return {"ok": True, "note": "kept secret: outsiders learn it only as fast as its trades and materials allow"}

    def _license(self, node_id, licensee_id, fee, royalty):
        licensee = self.actors.get(licensee_id) if licensee_id else None
        if licensee is None or licensee.kind == "interest_group":
            return {"ok": False, "error": "name a firm or the state to license it to: %s" % (
                ", ".join(self.licensable_actor_ids()) or "none exist yet")}
        problem = licence.terms_problem(licensee, fee, royalty)
        if problem:
            return {"ok": False, "error": problem}
        if not licence.grant(self.household, licensee, node_id, fee, SimWorld(self)):
            return {"ok": False, "error": "the licensee can already make it"}
        record = self._disclosure_record(node_id)
        if record["mode"] == "default":
            record["mode"] = "license"
        record["licensees"][licensee_id] = {"fee": fee, "royalty": royalty,
                                           "year": self.state.scenario.year}
        return {"ok": True, "note": "licensed to %s" % licensee_id}

    def licensable_actor_ids(self):
        return [actor.identity() for kind in ("firm", "government") for actor in self.actors.of_kind(kind)
                if getattr(actor.record, "exited_year", None) is None]

    def disclosure_listing(self):
        """Every invention of yours with what you have chosen for it."""
        projects = self.state.projects
        return [{"id": node_id, "mode": self.disclosure_of(node_id)["mode"],
                 "licensees": sorted(self.disclosure_of(node_id)["licensees"]),
                 "operating": node_id in projects.operating}
                for node_id in sorted(projects.done - projects.granted)]
