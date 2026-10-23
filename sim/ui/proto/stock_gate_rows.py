"""The living-stock rows `why` shows for a node: held beside needed, with the node that brings the stock named only if the
player may see that node (a node's name must not leak the hidden tree)."""


def rows_for_player(gates, visible_to_player):
    """`gates` as `why` lists them: a gate brought by a node the player cannot see names no node; a gate brought by nothing, and
    one brought by a visible node, are unchanged. `visible_to_player(node_id)` says whether the player may see a node."""
    return [dict(gate, brought_by=gate["brought_by"] if visible_to_player(gate["brought_by"]) else None)
            if gate["brought_by"] else gate for gate in gates]
