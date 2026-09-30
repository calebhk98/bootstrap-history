"""The `start` reply: the generic dump, with the credit forecast shortened to one line after its first showing in a year."""

from .render_screens_status import render_generic
from .util import _fmt_num

_CREDIT_BLOCKS = ("on_credit", "total_committed_across_active_work")


def _credit_summary(out):
    borrow = out.get("on_credit")
    committed = out.get("total_committed_across_active_work")
    parts = []
    if borrow:
        parts.append("would borrow %s at %s%% (about %s a year)" % (
            _fmt_num(borrow.get("you_would_borrow")), _fmt_num(borrow.get("interest_rate_percent")),
            _fmt_num(borrow.get("estimated_annual_interest"))))
    if committed:
        parts.append("%s promised across %s projects against a ceiling of %s" % (
            _fmt_num(committed.get("you_have_promised")), _fmt_num(committed.get("across_projects_in_hand")),
            _fmt_num(committed.get("your_real_ceiling_if_it_comes_to_that"))))
    return "credit: %s (the full explanation was given earlier this year)" % "; ".join(parts)


def render_start(out):
    shown_in_full = out.get("credit_forecast_in_full", True)
    kept = {key: value for key, value in out.items()
            if key != "credit_forecast_in_full" and (shown_in_full or key not in _CREDIT_BLOCKS)}
    text = render_generic(kept)
    if not shown_in_full and any(key in out for key in _CREDIT_BLOCKS):
        text += "\n" + _credit_summary(out)
    return text
