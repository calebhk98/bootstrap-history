"""Regression tests for complaint 207 (money unit anchoring) and complaint
236 item 5 (mortality wording). Tests that the money unit is explained in
the start text, and that the mortality question uses neutral wording."""
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


# ---- Complaint 207: money unit is anchored to labourer wage
_saves_207, _env_207 = _env("207-money-unit")
_out_207 = _run(["play", "--civ", "england_1300", "--kit", "poor_scholar",
                 "--fog", "--seed", "1", "--session",
                 os.path.join(_saves_207, "test.json")],
                "quit\n", _env_207).stdout
check("207: start text says the wage behind the money comes from the game's labour market",
      "labour market" in _out_207 and "price records" in _out_207, _out_207[:1500])
check("207: start text does not claim the money is detached from the civilisation's coin",
      "not to any historical coin" not in _out_207, _out_207[:1500])
_help_207 = _run(["play", "--civ", "england_1300", "--seed", "1", "--session",
                  os.path.join(_saves_207, "help.json")], "help money\nquit\n", _env_207).stdout
check("207: help money explains the unit the same way",
      "labour market" in _help_207 and "price records" in _help_207, _help_207[-2500:])
check("207: help money does not claim every price is calculated",
      "calculated from production and demand" not in _help_207, _help_207[-2500:])

# ---- Complaint 236 item 5: mortality wording is neutral, not prescriptive
_saves_236, _env_236 = _env("236-mortality-text")
_out_236 = _run(["menu"], "1\n" + "\n" * 5 + "quit\n", _env_236).stdout
check("236: mortality text does not use 'honest number' (prescriptive wording)",
      "honest number" not in _out_236,
      _out_236)
