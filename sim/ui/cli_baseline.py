"""`baseline-ensemble`: play several unplayed games of a civilisation and store their distributions (Complaints/266)."""
from sim.engine import baseline_ensemble
from sim.engine.ui_port import default_civilisation_id


def cmd_baseline_ensemble(args, runner=None):
    """Run `--seeds` baseline games of `--civ` for `--years` years and write the cache the divergence screen reads."""
    civilisation_id = args.civ or default_civilisation_id()
    seeds = list(range(1, args.seeds + 1))
    ensemble = baseline_ensemble.run_ensemble(civilisation_id, seeds, args.years, runner=runner, jobs=args.jobs)
    path = baseline_ensemble.write_cache(ensemble, getattr(args, "directory", None))
    print("%s: %d runs, %d years, written to %s" % (civilisation_id, ensemble["runs"], ensemble["years"], path))
    for metric, bands in ensemble["metrics"].items():
        print("  %-18s start %s, median at the end %s (p10 %s, p90 %s)" % (
            metric, "%.4g" % bands["median"][0], "%.4g" % bands["median"][-1],
            "%.4g" % bands["p10"][-1], "%.4g" % bands["p90"][-1]))
    return 0
