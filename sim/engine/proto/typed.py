"""Parsing what a person types at `play`'s prompt into the one JSON command dict the protocol already understands. A parser, not a second implementation - see its own module comment below."""

import json

from .dispatch import KNOWN_COMMANDS
from .nodes import NODE_IDS, NODE_IDS_LOWER

# ---------------------------------------------------------------------------
# TYPED COMMANDS, for a person at a keyboard.
#
# Everything a player can do lived only in the JSON protocol above. `play` -
# the human front door - understood six things: next year, available, status,
# start, stop, quit. Money, hiring, teaching a trade, working for wages,
# policy, the ledger, saving: a human could not reach any of it without
# typing JSON at a prompt, and the menu's answer was to hand them
# {"cmd":"available"} and wish them luck.
#
# So this is a parser and NOT a second implementation. It turns a typed line
# into exactly the dict the JSON protocol takes, and hands it to the same
# _agent_dispatch below. There is one command set, one set of rules, and one
# place a new command has to be added. A typed game and a scripted game
# cannot disagree about what the game is, because underneath they are the
# same call.
# ---------------------------------------------------------------------------

# What a person types on the left, the protocol's own name on the right. The
# single letters are the ones `play` has always used, kept because the older
# notes and anyone who has played before will still type them.
TYPED_ALIASES = {
    "s": "state", "st": "state", "status": "state",
    "a": "available", "av": "available", "options": "available",
    "n": "step", "next": "step", "wait": "step", "year": "step",
    "x": "stop", "abandon": "stop", "cancel": "stop",
    "q": "quit", "exit": "quit", "bye": "quit",
    "h": "help", "?": "help", "commands": "help",
    "ledger": "money", "accounts": "money", "cash": "money",
    "hazards": "risk", "risks": "risk",
    "history": "log", "diary": "log", "logs": "log", "journal": "log",
    "people": "labour", "staff": "labour", "workers": "labour",
    "demographics": "population", "demography": "population", "census": "population",
    "pop": "population",
    "dismiss": "fire", "sack": "fire", "lay": "fire",
    "job": "commission", "hireout": "commission",
    "teach": "train", "learn": "train",
    "price": "quote", "cost": "quote",
    "shut": "close", "closemine": "close", "close_mine": "close",
    "begin": "start", "research": "start", "build": "start",
    "explain": "why", "look": "why", "inspect": "why",
    "route": "path", "plan": "path",
    "workings": "mines", "mine": "mines", "pits": "mines",
    "blocked": "stuck", "help_me": "stuck", "why_stuck": "stuck",
    "retire": "withdraw", "step_back": "withdraw", "obscurity": "withdraw",
    "beliefs": "values", "traits": "values", "society": "values",
    "startall": "rush", "start_all": "rush", "muster": "rush",
    "overview": "capacity", "industry": "capacity", "dashboard": "capacity",
    "infrastructure": "capacity", "power": "capacity",
    "prices": "economy", "econ": "economy",
    "diff": "changes", "recap": "changes", "summary": "changes",
    "direct": "allocate", "assign": "allocate", "split": "allocate",
}


def _typed_number(tok):
    """The token as a number, or None. Tolerates 1,000 and 1_000 because
    people type both, and a thousand-separator is not a syntax error."""
    try:
        return float(str(tok).replace(",", "").replace("_", ""))
    except (TypeError, ValueError):
        return None


def _absorb_key_colons(rest, flag_keys, value_keys):
    """Normalise 'key:value' typed tokens into the plain words the rest of a
    command's own parser already reads one at a time.

    'sort:risk' becomes the two words 'sort', 'risk' - value_keys, where the
    value matters. 'all:true' becomes the one bare word 'all'; 'all:false'
    is dropped outright, the same as never typing it - flag_keys, a word
    whose own presence IS the value and which a command's follow-up loop
    turns into True on sight.

    Every one of these was the same break, found three times: a typed
    key:value pair that `help commands` itself advertises fell straight
    through a loop that only read bare words, with no error - 'available
    all:true' became a search for the literal string "all:true" and quietly
    matched nothing, then 'available ... limit:N', then 'available
    reverse:true'. Fixing the instance in front of you each time is how it
    kept coming back in a fourth command; this is the one place it is fixed
    for every caller that uses it, including the next one.
    """
    out = []
    for token in rest:
        text = str(token)
        if ":" in text:
            key, _, value = text.partition(":")
            lower_key = key.lower()
            if lower_key in flag_keys:
                if value.lower() in ("false", "0", "no", "off"):
                    continue          # same as never having typed it
                out.append(key)
                continue
            if lower_key in value_keys:
                out.append(key)
                if value:
                    out.append(value)
                continue
        out.append(text)
    return out


