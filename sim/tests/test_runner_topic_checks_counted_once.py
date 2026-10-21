"""A topic module imported as another topic's helper runs none of its checks there: they run once, in its own
topic, whatever else ran before it in the process."""

QUICK_TOPIC = True

import importlib.abc
import importlib.util
import sys

from sim.tests import harness, topic_import_guard

OWNER = "sim.tests.test_guard_probe_owner"
HELPER = "sim.tests.test_guard_probe_helper"

SOURCES = {
    HELPER: "from sim.tests.harness import check\ncheck('helper own check', True)\nVALUE = 3\n",
    OWNER: "from sim.tests.harness import check\nfrom sim.tests.test_guard_probe_helper import VALUE\n"
           "check('owner check', VALUE == 3)\n",
}


class _ProbeSource(importlib.abc.MetaPathFinder, importlib.abc.Loader):
    def find_spec(self, name, path, target=None):
        return importlib.util.spec_from_loader(name, self) if name in SOURCES else None

    def create_module(self, spec):
        return None

    def exec_module(self, module):
        exec(SOURCES[module.__name__], module.__dict__)


def checks_recorded_importing(own_name):
    """Names of the checks recorded while own_name is imported as a topic; the probe's own records are dropped."""
    probe = _ProbeSource()
    sys.meta_path.append(probe)
    before = len(harness.CHECKS_RUN)
    failures_before = len(harness.FAILURES)
    try:
        with topic_import_guard.own_checks_only(own_name):
            __import__(own_name)
        return [name for name, _ in harness.CHECKS_RUN[before:]]
    finally:
        sys.meta_path.remove(probe)
        del harness.CHECKS_RUN[before:]
        del harness.FAILURES[failures_before:]


owner_checks = checks_recorded_importing(OWNER)
helper_checks = checks_recorded_importing(HELPER)     # imported before as the owner's helper, silently
for name in (OWNER, HELPER):
    sys.modules.pop(name, None)

harness.check("a helper topic's checks do not run under the topic that imports it",
              owner_checks == ["owner check"], owner_checks)
harness.check("a topic imported earlier as a helper still runs its own checks",
              helper_checks == ["helper own check"], helper_checks)
