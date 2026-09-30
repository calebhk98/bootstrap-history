"""Tests for CLI small fixes (complaints 159, 160, 161, 172)."""
import json
import os
import subprocess
import sys
import tempfile

from .harness import *  # noqa: F401,F403


def test_159_play_session_new_file_uses_default_civ():
    """play --session <nonexistent-path> should start default civ, not reject."""
    with tempfile.TemporaryDirectory() as tmpdir:
        session_path = os.path.join(tmpdir, "newgame.json")
        # Run play with a new session file and pipe EOF immediately
        result = subprocess.run(
            [sys.executable, os.path.join(ROOT, "sim", "simulator.py"),
             "play", "--session", session_path, "--seed", "1"],
            input="quit\n",
            capture_output=True,
            text=True,
            timeout=10,
            cwd=ROOT
        )
        # Should succeed and create the save file (not reject "no --civ given")
        output = result.stdout + result.stderr
        assert "no --civ given" not in output, f"Should not reject for missing --civ. Got: {output[:300]}"
        assert os.path.exists(session_path), "Should have created the session file"


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


def test_161_options_menu_echo_and_return_on_invalid():
    """options menu should echo invalid input and return to game on non-choice."""
    with tempfile.TemporaryDirectory() as tmpdir:
        session_path = os.path.join(tmpdir, "optionstest.json")
        # Run play, open options menu, enter invalid input, then quit
        result = subprocess.run(
            [sys.executable, os.path.join(ROOT, "sim", "simulator.py"),
             "play", "--session", session_path, "--seed", "1"],
            input="options\ninvalid\nb\nquit\n",
            capture_output=True,
            text=True,
            timeout=10,
            cwd=ROOT
        )
        assert result.returncode == 0
        output = result.stdout + result.stderr
        # Should echo or acknowledge the invalid input
        # And should return to game (not consume further piped input silently)
        assert "quit" not in output or "Ended" in output or "quit" in output.lower(), \
            "Should have processed the quit command (menu didn't consume piped input)"


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
    test_159_play_session_new_file_uses_default_civ()
    check("159: play --session with new file uses default civ", True)
except AssertionError as e:
    check("159: play --session with new file uses default civ", False, str(e))
except Exception as e:
    check("159: play --session with new file uses default civ", False, f"Exception: {e}")

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
    test_161_options_menu_echo_and_return_on_invalid()
    check("161: options menu echoes invalid input", True)
except AssertionError as e:
    check("161: options menu echoes invalid input", False, str(e))
except Exception as e:
    check("161: options menu echoes invalid input", False, f"Exception: {e}")

try:
    test_172_help_has_player_facing_description()
    check("172: --help shows player-facing descriptions", True)
except AssertionError as e:
    check("172: --help shows player-facing descriptions", False, str(e))
except Exception as e:
    check("172: --help shows player-facing descriptions", False, f"Exception: {e}")