# THE AGENT-ORIENTED COMPACT MODE. See Complaints/35 section 1: a player of
# this game who is itself an AI agent asked for "an explicit agent-oriented
# compact mode that can return highly structured state without losing the
# human-readable explanations... I wouldn't rush to remove the prose."
#
# THE MACHINERY ALREADY EXISTED, for three commands. `state json`, `risk
# json` and `portfolio json` each hand-rolled their own scan of the typed
# words for the literal token "json" and set a "json" field on the command
# dict; cli.py's own reply loop already reads that field GENERICALLY - "if
# cmd.get('json'): dump the raw reply; else: render it" - for every command,
# not just those three, and does so whether the field arrived typed or as a
# raw {"cmd":...,"json":true} pasted straight from the JSON protocol the
# game's help text already documents. So typing '{"cmd":"available",
# "json":true}' at the very same prompt already worked. What was missing was
# the typed shortcut for everything else: a player (or agent) typing plain
# words had no way to ask for it on 'available', 'why', 'stuck', 'log', or
# any of the other twenty-odd read commands without already knowing to hand
# write JSON.
#
# MOST OF THE REPLY ITSELF NEEDED NO CHANGE. Every reply already IS the
# structured dict the protocol returns - `why`'s "start_blocked_reason",
# "waiting_on" and "missing_prerequisites", `state`'s "stuck" and
# "why_underfunded", `stuck`'s own "each_waiting_on" - the reasoning was
# always a field on the same dict the numbers live on, never a second,
# separate explanation that only render.py knew how to produce. The one
# thing render.py does that the raw reply cannot is loop and pad it into a
# fixed-width table; asking for "json" skips exactly that step and nothing
# else, so a project cost, its reason for being blocked, and the sentence
# explaining that reason arrive in the same object, on demand, from a
# command an agent already knew how to send. 'compact' (see below) goes one
# step further, for the handful of commands whose whole reason to exist is
# explaining a block, and gives them all the same small shape for it.
#
# 'json' AND 'compact' ARE TWO DIFFERENT THINGS, not one word spelled two
# ways, because they answer two different questions:
#
#   'json'    - a PRESENTATION switch only. It has always meant "show me the
#               reply this command already computes, raw, instead of
#               rendering it into the screen" - the reply's own fields are
#               untouched either way. This is what `state json`, `risk json`
#               and `portfolio json` already did; it is now every command's
#               to ask for, not just those three.
#   'compact' - a CONTENT switch, new. It asks the small set of commands
#               whose whole job is explaining why something is blocked
#               ('why', 'state', 'stuck') to ALSO fold their existing
#               reasoning fields into one small, identically-shaped
#               "blockers" list - see dispatch.py's _add_compact_fields.
#               Nothing is removed to make room for it: every field the
#               plain reply already had is still there, so asking for
#               'compact' costs nothing if you only wanted 'json'.
#
# 'compact' IMPLIES 'json' - an enriched dict is only worth asking for if it
# is not then immediately flattened back into a table that does not know
# the new fields exist - so typing 'compact' alone is enough; you do not
# also have to type 'compact json'.
_JSON_WORDS = ("json",)
_COMPACT_WORDS = ("compact",)


def _split_json_flag(rest):
    """rest with any bare 'json'/'compact' token removed, and (want_json,
    want_compact) for what was found - checked and stripped ONCE, for every
    command, before that command's own parser ever sees `rest`. Without
    this, a player typing either documented word in the wrong place risks
    the same failure mode an unrecognised bare word falls into:
    'available json' has no case above that recognises the bare
    word "json", so it would fall through to the last branch - "a bare word is a
    subject" - and become a search for a subject literally spelled "json",
    matching nothing, with no hint that the word had been understood as
    anything other than mistyped noise. Filtering both out up front, once,
    means every command's own parser goes on reading exactly the words it
    always has.
    """
    want_json = False
    want_compact = False
    kept = []
    for token in rest:
        low = str(token).strip().lower()
        if low in _JSON_WORDS:
            want_json = True
            continue
        if low in _COMPACT_WORDS:
            want_compact = True
            continue
        kept.append(token)
    if want_compact:
        want_json = True          # see the block comment just above
    return kept, want_json, want_compact


