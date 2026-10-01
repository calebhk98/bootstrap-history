"""Regression tests for remaining small text defects in complaints 198 and 236.

Complaint 198: Imperial edict node has Rome-specific flavour text
Complaint 236 item 8: "people kept on your own staff" text appears with no context
Complaint 236 item 10: Train reply misleading about when work can start
"""
from .harness import *

_SIMULATOR = os.path.join(HERE, "simulator.py")
_scratch = tempfile.mkdtemp()


def _env(name, config=None):
    saves = os.path.join(_scratch, name)
    os.makedirs(saves, exist_ok=True)
    config_file = os.path.join(_scratch, name + "-config.json")
    if config is not None:
        with open(config_file, "w") as handle:
            json.dump(config, handle)
    env = dict(os.environ, ROME_SAVE_DIR=saves, ROME_SIM_CONFIG=config_file)
    env.pop("ROME_DEFAULT_SEED", None)
    return saves, env


def _run(arguments, text, env, cwd=None):
    return subprocess.run([sys.executable, _SIMULATOR] + arguments, input=text,
                          capture_output=True, text=True, timeout=120, env=env, cwd=cwd)


# ---- Complaint 198: "Imperial edict" is Rome-specific
_saves_198, _env_198 = _env("198-imperial-edict")
_why_198 = _run(["play", "--civ", "rome_100ad", "--kit", "poor_scholar",
                 "--fog", "--seed", "1", "--session",
                 os.path.join(_saves_198, "test.json")],
                "why med_legal_physician\nquit\n", _env_198).stdout
check("198: why med_legal_physician does not contain 'Imperial edict' (Rome-specific wording)",
      "Imperial edict" not in _why_198, _why_198)

# ---- Complaint 236 item 8: "people kept on your own staff" text
_saves_236_8, _env_236_8 = _env("236-staff-text")
_why_236_8 = _run(["play", "--civ", "han_china_100ad", "--kit", "poor_scholar",
                   "--fog", "--seed", "1", "--session",
                   os.path.join(_saves_236_8, "test.json")],
                  "why writing_press\nquit\n", _env_236_8).stdout
check("236-8: why output should not include 'people kept on your own staff' without context",
      "people kept on your own staff" not in _why_236_8 or "art" in _why_236_8.lower(),
      _why_236_8)

# ---- Complaint 236 item 10: Train reply is misleading
_saves_236_10, _env_236_10 = _env("236-train-text")
_train_out = _run(["play", "--civ", "han_china_100ad", "--kit", "poor_scholar",
                   "--fog", "--seed", "1", "--session",
                   os.path.join(_saves_236_10, "test.json")],
                  "train chemist 2\nquit\n", _env_236_10).stdout
check("236-10: train reply does not say 'nobody can do that work yet'",
      "nobody can do that work yet" not in _train_out, _train_out)
