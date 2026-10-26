"""Pure pieces of the equivalence tool: flatten a saved state, relocate and drop paths, hash by section, diff."""
import hashlib, json

SEPARATOR = "/"
LOG_MARKER = "__log_line__"
ABSENT = "<absent>"


def leaf_text(value):
    """Canonical text of a scalar: floats by repr so a last-bit change shows."""
    return repr(value) if isinstance(value, float) else json.dumps(value)


def flatten(node, path="", leaves=None):
    """{path: canonical leaf text}. Keys sorted, empty containers kept as leaves; a log record keeps its kind and
    facts and loses its prose `text`."""
    leaves = {} if leaves is None else leaves
    if isinstance(node, dict):
        if not node:
            leaves[path] = "{}"
        is_log = LOG_MARKER in node
        for key in sorted(node, key=str):
            if is_log and key == "text":
                continue
            flatten(node[key], path + SEPARATOR + str(key), leaves)
    elif isinstance(node, (list, tuple)):
        if not node:
            leaves[path] = "[]"
        for index, item in enumerate(node):
            flatten(item, path + SEPARATOR + str(index), leaves)
    else:
        leaves[path] = leaf_text(node)
    return leaves


def under(path, prefix):
    return path == prefix or path.startswith(prefix + SEPARATOR)


def relocate(leaves, relocations):
    """Leaves with every path rewritten by each (old_prefix, new_prefix) in order."""
    if not relocations:
        return leaves
    moved = {}
    for path, value in leaves.items():
        for old_prefix, new_prefix in relocations:
            if under(path, old_prefix):
                path = new_prefix + path[len(old_prefix):]
        moved[path] = value
    return moved


def drop_ignored(leaves, ignored):
    """Leaves without any path under an ignored (prefix, reason) pair."""
    prefixes = [prefix for prefix, _reason in ignored]
    if not prefixes:
        return leaves
    return {path: value for path, value in leaves.items() if not any(under(path, prefix) for prefix in prefixes)}


def section_of(path):
    return path.split(SEPARATOR, 2)[1] if path.startswith(SEPARATOR) and len(path) > 1 else ""


def section_hashes(leaves):
    """{top-level section: short hash of its sorted (path, value) lines}."""
    grouped = {}
    for path, value in leaves.items():
        grouped.setdefault(section_of(path), []).append(path + "=" + value)
    return {section: hashlib.sha256("\n".join(sorted(lines)).encode()).hexdigest()[:12]
            for section, lines in sorted(grouped.items())}


def rng_hash(rng_record):
    return hashlib.sha256(json.dumps(rng_record).encode()).hexdigest()[:12]


def differing_sections(base_hashes, current_hashes):
    """Sorted names of sections whose hash differs or that exist on one side only."""
    return sorted(name for name in set(base_hashes) | set(current_hashes)
                  if base_hashes.get(name) != current_hashes.get(name))


def diff_leaves(base_leaves, current_leaves, limit=20, sections=None):
    """(first `limit` of [(path, base value, current value)] sorted by path, total differing).
    A leaf missing on one side reads ABSENT. `sections` narrows the comparison."""
    differing = sorted(path for path in set(base_leaves) | set(current_leaves)
                       if (sections is None or section_of(path) in sections)
                       and base_leaves.get(path) != current_leaves.get(path))
    shown = [(path, base_leaves.get(path, ABSENT), current_leaves.get(path, ABSENT)) for path in differing[:limit]]
    return shown, len(differing)
