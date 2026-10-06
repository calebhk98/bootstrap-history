"""Complaint 460 (home config): the suite points the settings file and the save directory at a per-run
temporary directory, so no test can write the developer's real home."""

QUICK_TOPIC = True

from .harness import *  # noqa: F401,F403
from sim.engine import settings

home = os.path.expanduser("~")
config_file = settings.config_path()
save_directory = os.environ.get(settings.SAVE_DIR_ENV, "")
check("the settings file is not under the real home", not os.path.abspath(config_file).startswith(home + os.sep)
      or os.path.abspath(config_file).startswith(tempfile.gettempdir()), config_file)
check("the settings file is in the run's temporary directory",
      os.path.abspath(config_file).startswith(os.path.abspath(tempfile.gettempdir()) + os.sep), config_file)
check("the save directory is in the run's temporary directory",
      os.path.abspath(save_directory).startswith(os.path.abspath(tempfile.gettempdir()) + os.sep), save_directory)
check("a worker process shares its parent's directory",
      os.environ.get("ROME_TEST_ISOLATED_HOME") == os.path.dirname(config_file))
