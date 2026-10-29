"""What a sacking costs: the corpus hedge a sacking faces, which technologies it can take and how many, and what
the KNOWLEDGE LOST announcement says (Complaint 640: the rules are called on a stub game built here; the whole-game
checks that `risk` told the truth and that a sack's own report matches the headcount are in
test_knowledge_risk_and_sacking_scenario)."""
QUICK_TOPIC = True

import types

from .harness import *  # noqa: F401,F403
from sim.engine import bridge_hazards
from sim.knowledge.api import closure
from sim.knowledge import rules as knowledge_rules
from sim.knowledge.api import (CORPUS_HEDGE_FRACTION_LOST_NONE, CORPUS_HEDGE_LOSS_CHANCE_NONE, ForgetTechnique, KnowledgeSeat)
from sim.production.api import RefreshDoneCaches
from sim.knowledge.module import Knowledge
from sim.projects.api import ShutForgotten
from sim.reporting.api import RecordEvent
from sim.tests import hazards_host, module_harness
from sim.tests.ui_stand_in import FactViews


class _FrontOfTheListRNG:
    """sample() takes the front of the list, so how many are lost depends only on the fraction, never on luck."""

    def sample(self, population, count):
        return list(population)[:count]


class _SackGame(FactViews):
    """The tree and the techniques a sack reads, with the hazards module built over them. A ForgetTechniques it sends is
    applied as the engine bridge applies it."""
    def __init__(self, built=(), granted=(), held=(), goal=None, dispersed=("corpus_dispersed",)):
        tiers = [("corpus_dispersed", 0.2, 0.08), ("corpus_written", 0.5, 0.22)]
        self._held, self._dispersed = set(held), set(dispersed)
        self.nodes = {node_id: {"win_condition": False, "pre": []} for node_id in
                      ("corpus_dispersed", "corpus_written", "a", "b", "c", "d", "e", "f", "g", "h", "i", "j")}
        self.nodes["j"] = {"win_condition": True, "pre": []}
        self.goal = goal
        self.state = types.SimpleNamespace(
            projects=types.SimpleNamespace(operating=set(built), mothballed=set()))
        self.done_changed = 0
        self.knowledge = module_harness.build(
            Knowledge, views={"legacy_tree": self.nodes, "corpus_dispersed": self.corpus_is_dispersed},
            answers={RefreshDoneCaches: lambda command: self._done_changed()}, seat=KnowledgeSeat(done=set(built), granted=set(granted)))
        self.losable_node_ids = self.knowledge.losable_node_ids
        self.module = hazards_host.build(
            game_random=_FrontOfTheListRNG(),
            corpus_hedge=lambda: knowledge_rules.corpus_hedge(tiers, self._held, CORPUS_HEDGE_LOSS_CHANCE_NONE,
                                                              CORPUS_HEDGE_FRACTION_LOST_NONE),
            corpus_nodes=["corpus_dispersed"], mechanic=lambda name: {"corpus_dispersed": {}, "corpus_written": {}},
            goal=lambda: {"node": self.goal}, tree_nodes=self.nodes, tree_closure=lambda goal_id: closure(self.nodes, goal_id),
            losable_node_ids=lambda keep_dispersed=True: self.knowledge.losable_node_ids(keep_dispersed),
            answers={ForgetTechnique: lambda command: self.knowledge.forget_technique(command),
                     ShutForgotten: lambda command: bridge_hazards.shut_forgotten(self, command)})

    def corpus_is_dispersed(self, node_id):
        return node_id in self._dispersed

    def _done_changed(self):
        self.done_changed += 1

    def sack(self, fraction, hedge):
        self.module.sack_corpus_loss(150, fraction, hedge)

    def lines(self):
        return [command for command in module_harness.sent(self.module) if isinstance(command, RecordEvent)]


# --- the hedge a sacking faces: the strongest corpus held, whether or not it runs.
check("with no corpus held the undefended chance and fraction apply and no hedge is named",
      _SackGame().module.needs.corpus_hedge() == (CORPUS_HEDGE_LOSS_CHANCE_NONE, CORPUS_HEDGE_FRACTION_LOST_NONE, None))
