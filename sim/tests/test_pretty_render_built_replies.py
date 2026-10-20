"""The human renderings are called on replies built here, not on a running game: the money word of the place, the
ventures and labour screens, and the display width (Complaints 285 and the --pretty feature). The CLI runs they sit
behind are test_cli_menu_options_and_pretty."""
QUICK_TOPIC = True

from .harness import *  # noqa: F401,F403

from sim.engine import settings as _SETTINGS
from sim.engine.data import money_short
from sim.ui import cli as _CLI
from sim.ui import protocol as _protocol
from sim.ui.proto.render_typed import render_pretty


def render_in_money_word(word, command, reply):
    """The typed screen as a player of a place that counts in `word` reads it (the word is set when a game starts)."""
    _protocol.MONEY_SHORT = word
    try:
        return render_pretty(command, reply)
    finally:
        _protocol.MONEY_SHORT = "den"


LABOUR_REPLY = {
    "ok": True, "you_employ_in_total": 3, "annual_wage_bill": 1200.0, "slaves": 5, "freedmen": 2,
    "on_your_staff": [{"trade": "smith", "you_employ": 3, "a_year_of_one": 400.0}],
    "in_training": [{"trade": "carter", "people": 2, "ready_year": 104}],
}
VENTURES_REPLY = {
    "ok": True,
    "running": [{"id": "forge_works", "earns_a_year": 900.0, "costs_a_year": 400.0, "needs": {"scholars": 1, "craftsmen": 2}}],
    "you_know_how_but_have_not_opened": [{"id": "mill_works", "earns_a_year": 300.0, "costs_a_year": 100.0, "to_open_it": 800.0}],
}

# --- the money word of the place: each civilisation names its money once, and a screen uses that name ------------------
check("a civilisation's money word comes from its data: pence in England, cash in Han China",
      money_short(S.load_civ("england_1300")) == "pence" and money_short(S.load_civ("han_china_100ad")) == "cash",
      (money_short(S.load_civ("england_1300")), money_short(S.load_civ("han_china_100ad"))))
english = render_in_money_word("pence", "labour", LABOUR_REPLY)
check("a screen is counted in the place's money and never in denarii",  # presentation: the money word on the screen
      " den " not in english and "denarii" not in english and "pence" in english,
      [line for line in english.splitlines() if " den" in line or "denarii" in line][:2])

# --- the ventures screen is a table, not raw Python ---------------------------------------------------------------------
ventures = render_pretty("ventures", VENTURES_REPLY)
check("ventures renders as a table with its rows, not as raw Python",  # presentation: layout of the ventures screen
      "CONCERNS" in ventures and "forge_works" in ventures and "mill_works" in ventures
      and "{'id':" not in ventures and "{\"id\":" not in ventures,
      [line for line in ventures.splitlines() if "{'" in line][:2])

# --- the labour screen shows the whole household -----------------------------------------------------------------------
labour = render_pretty("labour", LABOUR_REPLY)
check("people you own appear in your household, as do freedmen",  # presentation: the labour screen's rows
      "people you own" in labour and "freedmen" in labour, [line for line in labour.splitlines() if "STAFF" in line][:2])
check("with nobody on staff, owned people still keep the household from reading 'nobody'",  # presentation: the labour screen's rows
      "ON YOUR STAFF:\n  nobody" not in render_pretty("labour", {**LABOUR_REPLY, "on_your_staff": [], "freedmen": 0})
      and "ON YOUR STAFF:\n  nobody" in render_pretty("labour", {**LABOUR_REPLY, "on_your_staff": [], "slaves": 0, "freedmen": 0}),
      "staff block")
check("a training row names its trade and is never printed as None",  # presentation: the labour screen's rows
      "carter x2, ready 104" in labour and "None" not in labour, labour.split("IN TRAINING")[-1][:120])

# --- the display width: `_wrap` uses the width it is given; the preference reaches both readers of it ----------------
narrow_lines = _CLI._wrap("word " * 40, width=30, indent="   ").splitlines()
wide_lines = _CLI._wrap("word " * 40, width=150, indent="   ").splitlines()
check("cli._wrap uses the width it is given (narrower wraps the same text into more lines)",
      len(narrow_lines) > len(wide_lines) >= 1, (len(narrow_lines), len(wide_lines)))
_CLI._apply_display_prefs({"display_width": 222})
carried = (_CLI._DISPLAY_WIDTH, _protocol.DISPLAY_WIDTH)
# Put the module globals back so no later check in this process renders at width 222.
_CLI._apply_display_prefs(dict(_SETTINGS.CONFIG_DEFAULTS))
check("_apply_display_prefs carries an Options override into cli._wrap's default and protocol.DISPLAY_WIDTH",
      carried == (222, 222), carried)
