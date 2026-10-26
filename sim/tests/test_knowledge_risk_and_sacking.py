"""What a sacking costs: the corpus hedge a sacking faces, which technologies it can take and how many, and what
the KNOWLEDGE LOST announcement says (Complaint 640: the rules are called on a stub game built here; the whole-game
checks that `risk` told the truth and that a sack's own report matches the headcount are in
test_knowledge_risk_and_sacking_scenario)."""
QUICK_TOPIC = True

import types

from .harness import *  # noqa: F401,F403
from sim.engine.forward_mechanics import ForwardMechanicsMixin
from sim.engine.society_hazards import HazardsMixin
from sim.refusal import cause_of, facts_of


class _FrontOfTheListRNG:
    """sample() takes the front of the list, so how many are lost depends only on the fraction, never on luck."""

    def sample(self, population, count):
        return list(population)[:count]


class _SackGame:
    """Only what the hedge and the corpus-loss rules read."""
    CORPUS_HEDGE_LOSS_CHANCE_NONE = S.Sim.CORPUS_HEDGE_LOSS_CHANCE_NONE
    CORPUS_HEDGE_FRACTION_LOST_NONE = S.Sim.CORPUS_HEDGE_FRACTION_LOST_NONE
    corpus_hedge = S.Sim.corpus_hedge
    losable_node_ids = ForwardMechanicsMixin.losable_node_ids
    _sack_corpus_loss = HazardsMixin._sack_corpus_loss
    _log_corpus_loss = HazardsMixin._log_corpus_loss

    def __init__(self, built=(), granted=(), held=(), goal=None, dispersed=("corpus_dispersed",)):
        tiers = [("corpus_dispersed", 0.2, 0.08), ("corpus_written", 0.5, 0.22)]
        self._tiers, self._held, self._dispersed = tiers, set(held), set(dispersed)
        self.nodes = {node_id: {"win_condition": False, "pre": []} for node_id in
                      ("corpus_dispersed", "corpus_written", "a", "b", "c", "d", "e", "f", "g", "h", "i", "j")}
        self.nodes["j"] = {"win_condition": True, "pre": []}
        self.goal = goal
        self.rng = _FrontOfTheListRNG()
        self.state = types.SimpleNamespace(
            projects=types.SimpleNamespace(done=set(built), granted=set(granted), operating=set(built), mothballed=set(),
                                           forgotten={}),
            household=types.SimpleNamespace(log=[]))
        self.done_changed = 0

    def corpus_hedge_tiers(self):
        return list(self._tiers)

    def has(self, node_id):
        return node_id in self._held

    def corpus_is_dispersed(self, node_id):
        return node_id in self._dispersed

    def nodes_with_mechanic(self, name):
        return ["corpus_dispersed", "corpus_written"]

    def best_corpus_node(self):
        return "corpus_dispersed"

    def _done_changed(self):
        self.done_changed += 1


# --- the hedge a sacking faces: the strongest corpus held, whether or not it runs.
check("with no corpus held the undefended chance and fraction apply and no hedge is named",
      _SackGame().corpus_hedge() == (S.Sim.CORPUS_HEDGE_LOSS_CHANCE_NONE, S.Sim.CORPUS_HEDGE_FRACTION_LOST_NONE, None))
check("a written corpus held is credited with its own chance and fraction",
      _SackGame(held=("corpus_written",)).corpus_hedge() == (0.5, 0.22, "corpus_written"))
check("a dispersed corpus held is credited, and it is the stronger",
      _SackGame(held=("corpus_written", "corpus_dispersed")).corpus_hedge() == (0.2, 0.08, "corpus_dispersed"))

# --- which technologies a sack can take.
_built = ("corpus_dispersed", "corpus_written", "a", "b", "c", "d", "e", "f", "g", "j")
_game = _SackGame(built=_built, granted=("a", "b"))
check("what a sack can take excludes inherited technologies, a measured goal and a dispersed corpus",
      _game.losable_node_ids() == ["c", "corpus_written", "d", "e", "f", "g"], _game.losable_node_ids())
check("...and a dispersed corpus counts when asked for",
      "corpus_dispersed" in _game.losable_node_ids(keep_dispersed=False))

# --- what a sack forgets.
_sacked = _SackGame(built=_built, granted=("a", "b"))
_sacked._sack_corpus_loss(150, 0.5, "corpus_dispersed")
check("the sack takes the stated fraction of what it can take, and no more",
      len(_sacked.state.projects.forgotten) == int(6 * 0.5), _sacked.state.projects.forgotten)
check("what is forgotten is no longer built, running or mothballed, and is dated",
      all(node_id not in _sacked.state.projects.done and node_id not in _sacked.state.projects.operating
          and year == 150 for node_id, year in _sacked.state.projects.forgotten.items()), _sacked.state.projects.forgotten)
check("a dispersed corpus and inherited technologies survive a sack",
      {"corpus_dispersed", "a", "b"} <= _sacked.state.projects.done, _sacked.state.projects.done)
check("the built set is told to refresh", _sacked.done_changed == 1)
_tiny = _SackGame(built=("corpus_written",))
_tiny._sack_corpus_loss(150, 0.01, "corpus_dispersed")
check("a sack that takes anything takes at least one technology", len(_tiny.state.projects.forgotten) == 1)
_nothing = _SackGame(built=("corpus_dispersed",))
_nothing._sack_corpus_loss(150, 0.5, "corpus_dispersed")
check("with nothing it can take it forgets nothing and says nothing", not _nothing.state.projects.forgotten
      and not _nothing.state.household.log)

# --- what the announcement carries.
_lines = [line for _year, line in _sacked.state.household.log]
check("a sack names the technologies it destroyed", len(_lines) == 1 and cause_of(_lines[0]) == "knowledge_lost"
      and sorted(facts_of(_lines[0])["forgotten"]) == sorted(_sacked.state.projects.forgotten), _lines)
_spared = _SackGame(built=_built, granted=("a", "b"))
_spared._sack_corpus_loss(150, 0.2, "corpus_dispersed")
check("a sack that does not reach the written corpus never claims the corpus went, nor that it was never dispersed",
      "corpus_written" not in _spared.state.projects.forgotten and not facts_of(_spared.state.household.log[0][1])["corpus_went"]
      and not facts_of(_spared.state.household.log[0][1])["corpus_never_dispersed"], facts_of(_spared.state.household.log[0][1]))
_undispersed = _SackGame(built=_built, granted=("a", "b"))
_undispersed._sack_corpus_loss(150, 0.5, "corpus_written")
check("a sack taken while only the written corpus stood says the corpus was never dispersed",
      facts_of(_undispersed.state.household.log[0][1])["corpus_never_dispersed"])
_corpus_goes = _SackGame(built=("corpus_written",), granted=())
_corpus_goes._sack_corpus_loss(150, 1.0, "corpus_written")
check("a sack that takes the corpus itself says so", facts_of(_corpus_goes.state.household.log[0][1])["corpus_went"])
_road = _SackGame(built=_built, granted=("a", "b"), goal="c")
_road.nodes["d"]["pre"] = ["c"]
_road.goal = "d"
_road._sack_corpus_loss(150, 1.0, "corpus_dispersed")
check("it counts how many forgotten technologies stood on the road to the goal",
      facts_of(_road.state.household.log[0][1])["on_road"] == 2, facts_of(_road.state.household.log[0][1]))
