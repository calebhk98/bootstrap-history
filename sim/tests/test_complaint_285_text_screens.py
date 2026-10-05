"""Complaint 285: no text screen prints a quantity in a unit the player did not choose.

A short game is played (land bought, years stepped), non-default units are
chosen for every dimension, and every read-only text screen is rendered. A
screen fails when it still prints a native unit label (tonne, hectare, den),
and a reply fails when a numeric field that reads like a quantity has no field
rule (so no converted sibling could exist for it).
"""
from .harness import *
import re as _re
from sim.engine import units as U
from sim.ui.proto.dispatch import _agent_dispatch
from sim.ui.proto.render_typed import render_pretty

SCREENS = ["state", "money", "materials", "market", "figures", "risk", "labour", "economy",
           "capacity", "mines", "stuck", "values", "score", "population", "map", "education",
           "demography", "divergence", "commitments", "groups", "available", "portfolio",
           "changes", "cashbook", "automation", "ventures", "goals", "policy", "causes", "idle",
           "options", "log", "leverage", "priority", "programme", "saving", "work", "pursue"]
# Screens that need arguments.
ARGUMENT_SCREENS = [{"cmd": "quote", "what": "mine", "material": "coal", "n": 500},
                    {"cmd": "buy", "what": "farm", "n": 5}, {"cmd": "buy", "what": "forest", "n": 5}]
CHOICES = {"mass": "pound", "area": "acre", "money": "labour_hour", "temperature": "fahrenheit"}
# A native unit label printed as a word, as a symbol, or as the per-mass price header.
NATIVE_LABEL = _re.compile(
    r"\btonnes?\b|\bkg\b|\bt/yr\b|/T\b|\bhectares?\b|\bha\b|/ha\b|\bm2\b|\bden\b|denarii|\bcelsius\b|\biugera\b")
# Numeric reply fields that read like a quantity of money, mass or area.
QUANTITY_KEY = _re.compile(
    r"(^|_)(tonnes?|kg|hectares?|ha|den|price|cost|costs|wage|wages|revenue|debt|cash|capital|"
    r"interest|bill|income|net|earns|spend)($|_)")
# Fields whose name matches but that are counts, ratios, indices or rates.
NOT_A_QUANTITY = _re.compile(
    r"(index|ratio|rate|chance|share|fraction|count|number|price_over_long_run_cost|food_cost_factor|startable_at_no_cash_cost|"
    r"founder_hours|wage_work|in_bondage_for_debt)")

game = sim(capital=5_000_000.0)
game.end_year = game.cfg["start_year"] + game.cfg["horizon_years"]
for _command in ({"cmd": "buy", "what": "farm", "n": 50}, {"cmd": "buy", "what": "forest", "n": 20},
                 {"cmd": "step", "years": 3}):
    _agent_dispatch(game, NODES, _command)

U.set_registry(U.load_units(ROOT))
registry = U.registry()
unruled = {}


def _unruled_keys(node, screen):
    if isinstance(node, dict):
        for key, value in node.items():
            if isinstance(value, (dict, list)):
                _unruled_keys(value, screen)
            elif (isinstance(value, (int, float)) and not isinstance(value, bool)
                  and not key.endswith("_display") and QUANTITY_KEY.search(key)
                  and not NOT_A_QUANTITY.search(key) and not U.field_rule(registry, key)):
                unruled.setdefault(key, screen)
    elif isinstance(node, list):
        for item in node:
            _unruled_keys(item, screen)


U.set_preferences(CHOICES)
for command in [{"cmd": name} for name in SCREENS] + ARGUMENT_SCREENS:
    screen = "%s %s" % (command["cmd"], command.get("what", "")) if len(command) > 1 else command["cmd"]
    reply = _agent_dispatch(game, NODES, dict(command))
    _unruled_keys(reply, screen)
    text = render_pretty(command["cmd"], reply)
    # Lines that show command syntax name the unit a command accepts; they are not quantities.
    shown = [line for line in text.splitlines() if "<" not in line and '{"cmd"' not in line]
    leaks = [line.strip() for line in shown if NATIVE_LABEL.search(line)]
    check("285 screen %s prints no native unit label" % screen, not leaks, leaks[:4])
check("285 every quantity-like numeric field has a unit rule", not unruled, unruled)

# The default choice leaves every screen as the game wrote it.
U.set_preferences({})
for screen in ("state", "materials", "market"):
    check("285 default %s still reads native" % screen,
          NATIVE_LABEL.search(render_pretty(screen, _agent_dispatch(game, NODES, {"cmd": screen}))) is not None)
U.set_registry(None)
