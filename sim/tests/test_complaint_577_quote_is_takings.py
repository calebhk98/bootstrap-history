"""Complaints/577: a concern's quoted earnings and its takings once open read one function at the same prices."""
from .harness import *  # noqa: F401,F403
from .harness import _mk_loom_sim

# a concern whose output the market prices below its long-run cost is quoted at that price before it is opened
_game = sim(civ="rome_100ad", capital=5_000_000.0)
_node_id = "pwr_coking"
_market = _game.node_output_market_factor(_game.nodes[_node_id])
_quote = _game.venture_real_earnings(_node_id)
_game.state.projects.done.add(_node_id)
_game._done_changed()
check("the quote before opening applies the market's price for the concern's goods",
      abs(_quote - _game.concern_takings(_node_id, 1.0) * _market) < 1e-6, (_quote, _market))

# once open, the screens' figure and the sum `revenue` takes are the same number
_loom, _chosen = _mk_loom_sim(1, 5)
_node_id = _chosen[0]
_output_factor = _loom.state.economy.output_factor
check("an open concern's quoted earnings are what revenue() sums for it",
      abs(_loom.venture_real_earnings(_node_id) - _loom.concern_revenue(_node_id) * _output_factor) < 1e-6,
      (_loom.venture_real_earnings(_node_id), _loom.concern_revenue(_node_id)))
check("the ledger row for it is the same figure",
      _node_id not in _loom.ledger_concern_rows()
      or abs(_loom.ledger_concern_rows()[_node_id] - _loom.venture_real_earnings(_node_id)) < 0.1,
      _loom.ledger_concern_rows())
_before = _loom.venture_real_earnings(_node_id, fully_ramped=True)
check("a fully ramped quote does not move with the ramp",
      abs(_before - _loom.venture_real_earnings(_node_id, fully_ramped=True, with_output_factor=False) * _output_factor) < 1e-6,
      _before)
