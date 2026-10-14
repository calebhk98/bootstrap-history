"""Lists the checks that match on reply or screen text, split into presentation and behaviour.

`python3 -m sim.tests --text-checks` prints one line per text-matching check of a behaviour topic, then
the counts. `--text-checks --all` also lists the presentation ones. Complaint 515's rule: a test of model
behaviour asserts on structured values (the engine's numbers, the JSON reply's fields); only a test whose
subject is presentation (units, wording, rounding, layout) asserts on text. This reads the syntax tree and
runs nothing, so it is a heuristic; a miss shows up as a behaviour line that is really a key check, or a
check that reads text through a helper this does not recognise.

A check "reads text" when its condition tests a string against a name or expression that holds text:
a reply's `text`, a rendered screen, captured output, a message list joined to a string.
"""
import ast
import os
import re

from sim.tests.discovery import TESTS_DIR, discover_topics

# Source fragments that make an expression text rather than structure.
TEXT_SOURCE = re.compile(
    r"""\[["'](text|reason|cause|error|note|why|label|advice|message|blurb|line)["']\]|\.stdout|"""
    r"""render_|_render|\brender\b|\bstr\(|\.lower\(\)|["']\.join\(|\bjson\.dumps|"""
    r"""\bformat_|_text\b|\btext\b|\bscreen_text|\bmessage|\bmsg\b|\bblurb|\bprose|\bwording|\boutput\b|"""
    r"""\bcaptured|\bprinted|\bpretty|\.get\(["'](error|reason|cause|note|why)["']""")
# A bare name is textual when one of its underscore-separated words is one of these.
TEXT_WORDS = {"text", "line", "lines", "said", "reason", "cause", "error", "advice", "why", "msg",
              "message", "note", "output", "stdout", "blurb", "prose", "words", "received", "screen",
              "rendered", "printed", "warning", "announcement", "refusal", "story"}

# A check whose subject is presentation says so on its own line or the line above, with the reason.
PRESENTATION_MARK = "# presentation:"

# Topic or check names whose subject is presentation (units, wording, rounding, layout).
PRESENTATION = re.compile(
    r"wording|worded|\btext\b|messag|render|display|layout|format|\bunits?\b|rounding|rounded|label|phrase|"
    r"\bprints?\b|printed|column|width|pretty|\bmenu\b|prose|legend|heading|screen|"
    r"readout|\bsays?\b|\bnames\b|\bmention|banner|headline|abbrev|plural|spell|\bshows?\b|"
    r"\bread(s|ing)? (as|back)\b|\bwords?\b|\bpointer\b|footer|\bhelp\b|\bexplains?\b|\bcarries\b|"
    r"wording|\blists?\b the|\bwarns?\b|\bstates\b|\bleads\b|\bfirst lines?\b",
    re.I)


def _source(node, text):
    return ast.get_source_segment(text, node) or ""


def _textual_names(tree, text):
    """Names assigned from an expression that produces text."""
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            value_source = _source(node.value, text)
            if TEXT_SOURCE.search(value_source) and not isinstance(node.value, (ast.Dict, ast.List)):
                for target in node.targets:
                    for name in ast.walk(target):
                        if isinstance(name, ast.Name):
                            names.add(name.id)
    return names


def _rendered_names(tree, text):
    """Names assigned from a renderer's output: a check on them has presentation as its subject."""
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and re.search(r"\brender\w*\(|\bscreen\w*\(", _source(node.value, text)):
            names.update(name.id for target in node.targets for name in ast.walk(target)
                         if isinstance(name, ast.Name))
    return names


def _reads_source(node, text):
    """True for a search of program source or a file, which tests code and data, not a reply."""
    source = _source(node, text)
    return bool(re.search(r"source|\.read\(\)|getsource", source))


def _is_structured(node, text):
    """True for a structured value: a code or fact read off a refusal or log line, or a collection."""
    if isinstance(node, (ast.SetComp, ast.ListComp, ast.GeneratorExp, ast.DictComp, ast.Dict, ast.Set,
                         ast.List, ast.Tuple)):
        return True
    return bool(re.search(r"\b(facts_of|cause_of|choices_of)\(", _source(node, text)))


