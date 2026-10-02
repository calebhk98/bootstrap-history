"""Complaint 181: a command that changes nothing (a refusal, a bare `state`)
must not pay for rewriting the whole save, and writing a save must not go
through the slow pure-Python JSON encoder. Counted work, not clock time."""
from .harness import *  # noqa: F401,F403
import json.encoder as _json_encoder
import sim.engine.proto.saveload as _saveload
from sim.engine.proto.saveload import save_state, load_state
from sim.engine.cli_interactive import _play_run_one_command


def _running_venture_sim():
    test_sim = sim(capital=1e9)
    venture_id = next(node_id for node_id in ORDER if test_sim.is_venture(node_id))
    run_it(test_sim, venture_id)
    return test_sim, venture_id


def _fresh_session():
    test_sim, venture_id = _running_venture_sim()
    path = os.path.join(tempfile.mkdtemp(), "session.json")
    save_state(test_sim, path)
    reloaded = sim(capital=1.0)
    load_state(reloaded, path)
    return reloaded, venture_id, path


class _CountWrites:
    """Counts how many times a save replaced the file, and how many times the
    pure-Python JSON encoder (the slow path) was built."""

    def __enter__(self):
        self.replaces = 0
        self.python_encoder_builds = 0
        self._real_replace = os.replace
        self._real_make_iterencode = _json_encoder._make_iterencode

        def counting_replace(source, destination):
            self.replaces += 1
            return self._real_replace(source, destination)

        def counting_make_iterencode(*args, **kwargs):
            self.python_encoder_builds += 1
            return self._real_make_iterencode(*args, **kwargs)

        os.replace = counting_replace
        _json_encoder._make_iterencode = counting_make_iterencode
        return self

    def __exit__(self, *exc):
        os.replace = self._real_replace
        _json_encoder._make_iterencode = self._real_make_iterencode


def _run(test_sim, command, path):
    import io, contextlib
    with contextlib.redirect_stdout(io.StringIO()):
        _play_run_one_command(test_sim, NODES, command, path)


# --- a refusal that changes nothing does not rewrite the save ---------------
refusal_sim, running_id, refusal_path = _fresh_session()
refusal_sim.end_year = refusal_sim.cfg["start_year"] + 500
_run(refusal_sim, {"cmd": "state"}, refusal_path)   # the first look sets a one-time flag
with _CountWrites() as counted:
    _run(refusal_sim, {"cmd": "open", "id": running_id}, refusal_path)
    _run(refusal_sim, {"cmd": "open", "id": "no_such_node_anywhere"}, refusal_path)
    _run(refusal_sim, {"cmd": "state"}, refusal_path)
check("refusals and a bare state rewrite the save zero times", counted.replaces == 0,
      counted.replaces)

# --- a command that does change the game still saves it ---------------------
with _CountWrites() as counted:
    _run(refusal_sim, {"cmd": "step", "years": 1}, refusal_path)
check("a step rewrites the save", counted.replaces == 1, counted.replaces)
stepped_year = refusal_sim.state.scenario.year
check_sim = sim(capital=1.0)
load_state(check_sim, refusal_path)
check("...and what it wrote is the stepped game", check_sim.state.scenario.year == stepped_year,
      (check_sim.state.scenario.year, stepped_year))

# --- the write path uses the C encoder --------------------------------------
with _CountWrites() as counted:
    save_state(refusal_sim, os.path.join(tempfile.mkdtemp(), "other.json"))
check("a save is encoded without the pure-Python JSON encoder",
      counted.python_encoder_builds == 0, counted.python_encoder_builds)

# --- a save is compact: no per-field indentation ----------------------------
with open(refusal_path) as save_handle:
    save_line_count = sum(1 for _ in save_handle)
check("a save is a handful of lines, not one line per value", save_line_count < 50,
      save_line_count)

# --- imitation scan: the society's baseline knowledge is read once per scan,
# --- not once per invention per actor ---------------------------------------
from sim.agents import SimWorld
from sim.engine.state import ActorRecord

scan_sim = sim(capital=1e9)
for scan_node in [node_id for node_id in ORDER if node_id not in scan_sim.done][:80]:
    scan_sim.state.projects.done.add(scan_node)
scan_sim._done_changed()
scan_firm = scan_sim.actors.add("firm:scan", ActorRecord(kind="firm", money=1e6))
scan_world = SimWorld(scan_sim)
baseline_reads = [0]
_real_baseline = scan_world.baseline_knowledge


def _counting_baseline():
    baseline_reads[0] += 1
    return _real_baseline()


scan_world.baseline_knowledge = _counting_baseline
scan_inventions = len(scan_world.founder_inventions())
scan_firm.imitation_options(scan_world)
check("set-up: the scan has many inventions to look at", scan_inventions >= 50, scan_inventions)
check("the baseline knowledge is read a constant number of times per scan",
      baseline_reads[0] <= 5, (baseline_reads[0], scan_inventions))
