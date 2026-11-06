"""Every call `Name(...)` in sim/ and mods/ (tests excluded) that resolves, through the file's own imports and definitions, to a
class defined in sim/ or mods/ is checked against that class's constructor: positional count, keyword names, and required
arguments. A class's constructor is its `__init__`, or the dataclass fields (kw_only, init=False, InitVar, inherited fields),
or the `__init__` of a base class that resolves. Calls through `from m import C`, `import m as a; a.C`, `from pkg import mod;
mod.C` and re-exports (an `api.py`) are followed. A call that cannot be resolved, a class whose constructor cannot be read
statically, and a call with `*args` or `**kwargs` are skipped and counted.

Also checked: every class in a module's `PARTS` is built as `part_class(module)` by Module.build_parts, so its constructor must
take exactly (self, module).

Run from the repository root; prints one line per problem and exits 1 if any. `--stats` adds a final `checked N, skipped M` line, and `--reasons` the skipped calls counted per reason.

A call with `*args` or `**kwargs` is checked for what it writes out (its leading positional arguments and its keyword names). A built-in
exception, called or used as a base, takes positional arguments and no keyword."""
import ast
import builtins
import sys
from collections import Counter

sys.path.insert(0, "tools")
from class_index import Index  # noqa: E402

PLAIN_DECORATORS = {"dataclass", "dataclasses.dataclass", "total_ordering", "functools.total_ordering", "final", "typing.final"}
NO_INIT_BASES = {"object", "Generic", "typing.Generic"}


class Signature:
    """positional: [(name, required, positional_only)] in call order; keyword_only: [(name, required)]."""

    def __init__(self, positional, keyword_only, varargs, varkw):
        self.positional = positional
        self.keyword_only = keyword_only
        self.varargs = varargs
        self.varkw = varkw


def builtin_exception(name):
    """True for a name that is a built-in exception class (`ValueError`, `KeyError`, ...)."""
    found = getattr(builtins, name, None)
    return isinstance(found, type) and issubclass(found, BaseException)


EXCEPTION_SIGNATURE = Signature([], [], True, False)   # a built-in exception takes any positional arguments and no keyword


def decorator_name(decorator):
    return ast.unparse(decorator.func if isinstance(decorator, ast.Call) else decorator)


def dataclass_options(node):
    """None when the class is not a dataclass, else its decorator keywords as {name: constant}."""
    for decorator in node.decorator_list:
        if decorator_name(decorator) in ("dataclass", "dataclasses.dataclass"):
            keywords = decorator.keywords if isinstance(decorator, ast.Call) else []
            return {keyword.arg: getattr(keyword.value, "value", None) for keyword in keywords}
    return None


