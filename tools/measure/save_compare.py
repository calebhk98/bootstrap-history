"""Compare two saves of one game (for example the same save stepped by two builds): the count of leaves that differ and
the largest relative difference of numeric leaves, by top-level part, then the first differing paths. Run:

    python3 tools/measure/save_compare.py FIRST.json SECOND.json

A port that only reorders float sums shows last-digit differences; a game that diverges through discrete rules shows many
leaves and a largest relative difference near two (a value against its opposite or zero)."""
import collections
import json
import math
import sys


def compare(first, second):
    counts = collections.Counter()
    largest = collections.defaultdict(float)
    examples = []

    def walk(one, other, path, part):
        if isinstance(one, dict) and isinstance(other, dict):
            for key in set(one) | set(other):
                where = part or str(key)
                if key not in one or key not in other:
                    counts[where] += 1
                    examples.append((path + "/" + str(key), "missing on one side"))
                    continue
                walk(one[key], other[key], path + "/" + str(key), where)
        elif isinstance(one, list) and isinstance(other, list):
            if len(one) != len(other):
                counts[part] += 1
                examples.append((path, "length %d against %d" % (len(one), len(other))))
                return
            for index, (left, right) in enumerate(zip(one, other)):
                walk(left, right, "%s[%d]" % (path, index), part)
        elif isinstance(one, (int, float)) and isinstance(other, (int, float)) and not isinstance(one, bool):
            if one != other:
                counts[part] += 1
                scale = max(abs(one), abs(other), 1e-300)
                largest[part] = max(largest[part], abs(one - other) / scale if math.isfinite(scale) else math.inf)
                examples.append((path, "%r against %r" % (one, other)))
        elif one != other:
            counts[part] += 1
            examples.append((path, "%r against %r" % (str(one)[:40], str(other)[:40])))

    walk(first, second, "", None)
    return counts, largest, examples


def main(first_path, second_path):
    with open(first_path, encoding="utf-8") as handle:
        first = json.load(handle)
    with open(second_path, encoding="utf-8") as handle:
        second = json.load(handle)
    counts, largest, examples = compare(first, second)
    print("differing leaves", sum(counts.values()))
    for part in sorted(counts, key=str):
        print("  %-30s %8d  largest relative difference %.3g" % (part, counts[part], largest[part]))
    for path, what in examples[:15]:
        print("  ", path[:140], what[:100])


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