def parse_typed(line):
    """One typed line -> (command dict, None), or (None, a refusal to show).

    Returns (None, None) for a blank line: nothing to do and nothing to say.
    """
    if line is None:
        return None, None
    text = line.strip()
    if not text:
        return None, None
    # A player who has read the JSON docs, or pasted from their own notes,
    # should not be told their own game's protocol is a syntax error.
    if text.startswith("{"):
        try:
            obj = json.loads(text)
        except ValueError as error:
            return None, "that looked like JSON but would not parse: %s" % error
        if isinstance(obj, dict) and "cmd" in obj:
            return obj, None
        return None, "a JSON command needs a 'cmd' field."

    # ONE COMMAND PER LINE. `step 1; step 1` advanced a single year and said
    # nothing about the half of the line it dropped. Silently doing part of what
    # was asked is the worst of the three options; the other two are doing all
    # of it or saying you will not.
    if ";" in text:
        first = text.split(";")[0].strip()
        return None, ("one command per line - I will not guess which half you "
                      "meant. Send %r on its own line, then the next."
                      % (first or text.strip()))
    parts = text.split()
    head = parts[0].lower()
    rest = parts[1:]
    command = TYPED_ALIASES.get(head, head)
    if command not in KNOWN_COMMANDS:
        near = [candidate for candidate in KNOWN_COMMANDS if candidate.startswith(head[:3])]
        return None, ("no command called %r. Type 'help' for the list%s."
                      % (head, (", or did you mean: " + ", ".join(near)) if near else ""))

    # THE OUTPUT-MODE WORDS, STRIPPED ONCE, FOR EVERY COMMAND - see
    # _split_json_flag's own comment for why this has to happen here, before
    # any command's own parser reads `rest`, rather than inside each one.
    rest, want_json, want_compact = _split_json_flag(rest)
    words = [word for word in rest if _typed_number(word) is None]
    nums = [_typed_number(word) for word in rest if _typed_number(word) is not None]

    out, err = _parse_command_body(command, rest, words, nums, want_json)
    # ONE PLACE BOTH FLAGS ARE APPLIED, for every command this parser has not
    # already given its own opinion about. `state`, `risk` and `portfolio`
    # set "json" themselves, always, true or false, because a player reading
    # their own typed command back (or a test asserting on it) has always
    # been able to see which way it went; every other command has never
    # carried the key at all when nobody asked for it, and this preserves
    # that - "json" only appears here when it is True, so a command with no
    # json opinion of its own is unaffected byte-for-byte when the word was
    # never typed. "compact" is never set by any individual command's own
    # branch, so it is always added here, and only when asked for.
    if err is None and isinstance(out, dict):
        if want_json and "json" not in out:
            out = dict(out, json=True)
        if want_compact:
            out = dict(out, compact=True)
    return out, err


def _parse_bare_command(command, rest, words, nums, want_json):
    """A command that takes no arguments at all and always produces the same
    one-key dict, {"cmd": command}. Covers what were eight separate,
    identical original branches: money, values, materials, quit, score,
    ventures, mines, stuck, capacity."""
    return {"cmd": command}, None


def _parse_sell(command, rest, words, nums, want_json):
    if not words or not nums:
        return None, "sell needs a material and tonnes, e.g. 'sell iron 50'."
    return {"cmd": "sell", "material": words[0].lower(), "n": nums[0]}, None


def _parse_risk(command, rest, words, nums, want_json):
    # 'risk json' (or 'risk compact') prints the raw reply - see
    # 'portfolio json' and 'state json' just below for the same fix in
    # the same family. want_json is already the answer: _split_json_flag
    # stripped the word out of `rest` (and so out of `words`) before
    # this function was even called.
    return {"cmd": "risk", "json": want_json}, None


def _parse_rush(command, rest, words, nums, want_json):
    # 'rush' alone starts everything you could begin today; 'rush 5',
    # 'rush limit:5' and 'rush limit 5' all cap it at the first five,
    # highest-leverage first.
    #
    # limit:N IS THE FORM THE HELP TEXT ADVERTISES - "add limit:N to cap
    # it" - and it must be accepted: `limit:3` is not itself a bare number,
    # so if `nums` alone decided the limit, no limit would be set and the
    # command would start everything startable. The safest-looking
    # spelling of the most expensive command in the game must not be the
    # one that silently removes the safety. Same key:value spelling
    # `state full:true` already takes.
    out = {"cmd": "rush"}
    if any(str(word).lower() in ("force", "confirm", "yes") for word in rest):
        out["force"] = True
    _lim = None
    for word in rest:
        token_text = str(word)
        for pre in ("limit:", "limit=", "n:", "n="):
            if token_text.lower().startswith(pre):
                value = _typed_number(token_text[len(pre):])
                if value is None:
                    # AND A CAP THAT DID NOT PARSE IS A REFUSAL, not a
                    # shrug. Falling through to no limit at all means the
                    # one typo a player can make while trying to be
                    # careful is the typo that starts everything.
                    return None, ("'%s' is not a number of things to "
                                  "start. 'rush limit:3' begins the three "
                                  "highest-leverage things you could "
                                  "begin today; 'rush' alone begins every "
                                  "one of them." % token_text[len(pre):])
                _lim = value
                break
    if _lim is None and nums:
        _lim = nums[0]
    if _lim is not None:
        out["limit"] = int(_lim)
    return out, None


