"""The score through a running game: the `score` command answers with its components, and the institutions
component and total do not move with the string hash seed (it sums floats over a frozenset). The scoring rules are
in test_score_and_ending."""
from .harness import *  # noqa: F401,F403


def _score_snapshot(seed_env):
    proc = subprocess.run(
        [sys.executable, "-c",
         "import sys; import random; from sim import simulator as S; "
         "from sim.ui.protocol import score_report as SC; "
         "T,P,N,W,G = S.load(); _l,O,_b = S.load_strategy('recommended', N, T['meta']['goal_node']); "
         "s = S.Sim(N, O, random.Random(1), events=False, manual=False, "
         "civ=S.load_civ('rome_100ad'), cfg={'start_capital':5000000.0}); "
         "s.goal, s.done_year = T['meta']['goal_node'], {}; "
         "s.goal_year = s.year + 1; "
         "[s.done.add(k) for k in sorted(s.CAPABILITY_INSTITUTIONS)]; "
         "[s.operating.add(k) for k in sorted(s.CAPABILITY_INSTITUTIONS)]; "
         "s.inst_units = {k: 2.0 for k in s.SCALABLE_INSTITUTIONS}; "
         "s._done_changed(); "
         "r = SC(s, N); "
         "print(repr((round(r['components']['institutions']['normalized'], 12), "
         "r['total'])))"],
        capture_output=True, text=True, timeout=60, cwd=ROOT,
        env=dict(os.environ, PYTHONHASHSEED=seed_env))
    return proc.stdout.strip()


_score_game = sim(capital=5_000_000.0)
_reply = S._agent_dispatch(_score_game, NODES, {"cmd": "score"})
check("`score` answers through the command dispatcher with its components",
      _reply.get("ok") and set(_reply["components"]) >= {"technology_coverage", "literacy", "standing"}, _reply)

_seed_a, _seed_b = _par_map(_score_snapshot, ("0", "98765"))
check("the institutions component, and the total it feeds, are identical under a different PYTHONHASHSEED",
      _seed_a == _seed_b and _seed_a, (_seed_a, _seed_b))
