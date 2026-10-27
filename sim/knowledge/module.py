"""The knowledge module: the tree, what each seat holds, lost and has heard of, and what fog lets it see.

What is held (`done`, `granted`, `done_year`), what is heard of (`revealed`), the tree and the fog switch are still
stored where the engine keeps them; the module reads and writes them through the `legacy_*` views (docs/architecture/
catalogue/knowledge.md lists every outside writer). What a seat has forgotten is the module's own state."""

from sim.assembly.api import Module

from . import fog_words, rules
from .commands import ForgetTechnique, LearnTechnique, RevealFrom, RevealNodes
from .constants import CORPUS_HEDGE_FRACTION_LOST_NONE, CORPUS_HEDGE_LOSS_CHANCE_NONE
from sim.production.api import RefreshDoneCaches

DONE = "done"
REVEALED = "revealed"


class Knowledge(Module):
    # ---- the tree and what a seat holds
    def tree(self, node_id):
        """The tree's node `node_id`, or None when the tree has none."""
        return self.needs.legacy_tree().get(node_id)

    def tree_nodes(self):
        """The whole tech tree, node data by id (the object itself: a re-derivation replaces it)."""
        return self.needs.legacy_tree()

    def techniques_held(self):
        """The nodes the acting seat holds, finished or granted (the live set)."""
        return self.needs.legacy_projects().done

    def techniques_revealed(self):
        """The nodes the acting seat has heard of under fog (the live set)."""
        return self.needs.legacy_projects().revealed

    def techniques_granted(self):
        """The held nodes its country already had, which are never counted as earned and never lost to a sack."""
        return self.needs.legacy_projects().granted

    def techniques_forgotten(self):
        """{node id: the year a sacking took it} for the acting seat (the live dict)."""
        return self.seat.forgotten

    def done_year(self):
        """{node id: the year the acting seat finished it}."""
        return self.needs.legacy_projects().done_year or {}

    def earliest_done_year(self, node_id, default):
        """The year the first seat to hold `node_id` finished it (`default` for a seat with no record)."""
        return rules.earliest_done_year(
            [(seat.projects.done, seat.projects.done_year) for seat in self.needs.legacy_seats().values()], node_id, default)

    def corpus_hedge(self):
        """(loss chance, fraction lost, hedge node or None) a sacking faces right now."""
        return rules.corpus_hedge(self.needs.corpus_hedge_tiers(), self.techniques_held(),
                                  CORPUS_HEDGE_LOSS_CHANCE_NONE, CORPUS_HEDGE_FRACTION_LOST_NONE)

    # ---- what fog lets the acting seat see
    def visibility(self, node_id, memo=None):
        """Whether the acting seat can see `node_id` at all: held, in hand, heard of, or startable now.

        `memo` is shared down one recursive descent (the start test asks visibility of each missing prerequisite, which
        asks the start test of its own): without it, one deep node costs a call per path to it. A fresh memo per
        outward-facing call keeps it exact; nothing is cached across commands."""
        if not self.needs.legacy_fog():
            return True
        projects = self.needs.legacy_projects()
        if node_id in projects.done or node_id in projects.active:
            return True
        if node_id in projects.revealed:
            return True
        memo = {} if memo is None else memo
        if node_id in memo:
            return memo[node_id]
        memo[node_id] = False  # provisional guard against cycles in the tree
        # startable now is visible; no message is built below the outermost call
        result = self.needs.start_check(node_id, False, memo, False)[0]
        memo[node_id] = result
        return result

    def visible_to_player(self, node_id):
        """Whether the player may be told about `node_id`: no fog, or a node of the tree that is visible."""
        return not self.needs.legacy_fog() or (node_id in self.needs.legacy_tree() and self.visibility(node_id, None))

    def prerequisite_message(self, missing, memo):
        """The one sentence for not-yet-held prerequisites, with the hidden ones unnamed; None when none are missing."""
        return fog_words.missing_prereq_message(
            self.needs.legacy_tree(), missing, lambda prereq_id: self.visibility(prereq_id, memo),
            self.needs.legacy_fog(), self.techniques_held())

    def fog_scrub(self, text):
        """`text` with every node id the acting seat has not heard of replaced; unchanged without fog or text."""
        if not text or not self.needs.legacy_fog():
            return text
        return fog_words.scrub_hidden_ids(text, self.needs.legacy_tree(), lambda node_id: self.visibility(node_id, None))

    def fog_summary(self, node_id):
        """One sentence about `node_id`, deliberately not the whole note and never what it unlocks."""
        return fog_words.summary_sentence(self.needs.legacy_tree()[node_id])

    def never_abandon(self, node_id):
        """Whether letting `node_id` go would cost the seat what it cannot rebuild or what its goal needs."""
        node = self.needs.legacy_tree()[node_id]
        return rules.never_abandon(self.needs.category_trait(node["cat"], "never_abandoned"),
                                   self.needs.relied_on_running[node_id], self.needs.on_road_to_goal(node_id))

    # ---- commands
    def learn_technique(self, command: LearnTechnique) -> None:
        projects = self.needs.legacy_projects()
        projects.done.add(command.node_id)
        self.needs.send(RefreshDoneCaches())
        self.bump_seat(DONE)
        if command.granted:
            projects.granted.add(command.node_id)
        if command.year is not None:
            if projects.done_year is None:
                projects.done_year = {}
            projects.done_year[command.node_id] = command.year

    def forget_technique(self, command: ForgetTechnique) -> None:
        projects = self.needs.legacy_projects()
        for node_id in command.node_ids:
            projects.done.discard(node_id)
            if command.year is not None:
                self.seat.forgotten[node_id] = command.year
        self.needs.send(RefreshDoneCaches())
        self.bump_seat(DONE)

    def reveal_from(self, command: RevealFrom) -> None:
        if not self.needs.legacy_fog():
            return
        self.needs.legacy_projects().revealed.update(rules.reveal_targets(self.needs.legacy_tree(), command.node_id))
        self.bump_seat(REVEALED)

    def reveal_nodes(self, command: RevealNodes) -> None:
        self.needs.legacy_projects().revealed.update(command.node_ids)
        self.bump_seat(REVEALED)
