"""Shared static index of the classes under sim/ and mods/ (tests excluded) and of what each file's names refer to.
Used by tools/check_constructor_calls.py and tools/check_class_names.py; it imports nothing from sim/ and runs nothing.

A name resolves to a class only when it is unambiguous in its file: bound once (one class definition or one import, not also
a parameter, a local variable, a function or a second definition). Anything else resolves to None and callers skip it."""
import ast
import glob
import os

ROOTS = ("sim", "mods")


def module_name_of(path):
    parts = path[:-3].split("/")
    if parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


class ModuleInfo:
    def __init__(self, path, tree):
        self.path = path
        self.name = module_name_of(path)
        self.is_package = os.path.basename(path) == "__init__.py"
        self.tree = tree
        self.classes = {}      # name -> [ClassDef] defined at module level (also inside module-level if/try)
        self.imports = {}      # name -> {(kind, source, original)}; kind is "from" or "import"; anywhere in the file
        self.stars = []        # modules star-imported
        self.bound = set()     # names bound some other way: parameters, assignments, functions, nested classes
        self._visit(tree.body, top=True)
        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and isinstance(node.ctx, (ast.Store, ast.Del)):
                self.bound.add(node.id)
            elif isinstance(node, ast.arg):
                self.bound.add(node.arg)
            elif isinstance(node, ast.ExceptHandler) and node.name:
                self.bound.add(node.name)

    def _visit(self, body, top):
        for node in body:
            if isinstance(node, ast.ClassDef):
                if top:
                    self.classes.setdefault(node.name, []).append(node)
                else:
                    self.bound.add(node.name)
                self._visit(node.body, top=False)
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self.bound.add(node.name)
                self._visit(node.body, top=False)
            elif isinstance(node, ast.ImportFrom):
                source = self._absolute(node.level, node.module)
                for alias in node.names:
                    if alias.name == "*":
                        self.stars.append(source)
                    else:
                        self.imports.setdefault(alias.asname or alias.name, set()).add(("from", source, alias.name))
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.asname:
                        self.imports.setdefault(alias.asname, set()).add(("import", alias.name, None))
                    else:
                        first = alias.name.split(".")[0]
                        self.imports.setdefault(first, set()).add(("import", first, None))
            else:
                inner = []
                for field in ("body", "orelse", "finalbody"):
                    inner += [item for item in getattr(node, field, None) or [] if isinstance(item, ast.stmt)]
                for handler in getattr(node, "handlers", None) or []:
                    inner += handler.body
                self._visit(inner, top)

    def _absolute(self, level, module):
        if level == 0:
            return module
        base = self.name.split(".")
        if not self.is_package:
            base = base[:-1]
        if level > 1:
            base = base[:len(base) - (level - 1)]
        return ".".join(base + ([module] if module else []))


class Index:
    def __init__(self, root="."):
        self.modules = {}
        self.parse_errors = []
        for top in ROOTS:
            for path in sorted(glob.glob(os.path.join(root, top, "**", "*.py"), recursive=True)):
                relative = os.path.relpath(path, root).replace(os.sep, "/")
                if "/tests/" in "/" + relative:
                    continue
                try:
                    with open(path, encoding="utf-8") as handle:
                        tree = ast.parse(handle.read())
                except (SyntaxError, UnicodeDecodeError) as error:
                    self.parse_errors.append("%s: cannot parse (%s)" % (relative, error))
                    continue
                info = ModuleInfo(relative, tree)
                self.modules[info.name] = info
        self.prefixes = {".".join(name.split(".")[:i]) for name in self.modules for i in range(1, len(name.split(".")))}

    def is_module(self, name):
        return name in self.modules or name in self.prefixes

    def follow(self, module_name, name, seen=None):
        """What `name` means inside `module_name`: ("class", module_name, ClassDef), ("module", module_name) or None."""
        seen = seen if seen is not None else set()
        module = self.modules.get(module_name)
        if module is None or (module_name, name) in seen:
            return None
        seen.add((module_name, name))
        if name in module.classes:
            if len(module.classes[name]) == 1 and name not in module.bound and name not in module.imports:
                return ("class", module_name, module.classes[name][0])
            return None
        if name in module.imports:
            if len(module.imports[name]) != 1 or name in module.bound:
                return None
            kind, source, original = next(iter(module.imports[name]))
            if kind == "import":
                return ("module", source) if self.is_module(source) else None
            found = self.follow(source, original, seen)
            if found is not None:
                return found
            submodule = "%s.%s" % (source, original)
            return ("module", submodule) if self.is_module(submodule) else None
        if name in module.bound:
            return None
        for source in module.stars:
            found = self.follow(source, name, seen)
            if found is not None:
                return found
        return None

    def resolve(self, module_name, expression):
        """The class or module a Name / dotted Attribute expression in `module_name` refers to, else None."""
        if isinstance(expression, ast.Name):
            return self.follow(module_name, expression.id)
        if isinstance(expression, ast.Attribute):
            base = self.resolve(module_name, expression.value)
            if base is None or base[0] != "module":
                return None
            found = self.follow(base[1], expression.attr)
            if found is not None:
                return found
            submodule = "%s.%s" % (base[1], expression.attr)
            return ("module", submodule) if self.is_module(submodule) else None
        return None
