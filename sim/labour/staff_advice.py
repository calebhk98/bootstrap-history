"""The remedies named when a household is short of artisans or scholars: only ones it could have heard of."""
import math


def staff_remedies(kind, sources, deficit, done, operating, is_venture, is_visible, waiting_on_kind, hire_advice):
    """[(sentence, {"action", "node"})] in the order of `sources`, [(node or HIRE/BUY, why)].

    Hiring is always sayable (the labour market is in front of the player), sized to `deficit` when one is known.
    A node already built but shut is offered back ('reopen', it costs a supervisor, not a second institution). A
    node not yet built is named only once the player can see it; when it is itself waiting on the very thing it
    would supply (`waiting_on_kind(node)`), hiring or commissioning comes first, so the advice is never a circle."""
    steps = []
    for node, why in sources:
        if node == "HIRE" and deficit:
            steps.append((hire_advice(kind, math.ceil(deficit - 1e-9)), {"action": "hire", "node": None}))
        elif node in ("BUY", "HIRE"):
            steps.append((why, {"action": node.lower(), "node": None}))
        elif node in done and node not in operating and is_venture(node):
            steps.append(("reopen %s ('open %s') - you already built this; it is only shut" % (node, node),
                          {"action": "reopen", "node": node}))
        elif node not in done and is_visible(node):
            if waiting_on_kind(node):
                steps.append(("build %s eventually (%s) - but it is itself waiting on %s, so hire or commission first"
                              % (node, why, kind), {"action": "build_after_hiring", "node": node}))
            else:
                steps.append(("build %s (%s)" % (node, why), {"action": "build", "node": node}))
    return steps
