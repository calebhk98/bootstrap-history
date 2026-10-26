"""What a seat does with an invention it made: keep it secret, license it, or publish it.

Needs: tree, techniques_held, techniques_granted, operating, year, reputation_gain_of, seat_list, seat_party,
legacy_actor_registry, legacy_agent_world, acting_seat."""
from typing import Any, Dict, List, Optional

from sim.agents.api import licence
from sim.polity.api import GainReputation
from sim.rekey import rekey

from . import rules


class Disclosure:

    def slot_of(self, seat_id: Optional[str]) -> Any:
        """The state of `seat_id`, or of the acting seat when none is named."""
        return self.seat if seat_id is None or seat_id == self.clock.acting_seat else self.seat_of(seat_id)

    def disclosure(self, node_id: str) -> Dict[str, Any]:
        """The seat's choice for an invention; `default` is how it spreads with no choice made."""
        record = self.seat.disclosures.get(node_id)
        return rules.default_disclosure() if record is None else record

    def disclosures(self, seat_id: str) -> Dict[str, Dict[str, Any]]:
        """Everything seat `seat_id` has chosen: node id to its record. Read only."""
        return self.slot_of(seat_id).disclosures

    def copy_difficulty(self, node_id: str) -> float:
        """How hard the know-how is to copy from sight."""
        return rules.copy_difficulty_of(self.tree_node(node_id))

    def _record(self, node_id: str) -> Dict[str, Any]:
        records = self.seat.disclosures
        if node_id not in records:
            records[node_id] = rules.default_disclosure()
        return records[node_id]

    def disclose(self, command: Any) -> Dict[str, Any]:
        """Choose what to do with an invention you made. Answers {"ok", "error" or "note"}."""
        node_id, mode = command.node_id, command.mode
        done = self.needs.techniques_held()
        problem = rules.disclosure_problem(self.needs.tree[node_id] is not None and node_id in done,
                                           node_id not in self.needs.techniques_granted(), mode,
                                           self.disclosure(node_id)["mode"])
        if problem is not None:
            return problem
        if mode == "license":
            return self._license(node_id, command.licensee, float(command.fee or 0.0), float(command.royalty or 0.0))
        record = self._record(node_id)
        record["mode"] = mode
        if mode == "publish":
            if record["published_year"] is None:
                record["published_year"] = self.needs.year()
                self.needs.send(GainReputation(self.needs.reputation_gain_of(node_id)))
            return {"ok": True, "note": "published: anyone may copy it, and your name is on it"}
        return {"ok": True, "note": "kept secret: outsiders learn it only as fast as its trades and materials allow"}

    def _license(self, node_id: str, licensee_id: Optional[str], fee: float, royalty: float) -> Dict[str, Any]:
        acting = self.clock.acting_seat
        licensee = self.needs.legacy_actor_registry().get(licensee_id) if licensee_id else None
        if licensee is None and licensee_id in self.needs.seat_list()["joined"] and licensee_id != acting:
            licensee = self.needs.seat_party[licensee_id]   # another player
        if licensee is None or licensee.kind == "interest_group":
            return {"ok": False, "error": "name a firm or the state to license it to: %s" % (
                ", ".join(self.licensable_actor_ids()) or "none exist yet")}
        problem = licence.terms_problem(licensee, fee, royalty, node_id, self.needs.legacy_agent_world())
        if problem:
            return rules.refusal_reply(problem)
        if not licence.grant(self.needs.seat_party[acting], licensee, node_id, fee, self.needs.legacy_agent_world()):
            return {"ok": False, "error": "the licensee can already make it"}
        record = self._record(node_id)
        if record["mode"] == "default":
            record["mode"] = "license"
        record["licensees"][licensee_id] = {"fee": fee, "royalty": royalty, "year": self.needs.year()}
        return {"ok": True, "note": "licensed to %s" % licensee_id}

    def licensable_actor_ids(self) -> List[str]:
        """Firms, the state and the other seats still playing."""
        acting = self.clock.acting_seat
        others = [seat_id for seat_id in self.needs.seat_list()["playing"] if seat_id != acting]
        registry = self.needs.legacy_actor_registry()
        return [actor.identity() for kind in ("firm", "government") for actor in registry.of_kind(kind)
                if getattr(actor.record, "exited_year", None) is None] + others

    def disclosure_listing(self) -> List[Dict[str, Any]]:
        """Every invention of yours with what you have chosen for it."""
        made = self.needs.techniques_held() - self.needs.techniques_granted()
        return rules.disclosure_listing(made, {node_id: self.disclosure(node_id) for node_id in made},
                                        self.needs.operating())

    def rekey_disclosures(self, command: Any) -> None:
        """A seat handed over to another id: the licences and disclosures that named the old id name the new one."""
        rekey(self.slot_of(command.seat).disclosures, command.from_id, command.to_id)