def _parse_state(command, rest, words, nums, want_json):
    # 'state full' and 'state full:true' both mean the same thing, and a
    # player who has read the JSON docs will type the second. 'state
    # json' (in any position, 'state full json' included, and now 'state
    # compact' too - see _split_json_flag) prints the raw reply instead
    # of the rendered screen: every player of this game is an AI agent
    # parsing text, and several have lost runs to parsing prose that was
    # never meant to be machine-readable.
    low_rest = [word.lower() for word in rest]
    want_full = bool(rest) and low_rest[0].split(":")[0] == "full"
    return {"cmd": "state", "full": want_full, "json": want_json}, None


def _available_consume_find_afford_or_limit(out, low, i):
    """The first half of the 'available' narrowings that read a following
    word: find/search/named, afford/under/within, limit. Returns (new_i,
    True) if one matched - new_i already includes both the inner `i += 1`
    the original elif body used when it consumed the following word, and the
    loop's own trailing `i += 1` - or (i, False) if none did, so the caller
    tries the remaining narrowings at the same, unmoved index. Split from
    _available_consume_offset_heard_or_sort only to keep each half's
    complexity low; together the two are one straight split of the original
    elif chain, tried in its original order. See _parse_available.
    """
    word = low[i]
    nxt = low[i + 1] if i + 1 < len(low) else None
    if word in ("find", "search", "named") and nxt:
        out["find"] = nxt
        return i + 2, True
    if word in ("afford", "under", "within") and nxt is not None:
        out["afford"] = _typed_number(nxt) or 0
        return i + 2, True
    if word == "limit" and nxt is not None:
        out["limit"] = int(_typed_number(nxt) or 0)
        return i + 2, True
    return i, False


def _available_consume_offset_heard_or_sort(out, low, i):
    """The second half of the 'available' narrowings that read a following
    word: offset, heard/heard_offset, sort - tried only once
    _available_consume_find_afford_or_limit has not matched. Same (new_i,
    matched) contract as that function. See _parse_available.
    """
    word = low[i]
    nxt = low[i + 1] if i + 1 < len(low) else None
    if word == "offset" and nxt is not None:
        out["offset"] = int(_typed_number(nxt) or 0)
        return i + 2, True
    if word in ("heard", "heard_offset") and nxt is not None:
        out["heard_offset"] = int(_typed_number(nxt) or 0)
        return i + 2, True
    # SORT AND REVERSE, spelled the way a person would type them:
    # 'available sort risk reverse'. Paging through a long list by hand,
    # thirty at a time, is exactly the failure a typed synonym for the
    # JSON 'sort' field exists to stop.
    if word == "sort" and nxt:
        out["sort"] = nxt
        return i + 2, True
    return i, False


def _available_consume_flag_or_subject(out, rest, low, i):
    """The remaining 'available' narrowings, tried only once
    _available_consume_find_afford_or_limit and
    _available_consume_offset_heard_or_sort have not matched: reverse/
    reversed/desc/descending, a bare number read as 'afford', and the two
    ways the rest of the line becomes a subject search. Returns (new_i,
    True) with a stop signal when the whole scan is done - the subject
    branches consume the rest of the line, the original loop's own `break`
    - or (new_i, False) to keep scanning. See _parse_available.
    """
    word = low[i]
    nxt = low[i + 1] if i + 1 < len(low) else None
    if word in ("reverse", "reversed", "desc", "descending"):
        out["reverse"] = True
        return i + 1, False
    if _typed_number(word) is not None:
        out["afford"] = _typed_number(word)
        return i + 1, False
    if word in ("subject", "group", "in") and nxt:
        out["subject"] = " ".join(rest[i + 1:])
        return i, True
    # A bare word is a subject: 'available metallurgy'. Subjects are
    # several words long ("roads, bridges and canals"), so take the
    # whole tail rather than one token.
    out["subject"] = " ".join(rest[i:])
    return i, True


