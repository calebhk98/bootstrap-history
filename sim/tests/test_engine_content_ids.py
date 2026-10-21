"""engine_content_ids: the engine reads node `mechanics`, never node ids (CLAUDE.md 4.7). No string literal in engine or world
code equals a technology node id. A scan of every engine and world module, so it is not in the quick tier; the engine
reading declared mechanics in a game is `test_engine_content_ids_scenario`, and the mechanics data checks are
`test_mechanics_documented`."""
import ast
from .harness import *  # noqa: F401,F403

# --- No string literal in engine or world code may equal a technology node id.
# ALLOWED holds the only exceptions, each with the reason it is not a node reference.
ALLOWED = {
    # GOODS_CATEGORIES key: a market category that shares its name with a tree node.
    ("sim/engine/economy_goods.py", "photography"),
}
_found = []
from .source_dirs import engine_and_world_dirs
for _directory in engine_and_world_dirs():
    for _path in sorted(glob.glob(os.path.join(_directory, "**", "*.py"), recursive=True)):
        _relative = os.path.relpath(_path, ROOT)
        _tree = ast.parse(open(_path, encoding="utf-8").read())
        for _node in ast.walk(_tree):
            if (isinstance(_node, ast.Constant) and isinstance(_node.value, str)
                    and _node.value in NODES and (_relative, _node.value) not in ALLOWED):
                _found.append("%s:%d %s" % (_relative, _node.lineno, _node.value))
check("no engine or world module names a technology node id in a string literal",
      not _found, _found[:10])