class Checker:
    def __init__(self, index):
        self.index = index
        self.signatures = {}
        self.problems = []
        self.checked = 0
        self.skipped = 0
        self.reasons = Counter()

    # ---- constructors ----
    def signature_of(self, module_name, node):
        key = (module_name, node.name, node.lineno)
        if key not in self.signatures:
            self.signatures[key] = None          # a cycle reads as unknown
            self.signatures[key] = self._signature(module_name, node)
        return self.signatures[key]

    def _base_refs(self, module_name, node):
        """[(kind, ref)] per base: ("none", None) for object-like, ("class", (module, ClassDef)), or ("unknown", None)."""
        refs = []
        for base in node.bases:
            if isinstance(base, ast.Subscript):
                base = base.value
            if ast.unparse(base) in NO_INIT_BASES:
                refs.append(("none", None))
                continue
            if isinstance(base, ast.Name) and builtin_exception(base.id) and not self.is_rebound(module_name, base.id):
                refs.append(("exception", None))
                continue
            found = self.index.resolve(module_name, base)
            if found is not None and found[0] == "class":
                refs.append(("class", (found[1], found[2])))
            else:
                refs.append(("unknown", None))
        return refs

    def _signature(self, module_name, node):
        if node.keywords or any(decorator_name(d) not in PLAIN_DECORATORS for d in node.decorator_list):
            return None
        inits = [item for item in node.body if isinstance(item, ast.FunctionDef) and item.name == "__init__"]
        news = [item for item in node.body if isinstance(item, ast.FunctionDef) and item.name == "__new__"]
        for item in node.body:
            if isinstance(item, ast.Assign) and any(isinstance(t, ast.Name) and t.id in ("__init__", "__new__") for t in item.targets):
                return None
        if len(inits) > 1 or len(news) > 1 or (inits and inits[0].decorator_list) or (news and (news[0].decorator_list or inits)):
            return None
        if inits:
            return self._from_function(inits[0])
        if news:
            return self._from_function(news[0])
        options = dataclass_options(node)
        if options is not None and options.get("init") is not False:
            fields = self._dataclass_fields(module_name, node)
            return None if fields is None else self._from_fields(fields)
        if any(ast.unparse(base) in ("NamedTuple", "typing.NamedTuple") for base in node.bases):
            fields = self._own_fields(node, False)
            return self._from_fields(fields)
        for kind, ref in self._base_refs(module_name, node):
            if kind == "unknown":
                return None
            if kind == "class":
                return self.signature_of(ref[0], ref[1])
            if kind == "exception":
                return EXCEPTION_SIGNATURE
        return Signature([], [], False, False)

    @staticmethod
    def _from_function(init):
        args = init.args
        positional = [(a.arg, True, True) for a in args.posonlyargs] + [(a.arg, True, False) for a in args.args]
        positional = positional[1:]
        for i in range(len(args.defaults)):
            name, _, only = positional[len(positional) - 1 - i]
            positional[len(positional) - 1 - i] = (name, False, only)
        keyword_only = [(a.arg, default is None) for a, default in zip(args.kwonlyargs, args.kw_defaults)]
        return Signature(positional, keyword_only, args.vararg is not None, args.kwarg is not None)

    @staticmethod
    def _own_fields(node, kw_only_default):
        """[(name, has_default, kw_only, in_init)] declared in the class body, in order."""
        fields = []
        kw_only = kw_only_default
        for item in node.body:
            if not (isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name)):
                continue
            annotation = ast.unparse(item.annotation)
            if "ClassVar" in annotation:
                continue
            if annotation in ("KW_ONLY", "dataclasses.KW_ONLY"):
                kw_only = True
                continue
            has_default = item.value is not None
            in_init = True
            field_kw_only = kw_only
            value = item.value
            if isinstance(value, ast.Call) and ast.unparse(value.func) in ("field", "dataclasses.field"):
                options = {keyword.arg: getattr(keyword.value, "value", True) for keyword in value.keywords}
                has_default = "default" in options or "default_factory" in options
                in_init = options.get("init", True) is not False
                field_kw_only = options.get("kw_only", kw_only) is True
            fields.append((item.target.id, has_default, field_kw_only, in_init))
        return fields

    def _dataclass_fields(self, module_name, node):
        merged = {}
        for kind, ref in reversed(self._base_refs(module_name, node)):
            if kind == "unknown":
                return None
            if kind == "class" and dataclass_options(ref[1]) is not None:
                inherited = self._dataclass_fields(ref[0], ref[1])
                if inherited is None:
                    return None
                merged.update(inherited)
        options = dataclass_options(node)
        for name, has_default, kw_only, in_init in self._own_fields(node, options.get("kw_only") is True):
            merged[name] = (has_default, kw_only, in_init)
        return merged

    @staticmethod
    def _from_fields(fields):
        if isinstance(fields, dict):
            fields = [(name,) + values for name, values in fields.items()]
        positional = [(n, not d, False) for n, d, k, i in fields if i and not k]
        keyword_only = [(n, not d) for n, d, k, i in fields if i and k]
        return Signature(positional, keyword_only, False, False)

    # ---- calls ----
    def problem_of(self, signature, call):
        """Why `call` does not fit `signature`, or None. Returns "skip" when the call uses * or **."""
        if any(isinstance(a, ast.Starred) for a in call.args) or any(k.arg is None for k in call.keywords):
            return self.partial_problem(signature, call)
        if len(call.args) > len(signature.positional) and not signature.varargs:
            return "%d positional arguments given, the constructor takes %d" % (len(call.args), len(signature.positional))
        given = {name for name, _, _ in signature.positional[:len(call.args)]}
        allowed = {name for name, _, only in signature.positional if not only} | {name for name, _ in signature.keyword_only}
        for keyword in call.keywords:
            if keyword.arg in given:
                return "argument %s given twice" % keyword.arg
            if keyword.arg not in allowed and not signature.varkw:
                return "unexpected keyword argument %s" % keyword.arg
            given.add(keyword.arg)
        missing = [name for name, required, _ in signature.positional if required and name not in given]
        missing += [name for name, required in signature.keyword_only if required and name not in given]
        return "missing required argument%s %s" % ("s" if len(missing) > 1 else "", ", ".join(missing)) if missing else None

    def is_rebound(self, module_name, name):
        """True when the file binds `name` itself (so it is not the built-in)."""
        module = self.index.modules[module_name]
        return name in module.bound or name in module.imports or name in module.classes

    def skip(self, reason):
        self.skipped += 1
        self.reasons[reason] += 1

    def unresolved_reason(self, module, function):
        """Why a capitalised call target is not a known class: a name classification for --stats."""
        if isinstance(function, ast.Name):
            if function.id in module.imports:
                sources = {source for _, source, _ in module.imports[function.id]}
                return "imported name from %s" % ("outside sim/mods" if not any(self.index.is_module(s) for s in sources) else "a module that does not yield one class")
            if function.id in module.classes:
                return "class name defined twice or also rebound in the file"
            return "name is bound some other way or is a builtin"
        chain = function
        while isinstance(chain, ast.Attribute):
            chain = chain.value
        if isinstance(chain, ast.Name) and (chain.id in module.imports or chain.id in module.classes):
            return "attribute of an imported or local name that is not a module"
        return "attribute of a value (self., a local or a call result)"

    def unreadable_reason(self, module_name, node):
        if node.keywords:
            return "class has keywords (metaclass)"
        if any(decorator_name(d) not in PLAIN_DECORATORS for d in node.decorator_list):
            return "class has a decorator"
        if any(isinstance(item, ast.FunctionDef) and item.name == "__new__" for item in node.body):
            return "__new__ with __init__, overloaded or decorated"
        inits = [item for item in node.body if isinstance(item, ast.FunctionDef) and item.name == "__init__"]
        if len(inits) > 1 or (inits and inits[0].decorator_list):
            return "overloaded or decorated __init__"
        if any(kind == "unknown" for kind, _ in self._base_refs(module_name, node)):
            return "a base class does not resolve"
        return "other"

    def check_call(self, module, node, signature, where, class_name):
        reason = self.problem_of(signature, node)
        if reason == "skip":
            self.skip("call passes * or ** and writes out nothing to check")
            return
        self.checked += 1
        if reason:
            self.problems.append("%s:%d %s(...) is %s.%s: %s" % (module.path, node.lineno, ast.unparse(node.func), where, class_name, reason))

    def partial_problem(self, signature, call):
        """A call with `*args` or `**kwargs`: only its leading positional arguments and its written keywords can be checked.
        "skip" when it has none of either."""
        leading = []
        for argument in call.args:
            if isinstance(argument, ast.Starred):
                break
            leading.append(argument)
        written = [keyword for keyword in call.keywords if keyword.arg is not None]
        if not leading and not written:
            return "skip"
        if len(leading) > len(signature.positional) and not signature.varargs:
            return "%d positional arguments given, the constructor takes %d" % (len(leading), len(signature.positional))
        given = {name for name, _, _ in signature.positional[:len(leading)]}
        allowed = {name for name, _, only in signature.positional if not only} | {name for name, _ in signature.keyword_only}
        for keyword in written:
            if keyword.arg in given:
                return "argument %s given twice" % keyword.arg
            if keyword.arg not in allowed and not signature.varkw:
                return "unexpected keyword argument %s" % keyword.arg
            given.add(keyword.arg)
        return None

    def check_module(self, module):
        for node in ast.walk(module.tree):
            if isinstance(node, ast.Call):
                found = self.index.resolve(module.name, node.func)
                if found is None and isinstance(node.func, ast.Name) and builtin_exception(node.func.id) \
                        and not self.is_rebound(module.name, node.func.id):
                    self.check_call(module, node, EXCEPTION_SIGNATURE, "builtins", node.func.id)
                    continue
                if found is None:
                    last = node.func.id if isinstance(node.func, ast.Name) else node.func.attr if isinstance(node.func, ast.Attribute) else ""
                    if last[:1].isupper():
                        self.skip("call target does not resolve: " + self.unresolved_reason(module, node.func))
                    continue
                if found[0] != "class":
                    continue
                signature = self.signature_of(found[1], found[2])
                if signature is None:
                    self.skip("constructor unreadable: " + self.unreadable_reason(found[1], found[2]))
                    continue
                self.check_call(module, node, signature, found[1], found[2].name)
            elif isinstance(node, ast.ClassDef):
                self.check_parts(module, node)

    def check_parts(self, module, node):
        for item in node.body:
            targets = item.targets if isinstance(item, ast.Assign) else [item.target] if isinstance(item, ast.AnnAssign) else []
            if not any(isinstance(t, ast.Name) and t.id == "PARTS" for t in targets) or not isinstance(item.value, ast.Dict):
                continue
            for value in item.value.values:
                found = self.index.resolve(module.name, value)
                signature = None if found is None or found[0] != "class" else self.signature_of(found[1], found[2])
                if signature is None:
                    self.skip("PARTS entry unresolved")
                    continue
                self.checked += 1
                names = [name for name, _, _ in signature.positional]
                if signature.varargs or signature.keyword_only and any(required for _, required in signature.keyword_only):
                    reason = "takes variable or keyword-only required arguments"
                elif len(names) != 1:
                    reason = "takes (self%s), Module.build_parts calls part_class(module)" % "".join(", " + name for name in names)
                else:
                    continue
                self.problems.append("%s:%d PARTS of %s lists %s.%s, which %s" % (module.path, value.lineno, node.name, found[1], found[2].name, reason))


def main():
    index = Index()
    checker = Checker(index)
    for module in index.modules.values():
        checker.check_module(module)
    for line in index.parse_errors + sorted(checker.problems):
        print(line)
    if "--stats" in sys.argv:
        print("checked %d, skipped %d" % (checker.checked, checker.skipped))
    if "--reasons" in sys.argv:
        for reason, count in checker.reasons.most_common():
            print("  skipped %4d  %s" % (count, reason))
    sys.exit(1 if checker.problems or index.parse_errors else 0)


main()
