"""Lists the checks that match on reply or screen text, split into presentation and behaviour (Complaint 515).

`python3 -m sim.tests --text-checks` prints one line per text-matching check that is not presentation, then the
counts; the complaint closes when that list is empty. `--all` also lists the presentation ones with the basis
for calling them presentation, and `--conditions` prints each check's condition under its line.

The rule (owner): a test of model behaviour asserts on structured values (the engine's numbers, the JSON
reply's fields, a refusal's `cause`, a log line's `kind` and `facts`; see sim/refusal.py); only a test whose
subject is presentation (units, wording, rounding, layout) asserts on text.

This reads the syntax tree and runs nothing, so it is a heuristic. A check "reads text" when its condition
tests a phrase, or a string against a name or expression that holds text (a reply's `error` or `note`, a
rendered screen, captured output, a log message), or compares a field to a multi-word string. The basis for
presentation is, in order: a `# presentation: <reason>` comment on the check's line or the line above; the
check reading the output of a `render*` call; the topic's name or first docstring paragraph; words in the
check's own name. A `# not text: <reason>` comment says the heuristic misread a stored value or an enumerated
field as wording; the checker then skips the check. The name and topic words are a guess to be audited with
`--all`; a check that reads text through a helper this does not recognise is not counted at all.
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
# A check the heuristic reads as text although it compares a stored value or an enumerated field; the reason follows.
NOT_TEXT_MARK = "# not text:"

# Topic or check names whose subject is presentation (units, wording, rounding, layout).
PRESENTATION = re.compile(
    r"wording|worded|\btext\b|messag|render|display|layout|format|\bunits?\b|rounding|rounded|label|phrase|"
    r"\bprints?\b|printed|column|width|pretty|\bmenu\b|prose|legend|heading|screen|"
    r"readout|\bsays?\b|\bnames\b|\bmention|banner|headline|abbrev|plural|spell|\bshows?\b|"
    r"\bread(s|ing)? (as|back)\b|\bwords?\b|\bpointer\b|footer|\bhelp\b|\bexplains?\b|\bcarries\b|"
    r"wording|\blists?\b the|\bwarns?\b|\bstates\b|\bleads\b|\bfirst lines?\b",
    re.I)


# Topic names or first docstring paragraphs whose subject is presentation. Narrower than PRESENTATION: a topic that
# merely "names" or "says" something may still test what the model does.
TOPIC_PRESENTATION = re.compile(
    r"wording|worded|\btext\b|messag|render|display|layout|format|\bunits?\b|rounding|label|\bmenu\b|pretty|"
    r"screens?\b|readout|\bhelp\b|noise|repeated|explain|disclosure|defects|guidance|prose|legend|"
    r"\bcli\b|quotes",
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
    return bool(re.search(r"\b(facts_of|cause_of|choices_of)\(|\[[\"'](commands|remedies|choices|ids|trades|fields)[\"']\]",
                          _source(node, text)))


def _named_as_text(node):
    """True when the expression is a bare name (or an attribute) that is named for text: `line`, `reply.text`."""
    if isinstance(node, ast.BoolOp):
        return any(_named_as_text(value) for value in node.values)
    if isinstance(node, ast.Call):
        function = node.func
        if isinstance(function, ast.Attribute) and function.attr in ("get", "lower", "strip"):
            function = function.value
        node = function
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
            if any(isinstance(operator, (ast.Eq, ast.NotEq)) for operator in node.ops):
                for side, other in ((node.left, node.comparators[0]), (node.comparators[0], node.left)):
                    if (isinstance(side, ast.Constant) and isinstance(side.value, str)
                            and len(side.value.split()) >= 2 and not _is_structured(other, text)
                            and not _reads_source(other, text)):
                        return True
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


def _basis(marked, from_renderer, topic_is_presentation, check_name):
    """Why a text-matching check counts as presentation, or None when it is a behaviour check."""
    if marked:
        return "marker"
    if from_renderer:
        return "renderer"
    if topic_is_presentation:
        return "topic"
    if PRESENTATION.search(check_name):
        return "name"
    return None


def scan_topic(topic):
    """[(line, check_name, basis, condition)] for the text-matching checks of one topic; basis is None for behaviour."""
    path = os.path.join(TESTS_DIR, "test_%s.py" % topic)
    with open(path, encoding="utf-8") as handle:
        text = handle.read()
    tree = ast.parse(text, filename=path)
    docstring = ast.get_docstring(tree) or ""
    names = _textual_names(tree, text) - {"_reply", "reply"}
    rendered = _rendered_names(tree, text)
    source_lines = text.split("\n")
    topic_is_presentation = bool(TOPIC_PRESENTATION.search(docstring.split("\n\n")[0] + " " + topic.replace("_", " ")))
    found = []
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "check"):
            continue
        if len(node.args) < 2 or not _reads_text(node.args[1], text, names):
            continue
        check_name = " ".join(_source(node.args[0], text).replace('"', " ").split())
        condition_source = _source(node.args[1], text)
        marker_lines = [source_lines[number - 1]
                        for number in range(max(1, node.lineno - 1), (node.end_lineno or node.lineno) + 1)]
        if any(NOT_TEXT_MARK in line for line in marker_lines):
            continue
        marked = any(PRESENTATION_MARK in line for line in marker_lines)
        from_renderer = bool(re.search(r"\brender\w*\(", condition_source)) or any(
            isinstance(inner, ast.Name) and inner.id in rendered for inner in ast.walk(node.args[1]))
        found.append((node.lineno, check_name, _basis(marked, from_renderer, topic_is_presentation, check_name),
                      " ".join(condition_source.split())))
    return found


def report(show_presentation=False, show_conditions=False):
    behaviour, presentation = [], []
    for topic in discover_topics():
        for line, check_name, basis, condition in scan_topic(topic):
            (behaviour if basis is None else presentation).append((topic, line, check_name, basis, condition))
    for rows in (presentation if show_presentation else [], behaviour):
        for topic, line, check_name, basis, condition in rows:
            print("%-22s %s:%d  %s" % ("presentation[%s]" % basis if basis else "behaviour", topic, line, check_name))
            if show_conditions:
                print("      " + condition[:240])
    topics = sorted({row[0] for row in behaviour})
    by_basis = {}
    for row in presentation:
        by_basis[row[3]] = by_basis.get(row[3], 0) + 1
    print("\nbehaviour checks reading text: %d in %d topics" % (len(behaviour), len(topics)))
    print("presentation checks reading text: %d (%s)" % (
        len(presentation), ", ".join("%s %d" % (basis, count) for basis, count in sorted(by_basis.items()))))
    return len(behaviour)