def _parse_available(command, rest, words, nums, want_json):
    # 'available' alone is the digest. The rest are the same narrowings the
    # digest itself suggests, spelled the way a person would say them:
    #   available metallurgy      available find furnace
    #   available afford 900      available all
    #   available limit 30 offset 30
    #   available find furnace sort risk reverse
    out = {"cmd": "available"}
    # key:value AND key value, BOTH. This loop read bare words only, so
    # `available all:true` - the spelling `help commands` itself gives -
    # fell all the way through to the subject branch at the bottom and was
    # used as a search string named "all:true", silently matching nothing.
    # A Han player reported it as a documentation bug and was right; the
    # same hole swallowed limit:30, find:furnace and every other pair, and
    # - found later, same shape exactly - `reverse:true`, which fell
    # through to the same subject branch and was read as a search for the
    # literal text "reverse:true". See _absorb_key_colons, which now does
    # this for every caller rather than once per command found missing it.
    rest = _absorb_key_colons(
        rest,
        flag_keys=("all", "reverse", "reversed", "desc", "descending"),
        value_keys=("find", "search", "named", "afford", "under", "within",
                    "limit", "offset", "heard", "heard_offset", "sort"))
    low = [word.lower() for word in rest]
    # THE TOKEN LOOP ITSELF, kept here so the scanning (which token is next,
    # when to stop) stays in one place; what each token MEANS is delegated to
    # the three helpers above, tried in a fixed order, as an elif chain
    # would.
    i = 0
    while i < len(low):
        word = low[i]
        if word == "all":
            out["all"] = True
            i += 1
            continue
        i, matched = _available_consume_find_afford_or_limit(out, low, i)
        if matched:
            continue
        i, matched = _available_consume_offset_heard_or_sort(out, low, i)
        if matched:
            continue
        i, stop = _available_consume_flag_or_subject(out, rest, low, i)
        if stop:
            break
    return out, None


def _parse_help(command, rest, words, nums, want_json):
    return {"cmd": "help", "topic": (rest[0].lower() if rest else None)}, None


def _parse_step(command, rest, words, nums, want_json):
    # A bare 'n' is one year - but `step abc` is not a bare 'n', and must
    # not silently fall through to the default and advance a year anyway
    # while `step 0` and `step -5` are properly refused. Accepting
    # unparseable input silently is the worst kind of inconsistency,
    # because it does something other than what was asked and says
    # nothing.
    if rest and not nums:
        return None, ("step takes a number of years, e.g. 'step 5', or "
                      "nothing at all for one. %r is not a number."
                      % " ".join(rest))
    return {"cmd": "step", "years": (nums[0] if nums else 1)}, None


def _log_consume_find_since_or_before(out, low, i):
    """The first half of the 'log' narrowings that read a following word:
    find/search, since, before. Returns (new_i, True) if one matched - new_i
    already includes both the inner `i += 1` the original elif body used
    when it consumed the following word, and the loop's own trailing
    `i += 1` - or (i, False) if none did, so the caller tries the remaining
    narrowings at the same, unmoved index. Split from
    _log_consume_limit_or_offset only to keep each half's complexity low;
    together the two are one straight split of the original elif chain,
    tried in its original order. See _parse_log.
    """
    word = low[i]
    nxt = low[i + 1] if i + 1 < len(low) else None
    if word in ("find", "search") and nxt:
        out["find"] = nxt
        return i + 2, True
    if word == "since" and nxt is not None:
        out["since"] = int(_typed_number(nxt) or 0)
        return i + 2, True
    if word == "before" and nxt is not None:
        out["before"] = int(_typed_number(nxt) or 0)
        return i + 2, True
    return i, False


def _log_consume_limit_or_offset(out, low, i):
    """The second half of the 'log' narrowings that read a following word:
    limit, offset - tried only once _log_consume_find_since_or_before has
    not matched. Same (new_i, matched) contract as that function. See
    _parse_log.
    """
    word = low[i]
    nxt = low[i + 1] if i + 1 < len(low) else None
    if word == "limit" and nxt is not None:
        out["limit"] = int(_typed_number(nxt) or 0)
        return i + 2, True
    if word == "offset" and nxt is not None:
        out["offset"] = int(_typed_number(nxt) or 0)
        return i + 2, True
    return i, False


def _log_consume_order_or_limit(out, low, i):
    """The remaining 'log' narrowings, tried only once
    _log_consume_find_since_or_before and _log_consume_limit_or_offset have
    not matched: oldest/forward, newest/backward/recent, and a bare number
    read as 'limit'. Always returns i + 1 - the original loop's own trailing
    `i += 1`, which ran whether or not any of these matched, silently
    skipping a token none of the chain recognised. See _parse_log.
    """
    word = low[i]
    if word in ("oldest", "forward"):
        out["order"] = "oldest"
    elif word in ("newest", "backward", "recent"):
        out["order"] = "newest"
    elif _typed_number(word) is not None:
        out["limit"] = int(_typed_number(word))
    return i + 1


