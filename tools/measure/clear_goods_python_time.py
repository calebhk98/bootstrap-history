"""Python time under `year_goods.clear_goods` from a `warm_year_split_profile.py` profile: its cumulative time minus the time in
`kernel__` entries beneath it (a callee shared with other callers is counted in proportion to its time under this caller).

    python3 tools/measure/clear_goods_python_time.py OUT.prof"""
import pstats
import sys


def kernel_share(stats, callees, key, memo):
    """Seconds of `key`'s cumulative time spent in kernel entries beneath it."""
    if key[2].startswith("kernel__"):
        return stats[key][3]
    if key not in callees:
        return 0.0
    if key in memo:
        return memo[key]
    memo[key] = 0.0     # a call cycle counts once
    total = 0.0
    for callee, edge in callees[key].items():
        edge_cumulative, callee_cumulative = edge[3], stats[callee][3] if callee in stats else 0.0
        if callee_cumulative > 0.0:
            total += kernel_share(stats, callees, callee, memo) * min(1.0, edge_cumulative / callee_cumulative)
    memo[key] = total
    return total


def main(path):
    profile = pstats.Stats(path)
    stats = profile.stats
    profile.calc_callees()
    root = next(key for key in stats if key[2] == "clear_goods")
    cumulative = stats[root][3]
    kernels = kernel_share(stats, profile.all_callees, root, {})
    print("clear_goods cumulative %.3f kernels %.3f python %.3f" % (cumulative, kernels, cumulative - kernels))


if __name__ == "__main__":
    main(sys.argv[1])
