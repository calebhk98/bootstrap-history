"""Tests for CLI small fixes (complaints 159, 160, 161, 172)."""
import json
import os
import subprocess
import sys
import tempfile

from .harness import *  # noqa: F401,F403


def test_159_new_session_needs_civ_and_readme_says_so():
    """A --session path that does not exist still needs --civ (a typo must not
    start a new game), and the README's new-game example names the civ."""
    with tempfile.TemporaryDirectory() as tmpdir:
        session_path = os.path.join(tmpdir, "newgame.json")
        result = subprocess.run(
            [sys.executable, os.path.join(ROOT, "sim", "simulator.py"),
             "play", "--session", session_path, "--seed", "1"],
            input="quit\n", capture_output=True, text=True, timeout=60, cwd=ROOT)
        output = result.stdout + result.stderr
        assert "--civ" in output, "the refusal should name --civ. Got: %s" % output[:300]
        assert not os.path.exists(session_path), "no save should be written for a typo'd path"
    with open(os.path.join(ROOT, "README.md")) as handle:
        readme = handle.read()
    assert "play --civ rome_100ad --session mygame.json" in readme, \
        "the README's first --session example should start a new game with --civ"


def test_160_goals_marks_actual_default():
    """goals output should mark the actual default goal, not just tree's meta."""
    result = subprocess.run(
        [sys.executable, os.path.join(ROOT, "sim", "simulator.py"), "goals"],
        capture_output=True,
        text=True,
        timeout=10,
        cwd=ROOT
    )
    assert result.returncode == 0
    lines = result.stdout.split("\n")
    # Find lines that mark a default
    default_marked = [line for line in lines if "<- DEFAULT" in line or "(default)" in line]
    assert len(default_marked) > 0, "Should mark which goal is the default"
    # The default should be point_contact_transistor, not junction_transistor
    default_lines = [line for line in default_marked if "point_contact" in line.lower()]
    assert len(default_lines) > 0, "point_contact_transistor should be marked as default"


def test_161_options_not_alias_of_available():
    """help commands should not list 'options' as an alias of 'available'."""
    result = subprocess.run(
        [sys.executable, os.path.join(ROOT, "sim", "simulator.py"),
         "play", "--seed", "1"],
        input="help commands\nquit\n",
        capture_output=True,
        text=True,
        timeout=10,
        cwd=ROOT
    )
    assert result.returncode == 0
    # Check that 'options' is not listed as an alias of 'available'
    # The output should show available and its aliases separately from options menu
    lines = result.stdout + result.stderr
    assert "options: available" not in lines, "options should not be listed as alias of available"


def test_172_help_has_player_facing_description():
    """--help should show player-facing descriptions, not developer module docstring."""
    result = subprocess.run(
        [sys.executable, os.path.join(ROOT, "sim", "simulator.py"), "--help"],
        capture_output=True,
        text=True,
        timeout=10,
        cwd=ROOT
    )
    assert result.returncode == 0
    output = result.stdout
    # Should NOT contain developer documentation terms
    assert "cli.py" not in output, "Should not show module references"
    assert "_wilson_interval" not in output, "Should not show internal function names"
    assert "cmd_sweep" not in output, "Should not show internal command details"
    # SHOULD contain player-facing command descriptions like "play", "goals", etc
    assert "play" in output.lower(), "Should mention play command"
    assert "goals" in output.lower(), "Should mention goals command"


# Run the tests
try:
    test_159_new_session_needs_civ_and_readme_says_so()
    check("159: a new --session needs --civ, and the README says so", True)
except AssertionError as e:
    check("159: a new --session needs --civ, and the README says so", False, str(e))
except Exception as e:
    check("159: a new --session needs --civ, and the README says so", False, f"Exception: {e}")

try:
    test_160_goals_marks_actual_default()
    check("160: goals marks actual default goal", True)
except AssertionError as e:
    check("160: goals marks actual default goal", False, str(e))
except Exception as e:
    check("160: goals marks actual default goal", False, f"Exception: {e}")

try:
    test_161_options_not_alias_of_available()
    check("161: options not alias of available", True)
except AssertionError as e:
    check("161: options not alias of available", False, str(e))
except Exception as e:
    check("161: options not alias of available", False, f"Exception: {e}")

try:
    test_172_help_has_player_facing_description()
    check("172: --help shows player-facing descriptions", True)
except AssertionError as e:
    check("172: --help shows player-facing descriptions", False, str(e))
except Exception as e:
    check("172: --help shows player-facing descriptions", False, f"Exception: {e}")
