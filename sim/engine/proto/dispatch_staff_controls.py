"""The keep and reserve commands: hold named concerns staffed, and a reserve of spare hands."""

from .command_registry import command


def _keep_listing(sim):
    return sorted(sim.state.projects.keep_staffed)


@command("keep", group="projects",
         summary="hire each year for the concerns you name",
         usage=["keep", "keep <id> staffed", "keep <id> off",
                '{"cmd":"keep","id":"<id>","staffed":true}'],
         options={"<id>": "a concern you know how to run",
                  "staffed / off": "hire for it each year, or stop"},
         description="A flagged concern gets first claim: each year, before the closure rule, "
                     "the game hires the craftsmen, scholars and specialist foreman it lacks, "
                     "within your cash and room. Bare keep lists them; 'ventures' shows them too.")
def _cmd_keep(sim, nodes, cmd, ended):
    node_id = cmd.get("id")
    if node_id is None:
        return {"ok": True, "keep_staffed": _keep_listing(sim)}
    projects = sim.state.projects
    if node_id not in projects.done or not sim.is_venture(node_id):
        return {"ok": False,
                "error": "you can only keep a concern you know how to run staffed; "
                         "'ventures' lists them"}
    flag = cmd.get("staffed", True)
    if isinstance(flag, str):
        flag = flag.strip().lower() not in ("off", "false", "no", "0")
    if flag:
        projects.keep_staffed.add(node_id)
    else:
        projects.keep_staffed.discard(node_id)
    return {"ok": True, "keep_staffed": _keep_listing(sim),
            "note": ("%s will be hired for each year before the closure rule" % node_id
                     if flag else "%s is no longer kept staffed" % node_id)}
