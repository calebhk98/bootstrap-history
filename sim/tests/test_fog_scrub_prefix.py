"""fog_scrub_prefix: hidden ids are replaced as whole ids, so an id that prefixes another does not corrupt it."""
from .harness import *  # noqa: F401,F403
from sim.knowledge.api import HIDDEN_ID_PLACEHOLDER, scrub_hidden_ids

QUICK_TOPIC = True

SHORT = "cap_measure_temp"
LONG = "cap_measure_temp_hi"
IDS = [SHORT, LONG]


def scrub(text, visible):
    return scrub_hidden_ids(text, IDS, lambda node_id: node_id in visible)


both = "the recipe needs cap_measure_temp and cap_measure_temp_hi"

shorter_hidden = scrub(both, {LONG})
check("shorter id hidden, longer id visible: longer id stays intact and the shorter is replaced",
      shorter_hidden == "the recipe needs %s and %s" % (HIDDEN_ID_PLACEHOLDER, LONG), shorter_hidden)

longer_hidden = scrub(both, {SHORT})
check("longer id hidden, shorter id visible: only the longer is replaced, no orphaned fragment",
      longer_hidden == "the recipe needs %s and %s" % (SHORT, HIDDEN_ID_PLACEHOLDER), longer_hidden)

both_hidden = scrub(both, set())
check("both ids hidden: both are replaced and nothing is left over",
      both_hidden == "the recipe needs %s and %s" % (HIDDEN_ID_PLACEHOLDER, HIDDEN_ID_PLACEHOLDER), both_hidden)

embedded = scrub("my_cap_measure_temp_hi_measurement", set())
check("an id embedded in a larger word is not touched", embedded == "my_cap_measure_temp_hi_measurement", embedded)

namespaced = scrub("mod:cap_measure_temp", set())
check("a namespaced id is not a match for its bare tail", namespaced == "mod:cap_measure_temp", namespaced)

check("all ids visible leaves the text alone", scrub(both, set(IDS)) == both)
