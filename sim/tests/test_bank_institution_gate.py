"""Complaint 106: a society founds banks only once it holds a node declaring the `deposit_banking` mechanic; the
engine hands the economy the institutions the home state's society holds (a civilisation with no banking
institution yet must not get banks). Rules on built inputs; the wiring to the economy is in
test_institutions_held.py."""
QUICK_TOPIC = True
from .harness import NODES, check

from sim.markets import port_institutions
from sim.mechanics.api import nodes_declaring
from sim.economy import api as economy_api

declaring = nodes_declaring(NODES, "deposit_banking")
check("a finance node in the tree declares the deposit_banking mechanic, with a source",
      bool(declaring) and declaring[0][0].startswith("fin_") and declaring[0][1].get("source"), declaring[:1])
check("a society holding no banking mechanic is told of no institution",
      port_institutions.institutions_of(set()) == () and port_institutions.institutions_of({"other"}) == ())
check("a society holding the deposit_banking mechanic is told of the deposit banking institution",
      port_institutions.institutions_of({"deposit_banking"}) == (economy_api.DEPOSIT_BANKING,))
