"""The one reader for the words after `available`.

Option words may come in any order and are lifted out of the line wherever
they stand; whatever bare words are left form the subject.
"""

_STATE_WORDS = ("startable", "blocked", "active", "done", "completed")
_FLAG_WORDS = {"all": "all", "reverse": "reverse", "reversed": "reverse",
               "desc": "reverse", "descending": "reverse"}
# word -> (output key, kind); a "words" value runs to the next option word
_VALUE_WORDS = {
    "find": ("find", "words"), "search": ("find", "words"), "named": ("find", "words"),
    "subject": ("subject", "words"), "group": ("subject", "words"),
    "afford": ("afford", "number"), "under": ("afford", "number"),
    "within": ("afford", "number"),
    "limit": ("limit", "count"), "offset": ("offset", "count"),
    "heard": ("heard_offset", "count"), "heard_offset": ("heard_offset", "count"),
    "sort": ("sort", "one"), "state": ("state", "one"), "tag": ("tag", "one"),
    "category": ("category", "one"), "cat": ("category", "one"),
}


def _is_option(word):
    return word in _FLAG_WORDS or word in _VALUE_WORDS or word in _STATE_WORDS


def _words_until_option(low, start):
    end = start
    while end < len(low) and not _is_option(low[end]):
        end += 1
    return " ".join(low[start:end]), end


def _read_value(out, low, index, to_number):
    """Consume one option and its value; returns (next index, error or None)."""
    word = low[index]
    key, kind = _VALUE_WORDS[word]
    if kind == "words":
        text, end = _words_until_option(low, index + 1)
        if not text:
            return end, "'%s' needs a word to look for." % word
        out[key] = (out[key] + " " + text) if key in out else text
        return end, None
    if index + 1 >= len(low):
        return index + 1, "'%s' needs a value." % word
    value = low[index + 1]
    if kind == "one":
        out[key] = value
        return index + 2, None
    number = to_number(value)
    if number is None or number < 0:
        return index + 2, "'%s' needs a number, not %r." % (word, value)
    out[key] = int(number) if kind == "count" else number
    return index + 2, None


def parse_available_words(low, to_number):
    """(command dict, error) from the lowercased words after `available`."""
    out = {"cmd": "available"}
    index = 0
    while index < len(low):
        word = low[index]
        if word in _FLAG_WORDS:
            out[_FLAG_WORDS[word]] = True
            index += 1
        elif word in _STATE_WORDS:
            out["state"] = word
            index += 1
        elif word in _VALUE_WORDS:
            index, error = _read_value(out, low, index, to_number)
            if error:
                return None, error
        elif word == "in" and "subject" not in out:
            index += 1
        elif to_number(word) is not None:
            out["afford"] = to_number(word)
            index += 1
        else:
            text, index = _words_until_option(low, index)
            out["subject"] = (out["subject"] + " " + text) if "subject" in out else text
    return out, None
