"""Replay carry-over (Complaint 267): the `again` command of `play` starts a new game with the built routes. The game is a stub holding what the command reads: the done set, the granted set and the reason it ended."""
import contextlib
import io
import os
import tempfile
from types import SimpleNamespace

from .harness import check
from sim.ui import cli_interactive, replay

QUICK_TOPIC = True


def _again(game, session):
    """Type `again` at play's command handler; returns (reply, routes handed to the new game)."""
    handed = {}

    def fake_new_game(civs, cfg, known_routes=None):
        handed["routes"] = known_routes
        return 0

    saved = cli_interactive._new_game, cli_interactive._load_civ_list
    cli_interactive._new_game, cli_interactive._load_civ_list = fake_new_game, lambda: []
    printed = io.StringIO()
    try:
        with contextlib.redirect_stdout(printed):
            reply = cli_interactive._play_handle_session_command("again", ["again"], game, session, {}, None)
    finally:
        cli_interactive._new_game, cli_interactive._load_civ_list = saved
    return reply, handed.get("routes"), printed.getvalue()


_built = "built_route"
_game = SimpleNamespace(done={_built, "granted_route"}, granted={"granted_route"}, dead_reason=None,
                        fog=False, revealed=set(), capital=100.0, state=SimpleNamespace(interface={}),
                        cfg={"start_year": 0, "horizon_years": 100}, year=0)

_reply, _routes, _text = _again(_game, None)
check("again before the game ends does nothing but explain", _reply == (True, None, False, None) and _routes is None
      and _text, (_reply, _routes, _text))
# presentation: the explanation says the new game waits for the end of this one
check("...and says why", "once this game has ended" in _text, _text)

_game.dead_reason = "the founder died"
with tempfile.TemporaryDirectory() as folder:
    _session = os.path.join(folder, "run.json")
    _reply, _routes, _text = _again(_game, _session)
    check("again after the end starts a new game with the routes built", _reply == (True, _session, True, 0)
          and _built in _routes, (_reply, _routes))
    check("...and writes them beside the session",
          replay.read_known_routes(replay.routes_path(_session)) == _routes)
    check("...but never what the society already had", not set(_routes) & set(_game.granted), _routes)

_reply, _routes, _text = _again(_game, None)
check("again with no session still carries the routes", _built in _routes, _routes)
