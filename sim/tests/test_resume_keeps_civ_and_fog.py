"""A save says what game it is: resuming `play --session` needs no --civ, keeps fog of war on,
and a contradicting --civ is refused rather than started over the top of the save."""

from . import cli_in_process
from .harness import *  # noqa: F401,F403


def _play(lines, extra, civ=None):
    arguments = ["play"] + (["--civ", civ] if civ else []) + list(extra)
    completed = cli_in_process.run(arguments, "".join(line + "\n" for line in lines))
    return completed.stdout + completed.stderr, completed.returncode


session_path = os.path.join(ROOT, _PLAY_DIR, "resume_keeps_civ_and_fog.json")
os.makedirs(os.path.dirname(session_path), exist_ok=True)
if os.path.exists(session_path):
    os.remove(session_path)

_play(["step 2", "quit"], ["--session", session_path, "--fog"], civ="england_1300")
resumed_text, _ = _play(["state", "quit"], ["--session", session_path])
check("a save resumes without being told again which game it is",
      "Resumed from" in resumed_text and "1302" in resumed_text, resumed_text[:400])
check("fog survives a save and reload, rather than opening the whole tree",
      "Fog of war is on" in resumed_text,
      [line for line in resumed_text.splitlines() if "og of war" in line])
refused_text, refused_code = _play(["quit"], ["--session", session_path], civ="rome_100ad")
check("a --civ that contradicts the save is refused, not started over the top",
      "that save is a" in refused_text and refused_code != 0, (refused_code, refused_text[:300]))
