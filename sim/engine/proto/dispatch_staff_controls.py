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


@command("reserve", group="labour",
         summary="how many spare craftsmen and scholars the reserve_staff policy keeps",
         usage=["reserve", "reserve craftsmen 5", "reserve scholars 1",
                '{"cmd":"reserve","craftsmen":5,"scholars":1}'],
         options={"craftsmen / scholars": "spare hands above what open concerns hold"},
         description="Sets the size of the reserve; 'policy reserve_staff on' makes the game "
                     "hire (and buy housing for) them each year. Bare reserve shows it.")
def _cmd_reserve(sim, nodes, cmd, ended):
    household = sim.state.household
    for key in ("craftsmen", "scholars"):
        if cmd.get(key) is None:
            continue
        value = cmd[key]
        if (isinstance(value, bool) or not isinstance(value, (int, float))
                or value < 0 or abs(value - round(value)) > 1e-6):
            return {"ok": False, "error": "%s must be a whole number, zero or more" % key}
        setattr(household, "reserve_" + key, int(round(value)))
    return {"ok": True,
            "reserve": {"craftsmen": household.reserve_craftsmen,
                        "scholars": household.reserve_scholars},
            "policy_reserve_staff": bool(sim.policy.get("reserve_staff", False)),
            "note": "Spare hands are kept only while 'policy reserve_staff on'."}
