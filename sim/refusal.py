"""Player text that also carries a stable code: a refusal's cause, or the kind of a log line.

Verbs such as hire and train answer `(ok, text)`, and the log is a list of `(year, text)`. The text is for
the player and its wording changes; the code (`literacy_wall`, `household_room`, `insolvency`, ...) is what a
reader tests. These classes are plain strings everywhere a string is expected, so existing callers are
unchanged; code that builds the reply or the test reads `.cause` (or `.kind`), `.facts` for the figures the
sentence states, and `.choices` when a refusal lists the answers it would have accepted. Any string
operation (`+`, `%`, slicing) returns an ordinary string, so wrap the final text last. The code does not
survive a save: a log line read back from a save is plain text.
"""


class Refusal(str):
    """Refusal text with a `cause` code, optional `choices` and the `facts` it states."""

    def __new__(cls, cause, text, choices=None, **facts):
        instance = super().__new__(cls, text)
        instance.cause = cause
        instance.choices = list(choices) if choices is not None else None
        instance.facts = facts
        return instance

    def __reduce_ex__(self, protocol):
        return (_rebuild, (type(self), self.cause, str(self), self.choices, self.facts))


class LogLine(Refusal):
    """A log line with the `kind` of event it reports (the same code as `cause`) and the `facts` it states."""

    @property
    def kind(self):
        return self.cause


def _rebuild(cls, cause, text, choices, facts):
    return cls(cause, text, choices, **facts)


def cause_of(text):
    """The code of a refusal or log line, or None for a plain string."""
    return getattr(text, "cause", None)


def choices_of(refusal):
    """The valid answers a refusal offers, or None."""
    return getattr(refusal, "choices", None)


def facts_of(text):
    """The figures a refusal or log line states, as a dict (empty for a plain string)."""
    return getattr(text, "facts", None) or {}
