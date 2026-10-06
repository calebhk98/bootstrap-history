"""Point the settings file and the save directory at a temporary directory for the whole test run."""
import atexit
import os
import shutil
import tempfile

MARKER = "ROME_TEST_ISOLATED_HOME"


def isolate_home():
    """Set ROME_SIM_CONFIG and ROME_SAVE_DIR under one temporary directory. The run's first process creates
    it and removes it at exit; worker processes find the marker in the inherited environment and reuse it."""
    if os.environ.get(MARKER):
        return
    root = tempfile.mkdtemp(prefix="rome-sim-test-home-")
    os.environ[MARKER] = root
    os.environ["ROME_SIM_CONFIG"] = os.path.join(root, "config.json")
    os.environ["ROME_SAVE_DIR"] = os.path.join(root, "saves")
    atexit.register(shutil.rmtree, root, ignore_errors=True)
