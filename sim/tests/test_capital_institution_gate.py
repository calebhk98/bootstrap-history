"""Complaint 106: each capital-market institution is unlocked by a node declaring a mechanic, with a source, and the engine
hands the economy the institutions the home society holds. Read from the data, with no game."""
QUICK_TOPIC = True
from .harness import NODES, check

from sim.engine import economy_port_institutions
from sim.mechanics.api import nodes_declaring
from sim.economy import api as economy_api

MECHANICS = {"share_trading": economy_api.SHARE_TRADING, "bond_market": economy_api.BOND_MARKET,
             "insurance_underwriting": economy_api.INSURANCE_UNDERWRITING, "risk_pooling": economy_api.RISK_POOLING,
             "pooled_funds": economy_api.POOLED_FUNDS}

for mechanic, institution in MECHANICS.items():
    declaring = nodes_declaring(NODES, mechanic)
    check("a finance node declares %s, with a source" % mechanic,
          bool(declaring) and declaring[0][0].startswith("fin_") and declaring[0][1].get("source"), declaring[:1])
    check("a society holding %s is told of the %s institution" % (mechanic, institution),
          economy_port_institutions.institutions_of({mechanic}) == (institution,))
check("a society holding none of them is told of none", economy_port_institutions.institutions_of({"other"}) == ())
check("every institution name is distinct", len(set(MECHANICS.values())) == len(MECHANICS))