def _parse_log(command, rest, words, nums, want_json):
    # 'log' alone is the twenty most recent lines. The same narrowings
    # 'available' takes, spelled the way a person would say them:
    #   log failures              log find plague
    #   log since 300             log before 200 oldest
    #   log limit 50 offset 50
    out = {"cmd": "log"}
    # SAME FAMILY, SAME FIX. 'log failures:true' was the same shape as
    # 'available all:true' - a key:value pair `help` never tells anyone
    # NOT to type, read by a loop that only matched bare words - except
    # here there is no subject fallback to land in, so it failed even
    # more quietly: the flag was simply dropped, with the command
    # reporting ok:true on a plain, unfiltered log instead of erroring or
    # searching. See _absorb_key_colons.
    rest = _absorb_key_colons(
        rest,
        flag_keys=("failures", "failure", "fails", "fail",
                  "oldest", "forward", "newest", "backward", "recent"),
        value_keys=("find", "search", "since", "before", "limit", "offset"))
    low = [word.lower() for word in rest]
    # THE TOKEN LOOP ITSELF, kept here so the scanning stays in one place;
    # what each token MEANS is delegated to the three helpers above, tried
    # in a fixed order, as an elif chain would.
    i = 0
    while i < len(low):
        word = low[i]
        if word in ("failures", "failure", "fails", "fail"):
            out["failures"] = True
            i += 1
            continue
        i, matched = _log_consume_find_since_or_before(out, low, i)
        if matched:
            continue
        i, matched = _log_consume_limit_or_offset(out, low, i)
        if matched:
            continue
        i = _log_consume_order_or_limit(out, low, i)
    return out, None


def _parse_open_or_named_tech(command, rest, words, nums, want_json):
    """The 'open' command's own numeric-units special case, followed by the
    shared "name a technology" parsing that 'open' falls through to when it
    takes no trailing number - the same parsing why/path/start/stop/bounty/
    mothball/restore use outright. Kept as one function, in the original
    two-if order, because 'open' has to try the first shape before falling
    into the second; this function is only ever dispatched for the eight
    commands the original code guarded both blocks with, so that guard
    (`if command in (...)`) is implied by being called at all and is not
    repeated here.
    """
    if command == "open" and nums:
        # A TRAILING NUMBER IS UNITS, NOT PART OF THE NAME. 'open
        # school_founded 2' founds a second school - see
        # ProjectsMixin._expand_institution. No id is only digits, so a
        # number anywhere in the line is unambiguously this, not a stray word
        # of a multi-word name.
        want = " ".join(words)
        if want not in NODE_IDS:
            want = NODE_IDS_LOWER.get(want.lower(), want)
        return {"cmd": "open", "id": want, "units": nums[-1]}, None

    if not rest:
        return None, ("%s needs the name of a technology, e.g. '%s "
                      "fud_wheelbarrow'. 'available' lists what you can "
                      "begin now." % (command, command))
    # MATCHED CASE-INSENSITIVELY, NOT LOWERCASED: flattening the case would
    # break ids that genuinely carry capitals, among them the whole
    # cap_pure_2N/4N/6N/9N purity ladder, which sits on the critical path
    # to germanium. So: try what was typed, then try a case-insensitive
    # match against the real ids, and keep whatever the tree actually
    # calls it.
    #
    # THE WHOLE REST OF THE LINE, NOT JUST rest[0]. Every screen in this
    # game prints a NAME - "Horizontal loom", two words - and every one of
    # these commands took only an id until now, so 'why horizontal loom'
    # silently discarded 'loom' and asked about a nonexistent 'horizontal'.
    # A single id never has a space in it, so joining the whole tail costs
    # a one-word id nothing and is what a multi-word name needs. Names are
    # not unique, so this does not resolve them here - _agent_dispatch_inner
    # does that, because resolving under fog has to filter candidates by
    # what the player has actually heard of, which needs the live Sim this
    # function does not have.
    want = " ".join(rest)
    if want not in NODE_IDS:
        want = NODE_IDS_LOWER.get(want.lower(), want)
    return {"cmd": command, "id": want}, None


def _parse_withdraw(command, rest, words, nums, want_json):
    return {"cmd": "withdraw"}, None


def _parse_portfolio(command, rest, words, nums, want_json):
    # 'portfolio json' (or 'portfolio compact') prints the raw reply
    # instead of the rendered table. A player typing that after reading
    # the JSON docs should not have it silently ignored if it comes second
    # in the line - every player of this game is an AI agent parsing text,
    # and prose is not a stable interface to parse. want_json is scanned across the whole line
    # (not just rest[0]) by _split_json_flag, upstream of this function.
    return {"cmd": "portfolio", "json": want_json}, None


def _parse_economy(command, rest, words, nums, want_json):
    return {"cmd": "economy", "full": "full" in [word.lower() for word in words]}, None


def _parse_changes(command, rest, words, nums, want_json):
    # 'changes' alone means the last 5 years; 'changes 10' means ten.
    return {"cmd": "changes", "years": (nums[0] if nums else 5)}, None


def _parse_bribe(command, rest, words, nums, want_json):
    if not nums:
        return None, "bribe needs an amount, e.g. 'bribe 500'."
    return {"cmd": "bribe", "amount": nums[0]}, None


