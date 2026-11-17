"""Print the twin probe's rows: per year the outcome differences and per section the differing share and sizes."""
import json, sys
path = sys.argv[1]
upto = int(sys.argv[2]) if len(sys.argv) > 2 else 8
worst_count = int(sys.argv[3]) if len(sys.argv) > 3 else 8
rows = [json.loads(line) for line in open(path)]
for row in rows[1:1 + upto]:
    print("==", row["stage"], row["year"], "outcome: differing %.3f median %.3g p90 %.3g largest %.3g" % (
        row["outcome"]["differing_share"], row["outcome"]["median"], row["outcome"]["p90"], row["outcome"]["largest"]))
    for name, section in row["sections"].items():
        if section["leaves"] and section["largest"] > 0:
            print("   %-16s leaves %7d one-side %5d differing %.3f median %.3g p90 %.3g largest %.3g" % (
                name, section["leaves"], section["only_one_side"], section["differing_share"], section["median_of_differing"],
                section["p90"], section["largest"]))
    for difference, path_name, first, second in row["outcome"]["worst"][:worst_count]:
        print("      out %.3g %s %.6g %.6g" % (difference, path_name, first, second))
    for difference, path_name, first, second in row["worst"][:worst_count]:
        print("      rec %.3g %s %.6g %.6g" % (difference, path_name[:110], first, second))
