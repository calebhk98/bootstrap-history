"""The text of `why <material>`."""

from sim.ui import units_text
from .util import _fmt_num


def _names(entries):
    return ", ".join("%s [%s]" % (entry["name"], entry["id"]) for entry in entries[:6]) + (
        " and %d more" % (len(entries) - 6) if len(entries) > 6 else "")


def render_material_story(out):
    rate = units_text.rate_label("mass", "yr", "t/yr")
    lines = ["%s  [%s]" % (out["name"], out["material_story"]), ""]
    if out.get("buy_per_tonne") is not None:
        lines.append("  market: buy %s, sell back %s %s; the market offers about %s %s"
                     % (_fmt_num(out["buy_per_tonne"]), _fmt_num(out["sell_per_tonne"]),
                        units_text.per_mass_heading("per").lower(),
                        _fmt_num(out["market_available_tonnes_per_year"]), rate))
    else:
        lines.append("  no market in reach sells it")
    if out.get("demand_tonnes_per_year") is not None:
        lines.append("  your work wants about %s %s; you supply %s %s yourself"
                     % (_fmt_num(out["demand_tonnes_per_year"]), rate,
                        _fmt_num(out["your_own_tonnes_per_year"]), rate))
    if out["needed_by_running_projects"]:
        lines.append("  needed by projects you are running: " + _names(out["needed_by_running_projects"]))
    else:
        lines.append("  no project you are running needs it right now")
    if out["drawn_by_finished_work"]:
        lines.append("  drawn each year by finished work: " + _names(out["drawn_by_finished_work"]))
    if out["short"]:
        lines.append("  SHORT by about %s %s; 'capacity' shows the shortfall"
                     % (_fmt_num(out["shortfall_tonnes_per_year"]), rate)
                     + ("" if out["slowing_work"] else ", though nothing you are running is held back by it"))
    else:
        lines.append("  not short: the market and your own supply cover what is wanted")
    return "\n".join(lines)
