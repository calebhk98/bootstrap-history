"""fog_scrub_prefix: substring replace corrupts ids with shared prefixes."""
from .harness import *  # noqa: F401,F403

# =============================================================================
# FOG SCRUB PREFIX BUG: fog_scrub() uses plain substring replace, so a hidden
# id that is a prefix of another id corrupts the longer id. The tree contains
# at least 17 such pairs (cap_measure_temp/cap_measure_temp_hi being one).
# If cap_measure_temp is hidden and text contains "cap_measure_temp_hi", the
# replace consumes "cap_measure_temp" and leaves "something you have not heard
# of_hi", exposing the suffix "_hi". This test covers three cases: a shorter
# id hidden, a longer id hidden, and both hidden. The fix matches whole ids
# only (word boundaries: [A-Za-z0-9_]) and replaces longest ids first.
# =============================================================================

# --- Case 1: Only the shorter id (cap_measure_temp) is hidden.
# The longer id (cap_measure_temp_hi) is visible. The text contains both.
# After fog_scrub, the visible one should remain, and the hidden one should
# be replaced. Most importantly: no corrupted suffix like "_hi".
_test_sim = sim(capital=1000.0)
_test_sim.fog = True
_test_sim.revealed = {"cap_measure_temp_hi"}  # longer one visible, shorter one hidden
_text_both = "the recipe needs cap_measure_temp and cap_measure_temp_hi"
_result_case1 = _test_sim.fog_scrub(_text_both)
check("shorter id hidden, longer id visible: longer id stays intact",
      "cap_measure_temp_hi" in _result_case1,
      _result_case1)
check("shorter id hidden, longer id visible: shorter id replaced",
      "something you have not heard of" in _result_case1,
      _result_case1)

# --- Case 2: Only the longer id (cap_measure_temp_hi) is hidden.
# The shorter id (cap_measure_temp) is visible. The text contains both.
_test_sim2 = sim(capital=1000.0)
_test_sim2.fog = True
_test_sim2.revealed = {"cap_measure_temp"}  # shorter one visible
_text_both = "the recipe needs cap_measure_temp and cap_measure_temp_hi"
_result_case2 = _test_sim2.fog_scrub(_text_both)
check("longer id hidden, shorter id visible: shorter id remains",
      "cap_measure_temp" in _result_case2,
      _result_case2)
check("longer id hidden, shorter id visible: longer id replaced",
      "cap_measure_temp_hi" not in _result_case2,
      _result_case2)
check("longer id hidden, shorter id visible: no orphaned fragment",
      "_hi" not in _result_case2,
      _result_case2)

# --- Case 3: Both ids are hidden.
# The text contains both. After fog_scrub, neither should appear.
_test_sim3 = sim(capital=1000.0)
_test_sim3.fog = True
_test_sim3.revealed = set()  # both hidden
_text_both = "the recipe needs cap_measure_temp and cap_measure_temp_hi"
_result_case3 = _test_sim3.fog_scrub(_text_both)
check("both ids hidden: shorter id is replaced",
      "cap_measure_temp" not in _result_case3,
      _result_case3)
check("both ids hidden: longer id is replaced",
      "cap_measure_temp_hi" not in _result_case3,
      _result_case3)
check("both ids hidden: no orphaned fragment",
      "_hi" not in _result_case3,
      _result_case3)

# --- Case 4: Id at word boundary - should only match whole ids.
# If scrub matches within a larger word, it could leave corruption.
_test_sim4 = sim(capital=1000.0)
_test_sim4.fog = True
_test_sim4.revealed = set()  # both hidden
_text_embedded = "my_cap_measure_temp_hi_measurement"
_result_case4 = _test_sim4.fog_scrub(_text_embedded)
check("ids embedded in larger word are preserved (no corruption)",
      "my_cap_measure_temp_hi_measurement" in _result_case4 or "_hi" not in _result_case4,
      _result_case4)
