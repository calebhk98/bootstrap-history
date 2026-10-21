"""The dice a typed game rolls: the saved settings and the command-line flag decide them."""
import random

from sim.engine.ui_port import DetRNG


def dice_for_play(app_cfg, deterministic_flag, seed):
    """(random source, whether events fire) for a typed game: deterministic when the flag or the saved
    `default_deterministic` says so; events on unless the saved `default_events` is off."""
    deterministic = bool(deterministic_flag) or bool(app_cfg.get("default_deterministic", False))
    return (DetRNG(seed) if deterministic else random.Random(seed)), bool(app_cfg.get("default_events", True))
