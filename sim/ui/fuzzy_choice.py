"""The fuzzy-estimates option as the command line and the options screen decide it."""

TURN_ON_PROMPT = "   Turn fuzzy estimates on now? [y/N] "
EXPLANATION = ("From now on the needs of unfinished work are shown as estimates that tighten as you start and finish it. "
               "This cannot be turned off again in this game.")


def fuzzy_estimates_wanted(flag, resuming_a_save, settings_default):
    """Whether a game starts with fuzzy estimates: the flag or menu choice when one was given, else the settings
    default for a fresh game only, so resuming never switches it on unasked."""
    if flag is not None:
        return bool(flag)
    return (not resuming_a_save) and bool(settings_default)


def turn_fuzzy_estimates_on(sim, ask, say, explain):
    """The options screen's one-way switch: explain it, ask, and turn the option on when the answer is y.
    Returns whether it was turned on. `ask(prompt, options, default)` answers an option or None; `explain(text)` prints the
    explanation and `say(text)` the outcome."""
    explain(EXPLANATION)
    if ask(TURN_ON_PROMPT, ["y", "n"], "n") == "y":
        sim.fuzzy_estimates = True
        say("   -- done. Fuzzy estimates are on.")
        return True
    say("   -- unchanged.")
    return False
