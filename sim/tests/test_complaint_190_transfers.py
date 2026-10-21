"""Complaint 190: a one-off transfer to the state is declared by works as data (`transfer`, knowledge with no upkeep), the
typed `pay` lines read, and two concerns declare the state's share of their takings. The payments, the `pay` command and
the levy on a game are the scenario in test_complaint_190_transfers_scenario."""
from .harness import *  # noqa: F401,F403

for node_id, base in (("ben_state_debt_redemption", "debt"), ("ben_political_settlement", "claims"),
                      ("ben_disaster_relief_grant", None)):
    check("%s declares a transfer" % node_id, "transfer" in (NODES[node_id].get("mechanics") or {}), node_id)
    check("%s is knowledge once done, not a going concern with upkeep" % node_id, NODES[node_id]["up"] == 0, NODES[node_id]["up"])

from sim.ui.proto.typed import parse_typed

check("the typed line `pay state debt` reads", parse_typed("pay state debt")[0] == {"cmd": "pay", "what": "debt"}, parse_typed("pay state debt"))
check("the typed line `pay state 500` reads", parse_typed("pay state 500")[0] == {"cmd": "pay", "amount": 500.0}, parse_typed("pay state 500"))
check("the typed line `pay state claims` reads", parse_typed("pay claims")[0] == {"cmd": "pay", "what": "claims"}, parse_typed("pay claims"))

for node_id in ("fin_gambling_house", "fin_lottery"):
    levy = (NODES[node_id].get("mechanics") or {}).get("state_levy")
    check("%s pays the state a share of its takings" % node_id, bool(levy) and 0.0 < levy["share"] < 1.0, levy)
check("a state lottery gives the state a larger share than a private gambling house",
      NODES["fin_lottery"]["mechanics"]["state_levy"]["share"] > NODES["fin_gambling_house"]["mechanics"]["state_levy"]["share"])
