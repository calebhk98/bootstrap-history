"""A screen registered with @renders in any render_*.py module is found by render_pretty without editing a shared table."""

QUICK_TOPIC = True

from sim.ui.proto import render_registry, render_typed

from .harness import check


@render_registry.renders("ui_registry_probe")
def _probe(reply):
    return "PROBE %s" % reply.get("value")


render_typed._RENDERERS.update(render_registry.RENDERERS)
check("a self-registered renderer draws its screen",
      render_typed.render_pretty("ui_registry_probe", {"ok": True, "value": 7}).startswith("PROBE 7"))
check("every hand-listed screen is still in the table",
      all(name in render_typed._RENDERERS for name in ("state", "step", "why", "figures", "portfolio")))