def _named_as_text(node):
    """True when the expression is a bare name (or an attribute) that is named for text: `line`, `reply.text`."""
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
        node = node.func.value
    word = node.id if isinstance(node, ast.Name) else node.attr if isinstance(node, ast.Attribute) else ""
    return bool(TEXT_WORDS & set(word.lower().strip("_").split("_")))


def _is_textual(node, text, names):
    source = _source(node, text)
    if _reads_source(node, text) or _is_structured(node, text):
        return False
    if _named_as_text(node):
        return True
    if any(isinstance(inner, ast.Name) and (inner.id in names) for inner in ast.walk(node)):
        return True
    return bool(TEXT_SOURCE.search(source))


def _reads_text(condition, text, names):
    """True if the condition tests a string constant or regex against text."""
    for node in ast.walk(condition):
        if isinstance(node, ast.Compare):
            for operator, right in zip(node.ops, node.comparators):
                if isinstance(operator, (ast.In, ast.NotIn)):
                    left_is_string = isinstance(node.left, ast.Constant) and isinstance(node.left.value, str)
                    if left_is_string and _is_textual(right, text, names):
                        return True
                    if left_is_string and re.search(r"\s", node.left.value.strip()) \
                            and not _reads_source(right, text) and not _is_structured(right, text):
                        return True
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr in ("startswith", "endswith", "count", "search", "match", "findall", "find"):
                if _is_textual(node.func.value, text, names) and node.args and any(
                        isinstance(argument, ast.Constant) and isinstance(argument.value, str)
                        for argument in node.args):
                    return True
    return False


def scan_topic(topic):
    """(is_presentation_topic, [(line, check_name, is_presentation_check, condition)]) for one topic."""
    path = os.path.join(TESTS_DIR, "test_%s.py" % topic)
    with open(path, encoding="utf-8") as handle:
        text = handle.read()
    tree = ast.parse(text, filename=path)
    docstring = ast.get_docstring(tree) or ""
    names = {name for name in _textual_names(tree, text)}
    names = {name for name in names if name not in ("_reply", "reply")} | set()
    rendered = _rendered_names(tree, text)
    source_lines = text.split("\n")
    topic_is_presentation = bool(PRESENTATION.search(docstring.split("\n\n")[0] + " " + topic.replace("_", " ")))
    found = []
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "check"):
            continue
        if len(node.args) < 2:
            continue
        if not _reads_text(node.args[1], text, names):
            continue
        name_node = node.args[0]
        check_name = " ".join(_source(name_node, text).replace('"', " ").split())
        condition_source = _source(node.args[1], text)
        marked = any(PRESENTATION_MARK in source_lines[number - 1]
                     for number in range(max(1, node.lineno - 1), (node.end_lineno or node.lineno) + 1))
        from_renderer = bool(re.search(r"\brender\w*\(", condition_source)) or any(
            isinstance(inner, ast.Name) and inner.id in rendered for inner in ast.walk(node.args[1]))
        found.append((node.lineno, check_name, marked or from_renderer or bool(PRESENTATION.search(check_name)),
                      " ".join(condition_source.split())))
    return topic_is_presentation, found


def report(show_presentation=False, show_conditions=False):
    behaviour, presentation = [], []
    for topic in discover_topics():
        topic_is_presentation, found = scan_topic(topic)
        for line, check_name, check_is_presentation, condition in found:
            row = (topic, line, check_name, condition)
            (presentation if topic_is_presentation or check_is_presentation else behaviour).append(row)
    for label, rows in (("presentation", presentation if show_presentation else []), ("behaviour", behaviour)):
        for topic, line, check_name, condition in rows:
            print("%-12s  %s:%d  %s" % (label, topic, line, check_name))
            if show_conditions:
                print("      " + condition[:240])
    topics = sorted({row[0] for row in behaviour})
    print("\nbehaviour checks reading text: %d in %d topics" % (len(behaviour), len(topics)))
    print("presentation checks reading text: %d" % len(presentation))
    return len(behaviour)