def _parse_population(command, rest, words, nums, want_json):
    # No argument: the country, the town, and every trade at once. Not
    # a fog spoiler (see the op handler's own comment) - demography,
    # not the tech tree - so nothing here is gated on what the player
    # has discovered.
    return {"cmd": "population"}, None


def _parse_labour(command, rest, words, nums, want_json):
    # A PLAYER WHO TYPES THE FIELD NAME MEANS THE FIELD: the help shows
    # {"cmd":"labour","trade":"smith"}, so `labour trade smith` is the
    # obvious typed reading of it, and the literal word "trade" must be
    # stripped before picking a trade name, or it reads as "no such trade:
    # trade". Same risk `available subject metallurgy` avoids by stripping
    # "subject": left in, it would quietly search for a subject literally
    # called "subject metallurgy" and report nothing startable.
    _trade_words = [word for word in words if word.lower() != "trade"]
    return {"cmd": "labour", "trade": (_trade_words[0].lower() if _trade_words else None)}, None


def _parse_hire_or_fire(command, rest, words, nums, want_json):
    if not words:
        return None, ("%s needs a trade, e.g. '%s smith 2'. 'labour' lists "
                      "which trades exist here." % (command, command))
    return {"cmd": command, "trade": words[0].lower(),
            "n": (nums[0] if nums else 1)}, None


def _parse_work_or_commission(command, rest, words, nums, want_json):
    if not words:
        return None, ("%s needs a trade and a number of hours, e.g. "
                      "'%s smith 200'." % (command, command))
    if not nums:
        return None, "%s needs a number of hours, e.g. '%s %s 200'." % (command, command, words[0])
    return {"cmd": command, "trade": words[0].lower(), "hours": nums[0]}, None


def _parse_train(command, rest, words, nums, want_json):
    # 'train smith 2' and 'train smith 2 from labourer' both read naturally.
    src_trade = None
    low = [word.lower() for word in words]
    if "from" in low:
        i = low.index("from")
        if i + 1 < len(low):
            src_trade = low[i + 1]
        low = low[:i]
    if not low:
        return None, ("train needs a trade to teach, e.g. 'train smith 2' "
                      "or 'train chemist 1 from artisan'.")
    out = {"cmd": "train", "trade": low[0], "n": (nums[0] if nums else 1)}
    if src_trade:
        out["from"] = src_trade
    return out, None


def _parse_buy_or_quote(command, rest, words, nums, want_json):
    if not words:
        return None, ("%s needs something to %s, e.g. '%s iron 500'."
                      % (command, command, command))
    # 'buy mine coal 500' and 'quote mine iron 200' are the forms the help
    # itself gives, so this must read the SECOND word as the material too,
    # not only the first - dropping it would fail every documented
    # three-word buy with an error that lists the material the player
    # just typed.
    out = {"cmd": command, "what": words[0].lower()}
    if len(words) > 1:
        out["material"] = words[1].lower()
    elif out["what"] in ("mine", "mines"):
        return None, "say which mineral, e.g. '%s mine coal 500'." % command
    # 'buy coal 500' means the same thing and is what a person types; the
    # protocol wants it spelled out as a mine in a mineral.
    if out["what"] in ("nitre", "saltpetre", "nitre_bed"):
        out["what"] = "nitre"
    elif out["what"] not in ("forest", "farm", "food", "housing", "houses",
                             "school", "trade_school", "material", "stock",
                             "slaves", "mine", "mines", "people",
                             "manumit", "manumission", "free"):
        out["material"], out["what"] = out["what"], "mine"
    if out["what"] == "mines":
        out["what"] = "mine"
    if nums:
        out["n"] = nums[0]
    return out, None


def _parse_close(command, rest, words, nums, want_json):
    if not words:
        return None, "close needs a mine, e.g. 'close iron'."
    # 'close mine coal' and 'close coal' both mean the one thing close does.
    mat = words[1].lower() if len(words) > 1 else words[0].lower()
    return {"cmd": "close", "what": mat, "material": mat}, None


def _parse_allocate(command, rest, words, nums, want_json):
    # Bare 'allocate' lists the standing orders in hand, same as bare
    # 'policy' lists the automatic switches.
    if not rest:
        return {"cmd": "allocate"}, None
    if not words:
        return None, ("say which project, or 'work', e.g. 'allocate "
                      "arithmetic_positional 500' or 'allocate work "
                      "labourer 100'.")
    target = words[0]
    _clear = any(word.lower() in ("off", "none", "clear", "stop")
                for word in words[1:]) or (bool(nums) and nums[0] == 0)
    if target.lower() == "work":
        out = {"cmd": "allocate", "id": "work"}
        trade = next((word.lower() for word in words[1:]
                     if word.lower() not in ("off", "none", "clear", "stop")),
                    None)
        if trade:
            out["trade"] = trade
        if _clear:
            out["hours"] = 0
        elif nums:
            out["hours"] = nums[0]
        else:
            return None, ("say how many hours a year, e.g. 'allocate "
                          "work labourer 100', or 'allocate work off' "
                          "to clear.")
        return out, None
    out = {"cmd": "allocate", "id": target}
    if _clear:
        out["hours"] = 0
    elif nums:
        out["hours"] = nums[0]
    else:
        return None, ("say how many hours a year, e.g. 'allocate %s "
                      "500', or 'allocate %s off' to clear."
                      % (target, target))
    return out, None


