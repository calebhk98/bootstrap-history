"""The BENEFIT block of `why`: what a node gives for good, what only while it
runs, what running it costs and what shutting it loses, read from the node's
mechanics and the engine's own lost-benefit table."""
from sim.engine.permanent_benefit import permanent_parts


def benefit_block(sim, node_id):
    """{permanent, while_open, cost_of_opening, if_shut} or None when the node
    declares nothing to say."""
    node = sim.nodes[node_id]
    capability = (node.get("mechanics") or {}).get("capability") or {}
    lost_benefit = capability.get("lost_benefit")
    permanent = permanent_parts(node, sim._tech_effects.get(node_id) or {})
    is_venture = sim.is_venture(node_id)
    if not permanent and not lost_benefit:
        return None
    block = {"permanent": ("; ".join(permanent) + ", kept even when no concern is open"
                           if permanent else "nothing: the benefit needs it open")}
    if is_venture:
        scholars, craftsmen = sim.venture_hands(node_id)
        upkeep = sim.venture_real_upkeep(node_id, 1.0)
        block["while_open"] = lost_benefit or "only what its revenue brings"
        block["cost_of_opening"] = (
            "%s a year upkeep, with %.1f scholars and %.1f craftsmen to supervise"
            % ("{:,.0f}".format(upkeep), scholars, craftsmen))
        block["if_shut"] = ("upkeep stops and so does: %s%s"
                            % (lost_benefit or "its revenue",
                               "; still kept: " + "; ".join(permanent) if permanent else ""))
    else:
        block["while_open"] = "nothing: it is knowledge, not a concern you open"
        block["cost_of_opening"] = "none"
        block["if_shut"] = "not applicable"
    return block
