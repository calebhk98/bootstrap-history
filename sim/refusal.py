"""A refusal's text that also carries a stable cause code.

Verbs such as hire and train answer `(ok, text)`. The text is for the player and its wording changes;
the cause (`literacy_wall`, `household_room`, ...) is what a reader tests. A `Refusal` is a plain string
everywhere a string is expected, so existing callers are unchanged; code that builds the reply or the
test reads `.cause`, and `.choices` when the refusal offers a list of valid answers. Any string operation
(`+`, `%`, slicing) returns an ordinary string, so wrap the final text last.
"""


class Refusal(str):
    """Refusal text with a `cause` code and, optionally, the `choices` that would have been accepted."""

    def __new__(cls, cause, text, choices=None):
        instance = super().__new__(cls, text)
        instance.cause = cause
        instance.choices = list(choices) if choices is not None else None
        return instance

    def __getnewargs__(self):
        return self.cause, str(self), self.choices


def cause_of(refusal):
    """The cause code of a refusal, or None for a plain string."""
    return getattr(refusal, "cause", None)


def choices_of(refusal):
    """The valid answers a refusal offers, or None."""
    return getattr(refusal, "choices", None)
