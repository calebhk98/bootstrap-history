"""The `groups` screen: who has organised against the founder, why, and what the state does."""

from .util import _fmt_num, _wrap


def render_groups(out):
    groups = out.get("groups") or []
    lines = ["INTEREST GROUPS"]
    if not groups:
        lines.append(_wrap(out.get("note", "none"), indent="  "))
        return "\n".join(lines)
    for group in groups:
        lines.append("%s: about %s people, %s a year lost (%s of their income), pull on the state %s"
                     % (group["name"], _fmt_num(group["people"]), _fmt_num(group["income_lost_per_year"]),
                        "%d%%" % round(group["grievance_share"] * 100), "%.2f" % group["pull_on_the_state"]))
        lines.append(_wrap("because " + group["cause"], indent="  "))
        lines.append(_wrap("the state undertakes to make good %s a year" % _fmt_num(group["state_undertakes_to_make_good"]),
                           indent="  "))
        for demand in group["demands"]:
            lines.append(_wrap("the state is meeting the demand to " + demand, indent="  "))
    lines.append("")
    lines.append("left unpaid by the state and raised from taxpayers it sees: %s a year   state in deficit: %s"
                 % (_fmt_num(out.get("state_leaves_unpaid_to_raise_from_taxpayers", 0)),
                    "yes" if out.get("state_in_deficit") else "no"))
    lines.append(_wrap(out.get("note", ""), indent="  "))
    return "\n".join(lines)
