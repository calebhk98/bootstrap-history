"""One classifier for why a project cannot begin.

`why`, `why ... compact`, `stuck`, `available` and the `start` refusal all
read `start_blockers`, so a readout cannot disagree with the gate: the gate
is the same list. Each entry is {"kind", "text", "ids"}.

Kinds: knowledge (prerequisites missing), power (a power capability missing),
supply (a material or vessel group with no option in hand), specialists
(people or trades missing), money (the bill is past cash and credit),
politics (the state or a patron), closed (built once but shut),
calendar (a floor of years still to serve, shown by `stuck`), hours (running
work waiting on the founder's own directed hours), idle (nothing in hand) and the terminal ones (done, active, goal, unavailable) where nothing is left to fix.
"""


BLOCKER_KINDS = frozenset((
    "knowledge", "power", "supply", "specialists", "money", "politics", "closed",
    "goal", "done", "active", "unavailable", "calendar", "idle", "hours"))

# Running work reads its blocker from the portfolio's constraint (the sentence
# `waiting_on` builds); this names the shared kind each constraint stands for.
RUNNING_CONSTRAINT_KIND = {
    "staffing": "specialists", "trade_hours": "specialists", "materials": "supply",
    "money": "money", "calendar": "calendar", "founder_hours": "hours", "unclear": "idle"}

BLOCKER_MEANING = {
    "specialists": "a trade is short or already booked: hire or train it, or pause a project that shares it",
    "supply": "a material is throttling the whole economy: buy or sink the source",
    "money": "the bill outruns what you can raise: wait, sell, or pause a draw",
    "calendar": "only the calendar floor is left: it cannot be bought, so spend the hours elsewhere",
    "hours": "your own directed hours are fully committed: reprioritise or raise the pool",
    "idle": "no single cause is named: 'why <id>' for the project"}


def blocker_kind(kind):
    """Mark a start check with the kind of blocker it reports."""
    if kind not in BLOCKER_KINDS:
        raise ValueError("unknown blocker kind %r" % kind)

    def mark(check):
        check.blocker_kind = kind
        return check
    return mark


class BlockersMixin:

    BLOCKER_KINDS = BLOCKER_KINDS
    _TERMINAL_BLOCKER_KINDS = ("goal", "done", "active", "unavailable", "closed")

    def _visible_to_player(self, node_id):
        return not self.fog or node_id in self.nodes and self.is_visible(node_id)

    def _is_power_capability(self, node_id):
        return "power_tier" in (self.nodes.get(node_id, {}).get("mechanics") or {})

    def _power_gate_text(self, power_ids):
        return ("%s %s a knowledge gate, not installed capacity: your installed "
                "generation (%.0f kW) does not satisfy it, the named capability "
                "has to be reached"
                % (", ".join(power_ids), "is" if len(power_ids) == 1 else "are",
                   self.generation_capacity_kw()))

    def _missing_prereq_entries(self, node_id, node, text):
        missing = [prereq_id for prereq_id in node["pre"] if prereq_id not in self.state.projects.done
                   and self._visible_to_player(prereq_id)]
        power_ids = [prereq_id for prereq_id in missing if self._is_power_capability(prereq_id)]
        plain_ids = [prereq_id for prereq_id in missing if prereq_id not in power_ids]
        entries = []
        hidden_missing = any(prereq_id not in self.state.projects.done
                             and not self._visible_to_player(prereq_id) for prereq_id in node["pre"])
        if plain_ids or hidden_missing or not power_ids:
            entries.append({"kind": "knowledge", "ids": plain_ids,
                            "text": text if not power_ids else self.missing_prereq_message(plain_ids)})
        if power_ids:
            entries.append({"kind": "power", "ids": power_ids, "text": self._power_gate_text(power_ids)})
        return entries

    def _classify_check(self, check, node_id, node, text):
        kind = check.blocker_kind
        check_name = check.__name__
        if check_name == "_check_missing_prereqs":
            return self._missing_prereq_entries(node_id, node, text)
        ids = []
        if kind == "supply":
            _group, options = getattr(self.household, "_last_subst_gap", None) or (None, [])
            ids = [option for option in options if self._visible_to_player(option)]
        if kind == "done" and self.is_venture(node_id) and not self.running(node_id):
            kind = "closed"
            text = ("you have built it already but it is shut: 'open %s' to run it" % node_id)
        if check_name == "_check_already_done" and node_id in self.state.projects.mothballed:
            kind = "closed"
        return [{"kind": kind, "ids": ids, "text": text}]

    def start_blockers(self, node_id, extra_owed=0.0):
        """Every reason the project cannot begin now, in the order the gate
        reads them; [] when it can. Changes no state. extra_owed is money
        already committed by starts not yet applied (a preview's earlier picks).
        """
        if node_id not in self.nodes:
            return [{"kind": "unavailable", "ids": [], "text": "no such node"}]
        node = self.nodes[node_id]
        blockers = []
        for check in self._START_REASON_CHECKS:
            verdict = check(self, node_id, node, False, None, True)
            if verdict is None or verdict[0]:
                continue
            entries = self._classify_check(check, node_id, node, verdict[1])
            blockers.extend(entries)
            if any(entry["kind"] in self._TERMINAL_BLOCKER_KINDS for entry in entries):
                return blockers
        money = self._money_refusal(node_id, extra_owed)
        if money:
            blockers.append({"kind": "money", "ids": [], "text": money})
        return blockers
