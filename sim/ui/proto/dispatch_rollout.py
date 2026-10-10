"""The rollout command: repeat a school, library or clinic across the land until a share of the people is served."""

from .command_registry import command


@command("rollout", group="projects",
         summary="repeat a work until a share of the people is covered",
         usage=["rollout", "rollout <id> <share>"],
         options={"<id>": "a work that declares coverage (a school, a clinic network)",
                  "<share>": "the share of the people to serve: 0.5 or 50 (percent)"},
         description="With no id, lists the works you can roll out: units open, the share of the people they "
                     "serve, and the units that would serve everyone. With an id and a share, opens or expands "
                     "the work by the units that reach that share, at the ordinary cost, staff and ceiling of "
                     "expanding a venture; it stops where the nation can fill no more.")
def _cmd_rollout(sim, nodes, cmd, ended):
    if ended:
        return {"ok": False, "error": "the run has ended (%s); nothing more can be built" % ended}
    node_id = cmd.get("id")
    if not node_id:
        rows = [sim.coverage_row(work) for work in sim.coverage_nodes() if work in sim.done]
        return {"ok": True, "rollouts": rows,
                "note": "" if rows else "you know no work that can be rolled out yet"}
    share = cmd.get("share")
    if share is None:
        return {"ok": False, "error": "name the share of the people to serve, e.g. 'rollout %s 50'" % node_id}
    share = float(share)
    share = share / 100.0 if share > 1.0 else share
    if not 0.0 < share <= 1.0:
        return {"ok": False, "error": "the share must be between 0 and 1 (or 1 and 100 percent)"}
    ok, text = sim.roll_out(node_id, share)
    if not ok:
        return {"ok": False, "error": text}
    return {"ok": True, "message": text, "covered": round(sim.coverage_share(node_id), 4),
            "units": round(sim.institution_units(node_id), 3)}
