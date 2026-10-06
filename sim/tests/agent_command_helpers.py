"""Shared fixtures for the topics that drive agent commands against small games: ask a game
a command, build a fogged game, share one pristine game per civilisation for read-only questions."""
from .harness import S, NODES, sim


def ask_agent(game, **command):
    """Dispatch one agent command to `game`, giving it an end year if it has none yet."""
    if not hasattr(game, "end_year"):
        game.end_year = game.cfg["start_year"] + game.cfg["horizon_years"]
    return S._agent_dispatch(game, NODES, command)


def with_end_year(game):
    game.end_year = game.cfg["start_year"] + game.cfg["horizon_years"]
    return game


def fogged_game(civ="rome_100ad", **options):
    game = sim(civ=civ, **options)
    game.fog = True
    game.revealed = set()
    return game


_pristine_games = {}


def pristine_game(civ="rome_100ad"):
    """One untouched game per civilisation, built on first use. Only for commands that read the
    game (help, why, state, risk, policy, stall_diagnosis) and never for one a check changes."""
    if civ not in _pristine_games:
        _pristine_games[civ] = sim(civ=civ)
    return _pristine_games[civ]


def starved_game(cost_left, supply=0.02, arrears=0.8, capital=20000.0):
    """One project that cannot finish, in a year that is short of both the trade it needs and
    the money to pay for it."""
    game = sim(capital=capital)
    game.start_project("identity_cover")
    game.active["identity_cover"]["cost_left"] = cost_left
    real_supply = game.labour.market_supply
    game.labour.market_supply = lambda trade, _fallback=real_supply: _fallback(trade) * supply
    game.capital = -game.credit_limit() * arrears      # in arrears, inside the limit
    return game