def _parse_policy(command, rest, words, nums, want_json):
    if not rest:
        return {"cmd": "policy"}, None
    if len(rest) < 2:
        return None, ("to change one, say which and whether, e.g. "
                      "'policy auto_hire off'. Bare 'policy' lists them.")
    val = rest[1].lower()
    if val in ("on", "true", "yes", "y", "1"):
        flag = True
    elif val in ("off", "false", "no", "n", "0"):
        flag = False
    else:
        return None, "say 'on' or 'off', e.g. 'policy auto_hire off'."
    return {"cmd": "policy", "set": {rest[0].lower(): flag}}, None


def _parse_save_or_load(command, rest, words, nums, want_json):
    if not rest:
        return None, "%s needs a file name, e.g. '%s mygame.json'." % (command, command)
    return {"cmd": command, "file": rest[0]}, None


# ONE ENTRY PER COMMAND NAME THIS PARSER HAS BEEN TAUGHT ABOUT, pointing at
# the function that parses it. Several names share a handler where the
# original code's bodies were identical or handled together (see each
# handler's own docstring/comment for why). This is the same shape as
# `_agent_dispatch_inner`'s split into forty handlers - see
# sim/ARCHITECTURE.md - applied to the same kind of function: a long chain
# of `if command == ...: return ...` branches, each one mutually exclusive
# with every other because they all test the same resolved `command` value.
# A dict lookup finds the one matching branch in one step instead of testing
# each condition in turn, without changing which branch runs for any input.
_COMMAND_PARSERS = {
    "money": _parse_bare_command,
    "values": _parse_bare_command,
    "materials": _parse_bare_command,
    "quit": _parse_bare_command,
    "score": _parse_bare_command,
    "ventures": _parse_bare_command,
    "mines": _parse_bare_command,
    "stuck": _parse_bare_command,
    "capacity": _parse_bare_command,
    "sell": _parse_sell,
    "risk": _parse_risk,
    "rush": _parse_rush,
    "state": _parse_state,
    "available": _parse_available,
    "help": _parse_help,
    "step": _parse_step,
    "log": _parse_log,
    "open": _parse_open_or_named_tech,
    "why": _parse_open_or_named_tech,
    "path": _parse_open_or_named_tech,
    "start": _parse_open_or_named_tech,
    "stop": _parse_open_or_named_tech,
    "bounty": _parse_open_or_named_tech,
    "mothball": _parse_open_or_named_tech,
    "restore": _parse_open_or_named_tech,
    "withdraw": _parse_withdraw,
    "retire": _parse_withdraw,
    "portfolio": _parse_portfolio,
    "economy": _parse_economy,
    "changes": _parse_changes,
    "bribe": _parse_bribe,
    "population": _parse_population,
    "labour": _parse_labour,
    "hire": _parse_hire_or_fire,
    "fire": _parse_hire_or_fire,
    "work": _parse_work_or_commission,
    "commission": _parse_work_or_commission,
    "train": _parse_train,
    "buy": _parse_buy_or_quote,
    "quote": _parse_buy_or_quote,
    "close": _parse_close,
    "allocate": _parse_allocate,
    "policy": _parse_policy,
    "save": _parse_save_or_load,
    "load": _parse_save_or_load,
}


def _parse_command_body(command, rest, words, nums, want_json):
    """The command-specific parsing `parse_typed` delegates to, once the line
    has been split into a resolved command name, the words, the numbers, and
    whether 'json' was typed (or implied by 'compact') and already stripped
    out of `rest`.

    Broken out so that stripping the output-mode words can happen exactly
    once, upstream of every branch below, instead of duplicated (or missed)
    in each one - see _split_json_flag.

    The actual per-command parsing lives in _COMMAND_PARSERS, one small
    function per command (or per small group of commands that always parsed
    identically). This function only looks up which one applies.
    """
    handler = _COMMAND_PARSERS.get(command)
    if handler is not None:
        return handler(command, rest, words, nums, want_json)
    # Any command added to KNOWN_COMMANDS that this parser has not been taught
    # about still reaches the dispatcher rather than being refused here.
    return {"cmd": command}, None
