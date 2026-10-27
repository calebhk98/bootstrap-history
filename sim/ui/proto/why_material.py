"""`why <material>`: what a material is to you right now, in the same figures `market`, `capacity` and the
shortage line already use."""

import sim.engine.ui_port as ui_port
from sim.engine.ui_port import material_words
from sim.ui.market_report import priceable_materials

from .economy import _material_capacity_rows


def _drawing_nodes(sim, material):
    """(running projects, finished things) whose listed materials include `material`, as [{"id", "name"}]."""
    def entries(node_ids):
        return [{"id": node_id, "name": sim.view("tree_nodes")()[node_id]["name"]} for node_id in sorted(node_ids)
                if material in (sim.view("tree_nodes")()[node_id].get("mat") or {})]
    finished = [node_id for node_id in sim.view("techniques_held")() if sim.view("tree_nodes")()[node_id].get("up", 0) > 0]
    return entries(sim.view("active_projects")()), entries(finished)


def material_story(sim, material):
    """The reply for `why <material>`, or None when `material` is not one this game knows."""
    working, standing = _drawing_nodes(sim, material)
    priced = material in priceable_materials(sim)
    if not (priced or working or standing):
        return None
    reply = {"ok": True, "material_story": material, "name": material_words(material),
             "needed_by_running_projects": working, "drawn_by_finished_work": standing}
    quote = sim.view("goods_quote")[material] if priced else None
    if quote is not None:
        reply["buy_per_tonne"] = round(quote["buy_per_tonne"], 2)
        reply["sell_per_tonne"] = round(quote["sell_per_tonne"], 2)
        reply["market_available_tonnes_per_year"] = round(quote["market_available_tonnes_per_year"], 2)
    supply_key = ui_port.material_tag(sim, material)[0]
    row = next((row for row in _material_capacity_rows(sim) if row["material"] == supply_key), None)
    if row is not None:
        reply.update(demand_tonnes_per_year=row["demand_t_per_yr"],
                     your_own_tonnes_per_year=row["your_own_capacity_t_per_yr"],
                     shortfall_tonnes_per_year=row["shortfall_t_per_yr"])
    reply["short"] = bool(row and row["shortfall_t_per_yr"] > 0)
    reply["slowing_work"] = bool(reply["short"] and working)
    return reply
