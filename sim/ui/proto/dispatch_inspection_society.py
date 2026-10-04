"""The risk, groups and values commands."""

from .command_registry import command
from .economy import (_agent_values)


@command("risk", group="society", aliases=("hazards", "risks"),
         summary="what history is about to do to you",
         usage=["risk", "risk json"], options={"json": "the raw reply"},
         description="The hazards in play and what blunts them.")
def _cmd_risk(sim, nodes, cmd, ended):
    knowledge_risk = sim.knowledge_risk()
    return {"ok": True, "knowledge_risk": knowledge_risk, "year": sim.year,
            "confiscation": sim.confiscation_status(),
            "interest_groups": sim.interest_groups(),
            "note": "What history is about to do to you, and what you have "
                    "built that blunts it. Every hazard here is fightable."}



@command("groups", group="society", aliases=("interest_groups", "factions"),
         summary="who the economy has organised against you",
         usage=["groups", "groups json"], options={"json": "the raw reply"},
         description="The interest groups your doing has created: people whose income you took "
                     "(producers your sales displace, employers your hiring squeezes), how many, "
                     "what they lost and to what, and what the state does about it - makes it good "
                     "from its purse, raises the rest from taxpayers it sees, or forbids the "
                     "technique.")
def _cmd_groups(sim, nodes, cmd, ended):
    report = sim.interest_groups_report()
    report["ok"] = True
    return report



@command("values", shape="bare", group="society", aliases=("beliefs", "traits", "society"),
         summary="what this society believes, as numbers",
         usage=["values"], options={},
         description="The same fields a completion's 'changes the society' line names.")
def _cmd_values(sim, nodes, cmd, ended):
    return _agent_values(sim)
