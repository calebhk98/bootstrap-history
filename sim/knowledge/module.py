"""The knowledge module: the tree, what each seat holds, lost and has heard of, and what fog lets it see.

What a seat holds (`done`, `granted`, `done_year`), has heard of (`revealed`) and has forgotten is the module's own seat state,
changed only by its commands and published as plain data. The tree is the module's too (replaced by `ReplaceTree`, never saved: a game is rebuilt over the same data); the
fog switch is the scenario's `fog_of_war`."""

from typing import Any, Dict, FrozenSet, Optional, Tuple

from sim.assembly.api import Module

from . import category_traits, fog_words, rules, tree_paths
from .commands import (ForgetTechnique, HandOverTechniques, LearnTechnique, NoteTechniquesChanged, ReceiveTechniques, RevealFrom, RevealNodes,
                       StartDoneYearRecord, ReplaceTree)
from .constants import CORPUS_HEDGE_FRACTION_LOST_NONE, CORPUS_HEDGE_LOSS_CHANCE_NONE
from sim.production.api import RefreshDoneCaches

DONE = "done"
REVEALED = "revealed"
HELD_CHANGES = "held_changes"   # the seat's held set changed where the caches over it are told (learning, forgetting, a re-derived tree)


class Knowledge(Module):
    def setup(self) -> None:
        self.nodes: Dict[str, Dict[str, Any]] = {}      # the tree; sent by the engine as the game is built
        self.catalogues: Dict[str, Dict[str, Any]] = {}  # the category traits by mods directory, read once

    def replace_tree(self, command: ReplaceTree) -> None:
        self.nodes = command.nodes

    # ---- the tree and what a seat holds
    def tree(self, node_id):
        """The tree's node `node_id`, or None when the tree has none."""
        return self.nodes.get(node_id)

    def tree_nodes(self):
        """The whole tech tree, node data by id (the object itself: a re-derivation replaces it)."""
        return self.nodes

    def _catalogue(self) -> Dict[str, Any]:
        directory = self.needs.mods_directory()
        if directory not in self.catalogues:
            self.catalogues[directory] = category_traits.load(directory)
        return self.catalogues[directory]

    def category_trait(self, category, trait):
        """Whether the data gives the node category `category` the flag `trait` (a category with no entry has none)."""
        return category_traits.has_trait(self._catalogue(), category, trait)

    def diffusion_traits(self):
        """The categories knowledge spreads by, in priority order: trait name to its entry."""
        return category_traits.diffusion_traits(self._catalogue())

    def techniques_held(self) -> FrozenSet[str]:
        """The nodes the acting seat holds, finished or granted."""
        return frozenset(self.seat.done)

    def techniques_version(self) -> tuple:
        """The change counter of the acting seat's held set, for memos over what is held: it moves exactly when the caches over
        the held set are told to drop (`LearnTechnique`, `ForgetTechnique`, `NoteTechniquesChanged`), not when a set is received."""
        return self.seat_version(HELD_CHANGES)

    def techniques_revealed(self) -> FrozenSet[str]:
        """The nodes the acting seat has heard of under fog."""
        return frozenset(self.seat.revealed)

    def techniques_granted(self) -> FrozenSet[str]:
        """The held nodes its country already had, which are never counted as earned and never lost to a sack."""
        return frozenset(self.seat.granted)

    def techniques_by_seat(self) -> Dict[str, rules.SeatTechniques]:
        """What every seat holds and what of it was granted, by seat id in joining order."""
        slots = {seat_id: self.seat_of(seat_id) for seat_id in self.needs.seat_list()["joined"]}
        return {seat_id: rules.SeatTechniques(frozenset(slot.done), frozenset(slot.granted)) for seat_id, slot in slots.items()}

    def losable_node_ids(self, keep_dispersed=True):
        """Built nodes a loss event may take: not inherited, not a measured goal, and by default not a dispersed corpus."""
        return rules.losable_node_ids(self.seat.done, self.seat.granted, self.tree_nodes(), keep_dispersed,
                                      self.needs.corpus_dispersed)

    def tree_closure(self, goal_id):
        """Every node the goal needs, following the mandatory prerequisites."""
        return tree_paths.closure(self.tree_nodes(), goal_id)

    def critical_path(self, goal_id):
        """(the longest chain's calendar years, the node ids on it) from the roots to `goal_id`."""
        return tree_paths.critical_path(self.tree_nodes(), goal_id)

    def hard_prerequisites(self, node_id):
        """Every prerequisite of a node that is mandatory: its `pre`, and the requirement groups that offer one real node."""
        return tree_paths.hard_pre(self.tree_nodes(), node_id)

    def techniques_forgotten(self):
        """{node id: the year a sacking took it} for the acting seat (the live dict)."""
        return self.seat.forgotten

    def done_year(self) -> Dict[str, int]:
        """{node id: the year the acting seat finished it}, as a copy."""
        return dict(self.seat.done_year or {})

    def earliest_done_year(self, node_id, default):
        """The year the first seat to hold `node_id` finished it (`default` for a seat with no record)."""
        return rules.earliest_done_year(
            [(slot.done, slot.done_year) for slot in (self.seat_of(seat_id) for seat_id in self.needs.seat_list()["joined"])],
            node_id, default)

    def corpus_hedge(self):
        """(loss chance, fraction lost, hedge node or None) a sacking faces right now."""
        return rules.corpus_hedge(self.needs.corpus_hedge_tiers(), self.seat.done,
                                  CORPUS_HEDGE_LOSS_CHANCE_NONE, CORPUS_HEDGE_FRACTION_LOST_NONE)

    # ---- what fog lets the acting seat see
    def visibility(self, node_id, memo=None):
        """Whether the acting seat can see `node_id` at all: held, in hand, heard of, or startable now.

        `memo` is shared down one recursive descent (the start test asks visibility of each missing prerequisite, which
        asks the start test of its own): without it, one deep node costs a call per path to it. A fresh memo per
        outward-facing call keeps it exact; nothing is cached across commands."""
        if not self.needs.fog_of_war():
            return True
        if node_id in self.seat.done or node_id in self.needs.active_projects():
            return True
        if node_id in self.seat.revealed:
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
        return not self.needs.fog_of_war() or (node_id in self.nodes and self.visibility(node_id, None))

    def prerequisite_message(self, missing, memo):
        """The one sentence for not-yet-held prerequisites, with the hidden ones unnamed; None when none are missing."""
        return fog_words.missing_prereq_message(
            self.nodes, missing, lambda prereq_id: self.visibility(prereq_id, memo),
            self.needs.fog_of_war(), self.seat.done)

    def fog_scrub(self, text):
        """`text` with every node id the acting seat has not heard of replaced; unchanged without fog or text."""
        if not text or not self.needs.fog_of_war():
            return text
        return fog_words.scrub_hidden_ids(text, self.nodes, lambda node_id: self.visibility(node_id, None))

    def fog_summary(self, node_id):
        """One sentence about `node_id`, deliberately not the whole note and never what it unlocks."""
        return fog_words.summary_sentence(self.nodes[node_id])

    def never_abandon(self, node_id):
        """Whether letting `node_id` go would cost the seat what it cannot rebuild or what its goal needs."""
        node = self.nodes[node_id]
        return rules.never_abandon(self.category_trait(node["cat"], "never_abandoned"),
                                   self.needs.relied_on_running[node_id], self.needs.on_road_to_goal(node_id))

    # ---- commands
    def learn_technique(self, command: LearnTechnique) -> None:
        self.seat.done.add(command.node_id)
        self.needs.send(RefreshDoneCaches())
        self.bump_seat(HELD_CHANGES)
        self.bump_seat(DONE)
        if command.granted:
            self.seat.granted.add(command.node_id)
        if command.year is not None:
            if self.seat.done_year is None:
                self.seat.done_year = {}
            self.seat.done_year[command.node_id] = command.year

    def receive_techniques(self, command: ReceiveTechniques) -> None:
        self.seat.done.update(command.node_ids)
        if command.granted:
            self.seat.granted.update(command.node_ids)
        self.bump_seat(DONE)

    def start_done_year_record(self, command: StartDoneYearRecord) -> None:
        self.seat.done_year = {}
        self.bump_seat(DONE)

    def hand_over_techniques(self, command: HandOverTechniques) -> int:
        leaver, heir = self.seat_of(command.from_seat_id), self.seat_of(command.to_seat_id)
        leaver.done |= heir.done
        leaver.granted |= heir.granted
        self.bump_seat(DONE, command.from_seat_id)
        self.bump_seat(DONE, command.to_seat_id)
        return len(leaver.done)

    def forget_technique(self, command: ForgetTechnique) -> None:
        for node_id in command.node_ids:
            self.seat.done.discard(node_id)
            if command.year is not None:
                self.seat.forgotten[node_id] = command.year
        self.needs.send(RefreshDoneCaches())
        self.bump_seat(HELD_CHANGES)
        self.bump_seat(DONE)

    def seat_bound(self) -> None:
        """What the acting seat holds is told to have changed, so the memos over it rebuild."""
        self.bump_seat(HELD_CHANGES)

    def note_techniques_changed(self, command: NoteTechniquesChanged) -> None:
        self.bump_seat(HELD_CHANGES)

    def reveal_from(self, command: RevealFrom) -> None:
        if not self.needs.fog_of_war():
            return
        self.seat.revealed.update(rules.reveal_targets(self.nodes, command.node_id))
        self.bump_seat(REVEALED)

    def reveal_nodes(self, command: RevealNodes) -> None:
        self.seat.revealed.update(command.node_ids)
        self.bump_seat(REVEALED)
