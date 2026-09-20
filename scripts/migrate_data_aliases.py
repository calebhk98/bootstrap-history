#!/usr/bin/env python3
"""Canonicalise labour and commodity identifiers in source JSON data.

The alias table is migration input, not an engine/build-time compatibility
layer.  Only identifier-bearing schema mappings are rewritten: prose and
technology ids such as ``requires_node`` are deliberately left untouched.
"""
import argparse
import json
from pathlib import Path


IDENTIFIER_MAP_FIELDS = {
    "lab", "mat", "inputs", "outputs", "labour_hours",
    "build_materials", "build_labour_hours",
}


def canonicalise_mapping(mapping, aliases, source):
    result = {}
    for old_key, value in mapping.items():
        new_key = aliases.get(old_key, old_key)
        if new_key in result:
            if isinstance(result[new_key], (int, float)) and isinstance(value, (int, float)):
                result[new_key] += value
                continue
            if result[new_key] != value:
                raise ValueError(
                    f"{source}: canonical key {new_key!r} has conflicting values")
        else:
            result[new_key] = value
    return result


def canonicalise(value, aliases, source, parent_key=None):
    if isinstance(value, list):
        return [canonicalise(item, aliases, source) for item in value]
    if not isinstance(value, dict):
        return value

    rewritten = {
        key: canonicalise(item, aliases, source, key)
        for key, item in value.items()
    }
    if parent_key in IDENTIFIER_MAP_FIELDS:
        rewritten = canonicalise_mapping(rewritten, aliases, source)
    # Production files key their top-level recipe table by material id.
    if parent_key == "materials":
        rewritten = canonicalise_mapping(rewritten, aliases, source)
    return rewritten


def migrate(root, aliases_path, check=False):
    aliases = json.loads(aliases_path.read_text())["alias"]
    changed = []
    for directory in (root / "data" / "branches", root / "data" / "production"):
        for path in sorted(directory.glob("*.json")):
            if path == aliases_path:
                continue
            original = json.loads(path.read_text())
            updated = canonicalise(original, aliases, path)
            if updated != original:
                changed.append(path)
                if not check:
                    path.write_text(json.dumps(updated, indent=1) + "\n")
    return changed


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true",
                        help="fail if deprecated identifiers remain")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    aliases_path = root / "data" / "branches" / "ALIASES.json"
    changed = migrate(root, aliases_path, check=args.check)
    if args.check and changed:
        for path in changed:
            print(path.relative_to(root))
        raise SystemExit(1)
    print(f"canonicalised {len(changed)} file(s)")


if __name__ == "__main__":
    main()
