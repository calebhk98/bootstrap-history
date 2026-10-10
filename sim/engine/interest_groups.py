"""What the founder sees of the interest groups the economy has made: who is organised, how
many people they speak for, what they lost and to what, and what the state is doing about it.

Methods of Sim. The groups themselves are actors (`sim/agents/group.py`); this is the
reading side, plus the one prohibition check the start gate calls.
"""
from sim.agents.api import Sector, supply
from . import need_substitutes
from .blockers import blocker_kind
from .units_prose import money_text


class InterestGroupsMixin:

    def _group_records(self):
        state = self.state.actors
        if state is None or not state.records:
            return []
        return [group.record for group in self.actors.of_kind("interest_group")
                if group.record.exited_year is None]

    def interest_groups(self):
        """One row per organised group: name, cause, size, loss, pull and what it asks."""
        rows = []
        for record in self._group_records():
            rows.append({"name": record.name, "kind": record.group_kind, "cause": record.cause,
                         "people": round(record.members), "income_lost_per_year": round(record.lost_income),
                         "grievance_share": round(record.grievance, 3),
                         "pull_on_the_state": round(record.strength, 3),
                         "state_undertakes_to_make_good": round(record.claim),
                         "demands": list(record.demands), "technique": record.technique, "petitions": record.petitions,
                         "organised_since": record.founded_year})
        return rows

    def interest_groups_report(self):
        """The `groups` screen: every organised group, what the state does about each, and
        what it costs you."""
        rows = self.interest_groups()
        if not rows:
            return {"groups": [], "note": "no body of people has lost enough to your doing to organise "
                                          "against you; see 'market' for the goods you sell and the trades you press"}
        treasury = self.state_treasury().record
        owed = {name: amount for name, amount in treasury.unfunded.items() if name.startswith("concession: ")}
        return {"groups": rows,
                "state_leaves_unpaid_to_raise_from_taxpayers": round(sum(owed.values())),
                "state_in_deficit": sum(treasury.unfunded.values()) > 1e-9,
                "note": "A group's pull is the share of the state's attention its lost income earns. The "
                        "state makes good what its capacity lets it and its purse pays; what it cannot "
                        "pay is raised from taxpayers it can see, which includes you, and a state not in "
                        "deficit may forbid the techniques that hurt the group. Protection above the "
                        "state-opposition line lets you build despite a prohibition"}

    def group_levy_reasons(self):
        """Why the requisition is larger than the ordinary rate: the groups the state is paying."""
        state = self.state.actors
        if state is None or not state.records:
            return []
        owed = self.state_treasury().record.unfunded
        reasons = []
        for record in self._group_records():
            amount = owed.get("concession: group:%s:%s" % (record.group_kind, record.subject), 0.0)
            if amount > 0.5:
                reasons.append("the state is making good %s a year to %s (%s) and raising what its purse "
                               "cannot pay from the taxpayers it sees"
                               % (money_text(record.claim, self, grouped=True), record.name, record.cause))
        return reasons

    def _technique_bans(self):
        """technique -> (name of the group, its pull) for the groups whose demand is to forbid one technique."""
        bans = {}
        for group in self.actors.of_kind("interest_group"):
            record = group.record
            if record.exited_year is None and record.demands and record.technique:
                bans[record.technique] = (record.name, record.strength)
        return bans

    def _banned_materials(self, technique):
        """The materials a forbidden technique makes and their substitutes (goods that serve the same needs):
        a technique that makes any of them does the forbidden technique's work another way."""
        cache = self.__dict__.setdefault("_banned_materials_cache", {})
        if technique not in cache:
            made = set(supply.materials_made_by(technique))
            cache[technique] = made.union(*(need_substitutes.substitutes_of(material) for material in made))
        return cache[technique]

    def group_prohibition_of(self, node_id):
        """(group name, subject, group pull) for the interest group whose demand has the state forbid
        starting this node, or None. A group of producers is met by the node reached through what it makes
        or what substitutes for it, its own goods category and the line of techniques it refines (see
        `Sector.reached_by`); a group of workers out of a job is met by the technique that did their work
        with fewer hands and by any technique that makes what it makes or a substitute for it. A node the
        state itself values is not forbidden."""
        state = self.state.actors
        if state is None or not state.records:
            return None
        banned = self.actors.prohibitions()
        by_technique = self._technique_bans()
        if (not banned and not by_technique) or self.state_interest(self.nodes[node_id]) > 0.0:
            return None
        reached = Sector.reached_by(node_id, self.nodes, supply.materials_made_by,
                                    lambda material: self._material_tag(material)[0],
                                    need_substitutes.substitutes_of)
        for subject in sorted(reached & set(banned)):
            strength = max((group.record.strength for group in self.actors.of_kind("interest_group")
                            if group.record.subject == subject and group.record.demands and not group.record.technique),
                           default=0.0)
            return banned[subject], subject, strength
        made = set(supply.materials_made_by(node_id))
        for technique, (name, strength) in sorted(by_technique.items()):
            if node_id == technique or made & self._banned_materials(technique):
                return name, self.nodes[technique].get("name", technique), strength
        return None


@blocker_kind("politics")
def check_group_prohibition(self, node_id, node, ignore_trade, _memo, _why):
    banned = self.group_prohibition_of(node_id)
    if banned is None:
        return None
    needed = Sector.protection_needed(banned[2], self.STATE_OPPOSITION_PROTECTION_OVERRIDE)
    if self.state.household.protection > needed:
        return None
    return False, (("the state has forbidden this at the petition of %s, who lose their living to "
                    "what it makes (%s); protection above %.2f (you have %.2f) lets you build "
                    "regardless" % (banned[0], banned[1], needed, self.state.household.protection))
                   if _why else None)
