"""`figures`: why a headline number changed (Complaints/95). The figures register
themselves in sim/ui/figures_headline.py; this only reads the registry."""

import sim.engine.ui_port as ui_port
from sim.ui import figures_headline, figures_world  # noqa: F401  (register the figures)
from sim.ui.figures import FIGURES, explain_figure
from .command_registry import command


def figure_listing():
    return {"ok": True,
            "figures": [{"name": entry["name"], "label": entry["label"], "unit": entry["unit"]}
                        for entry in FIGURES.values()],
            "note": "'figures <name>' shows last year's value, this year's and what moved it."}


def figure_reply(sim, name):
    """The explanation of one figure, or the refusal naming the ones that exist."""
    if name not in FIGURES:
        return {"ok": False,
                "error": "no figure called %r. Figures: %s" % (name, ", ".join(sorted(FIGURES)))}
    return explain_figure(sim, name, ui_port.dashboard_history(sim))


@command("figures", group="overview", aliases=("whychanged", "numbers"),
         summary="why a headline number changed",
         usage=["figures", "figures <name>", "why <name>"],
         options={"<name>": "a figure name; plain 'figures' lists every one"},
         description="Last year's value, this year's and the named causes with their "
                     "contributions, read from the functions that compute each figure. "
                     "What the named causes leave out is shown as its own line.")
def _cmd_figures(sim, nodes, cmd, ended):
    name = cmd.get("id")
    return figure_listing() if not name else figure_reply(sim, name)
