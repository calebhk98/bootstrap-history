"""Complaint 64: the mine commission display setting controls whether the mines screen shows when a mine is
commissioned, when it is ready, or both (the default). The rendering and the setting are called on a built reply."""
QUICK_TOPIC = True

from .harness import *
from sim.ui.proto import render_typed as _render_typed
from sim.ui.proto.render_screens_economy import render_mines
from sim.engine.settings import resolve_commission_display

_pending_screen = {"mines_you_own": "none", "still_being_sunk": {"coal": 105}}
_expected = {"commissioned": ("commissions during 105", "ready in"),
             "ready": ("ready in 106", "commissions during"),
             "both": ("commissions during 105, ready in 106", None)}
_saved_setting = _render_typed.COMMISSION_DISPLAY
for _setting, (_wanted, _absent) in _expected.items():
    _render_typed.COMMISSION_DISPLAY = _setting
    _text = render_mines(_pending_screen)
    # presentation: the wording of a pending mine on the mines screen
    check("pending mine text for %s setting" % _setting,
          _wanted in _text and (_absent is None or _absent not in _text), _text)
_render_typed.COMMISSION_DISPLAY = _saved_setting

check("unknown commission_display value falls back to both",
      resolve_commission_display({"commission_display": "sometimes"}) == "both",
      resolve_commission_display({"commission_display": "sometimes"}))
check("a known commission_display value is kept",
      all(resolve_commission_display({"commission_display": setting}) == setting for setting in _expected), "changed")
check("no commission_display value is both", resolve_commission_display({}) == "both", resolve_commission_display({}))