check("a written corpus held is credited with its own chance and fraction",
      _SackGame(held=("corpus_written",)).module.needs.corpus_hedge() == (0.5, 0.22, "corpus_written"))
check("a dispersed corpus held is credited, and it is the stronger",
      _SackGame(held=("corpus_written", "corpus_dispersed")).module.needs.corpus_hedge() == (0.2, 0.08, "corpus_dispersed"))

# --- which technologies a sack can take.
_built = ("corpus_dispersed", "corpus_written", "a", "b", "c", "d", "e", "f", "g", "j")
_game = _SackGame(built=_built, granted=("a", "b"))
check("what a sack can take excludes inherited technologies, a measured goal and a dispersed corpus",
      _game.losable_node_ids() == ["c", "corpus_written", "d", "e", "f", "g"], _game.losable_node_ids())
check("...and a dispersed corpus counts when asked for",
      "corpus_dispersed" in _game.losable_node_ids(keep_dispersed=False))

# --- what a sack forgets.
_sacked = _SackGame(built=_built, granted=("a", "b"))
_sacked.sack(0.5, "corpus_dispersed")
check("the sack takes the stated fraction of what it can take, and no more",
      len(_sacked.knowledge.seat.forgotten) == int(6 * 0.5), _sacked.knowledge.seat.forgotten)
check("what is forgotten is no longer built, running or mothballed, and is dated",
      all(node_id not in _sacked.knowledge.seat.done and node_id not in _sacked.state.projects.operating
          and year == 150 for node_id, year in _sacked.knowledge.seat.forgotten.items()), _sacked.knowledge.seat.forgotten)
check("a dispersed corpus and inherited technologies survive a sack",
      {"corpus_dispersed", "a", "b"} <= _sacked.knowledge.seat.done, _sacked.knowledge.seat.done)
check("the built set is told to refresh", _sacked.done_changed == 1)
_tiny = _SackGame(built=("corpus_written",))
_tiny.sack(0.01, "corpus_dispersed")
check("a sack that takes anything takes at least one technology", len(_tiny.knowledge.seat.forgotten) == 1)
_nothing = _SackGame(built=("corpus_dispersed",))
_nothing.sack(0.5, "corpus_dispersed")
check("with nothing it can take it forgets nothing and says nothing", not _nothing.knowledge.seat.forgotten
      and not _nothing.lines() and module_harness.sent(_nothing.module) == [])

# --- what the announcement carries.
_lines = _sacked.lines()
check("a sack names the technologies it destroyed", len(_lines) == 1 and _lines[0].kind == "knowledge_lost"
      and sorted(_lines[0].facts["forgotten"]) == sorted(_sacked.knowledge.seat.forgotten), _lines)
_spared = _SackGame(built=_built, granted=("a", "b"))
_spared.sack(0.2, "corpus_dispersed")
check("a sack that does not reach the written corpus never claims the corpus went, nor that it was never dispersed",
      "corpus_written" not in _spared.knowledge.seat.forgotten and not _spared.lines()[0].facts["corpus_went"]
      and not _spared.lines()[0].facts["corpus_never_dispersed"], _spared.lines()[0].facts)
_undispersed = _SackGame(built=_built, granted=("a", "b"))
_undispersed.sack(0.5, "corpus_written")
check("a sack taken while only the written corpus stood says the corpus was never dispersed",
      _undispersed.lines()[0].facts["corpus_never_dispersed"])
_corpus_goes = _SackGame(built=("corpus_written",), granted=())
_corpus_goes.sack(1.0, "corpus_written")
check("a sack that takes the corpus itself says so", _corpus_goes.lines()[0].facts["corpus_went"])
_road = _SackGame(built=_built, granted=("a", "b"), goal="c")
_road.nodes["d"]["pre"] = ["c"]
_road.goal = "d"
_road.sack(1.0, "corpus_dispersed")
check("it counts how many forgotten technologies stood on the road to the goal",
      _road.lines()[0].facts["on_road"] == 2, _road.lines()[0].facts)
