"""first_year_probe.py with the experiment switches of ablations.py applied first. Usage: ABLATE=name python3 first_year_ablate.py <probe.py> <civ> [years]"""
import os, runpy, sys
import ablations
ablations.apply(os.environ["ABLATE"])
sys.argv = sys.argv[1:]
runpy.run_path(sys.argv[0], run_name="__main__")
