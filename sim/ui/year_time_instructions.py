"""`year-time --count-instructions`: user-space instructions per simulated year, counted under valgrind's cachegrind.

Load-independent: the count does not move with the machine's speed or its other work. Python cannot issue valgrind client
requests, so each year is found by difference: the game is loaded and stepped k years in a child process for k = 0..years,
each under cachegrind, and year k is run k minus run k-1 (interpreter start, import and load cancel). The child's hash seed
is fixed, so set order is the same every run.

Valgrind reports a different CPU to numba than the real one, which would miss numba's on-disk kernel cache and recompile every
kernel under valgrind (an hour). So the children run with numba's generic CPU target, and the kernels for that target are
compiled once, natively, before counting. The count is therefore of generic-target machine code, the same on every machine.
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile

from sim.refusal import Refusal

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SUMMARY_LINE = re.compile(r"^summary:\s+(\d+)", re.MULTILINE)


def valgrind_refusal(valgrind_path):
    """A Refusal naming why the count cannot be made, or None when valgrind was found."""
    if valgrind_path is None:
        return Refusal("valgrind_missing", "--count-instructions needs valgrind on the PATH, and none was found; "
                       "install it (for example apt-get install valgrind) or measure wall time instead")
    return None


def total_instructions(output_text):
    """The instruction total of a cachegrind output file's text (its `summary:` line); None when there is none."""
    match = SUMMARY_LINE.search(output_text)
    return int(match.group(1)) if match else None


def per_year_instructions(totals):
    """(instructions of the load, instructions of each stepped year) from the totals of runs that step 0, 1, 2, ... years."""
    return totals[0], [later - earlier for earlier, later in zip(totals, totals[1:])]


def split_first_and_warm(per_year):
    """(first stepped year, later years): the first includes loading cached kernels."""
    return per_year[0], per_year[1:]


def counting_environment():
    """The child's environment: a fixed hash seed, numba's generic CPU target so its kernel cache is the same under valgrind,
    and one thread everywhere (threads that spin while waiting execute a varying number of instructions)."""
    single_thread = {name: "1" for name in ("NUMBA_NUM_THREADS", "OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS")}
    return dict(os.environ, PYTHONHASHSEED="0", NUMBA_CPU_NAME="generic", **single_thread)


def warm_kernel_cache():
    """Compile (natively, once; a no-op when cached) the kernels for the generic target the counted children use."""
    command = [sys.executable, os.path.join(REPO_ROOT, "sim", "simulator.py"), "compile-kernels"]
    subprocess.run(command, cwd=REPO_ROOT, env=counting_environment(), check=True, stdout=subprocess.DEVNULL)


def counted_run(session, years_stepped, directory):
    """Instructions of one child run (load the save, step `years_stepped` years) under cachegrind; None if it gave no total."""
    out_file = os.path.join(directory, "cachegrind_%d.out" % years_stepped)
    environment = counting_environment()
    command = ["valgrind", "--tool=cachegrind", "--cache-sim=no", "--cachegrind-out-file=" + out_file,
               sys.executable, "-m", "sim.ui.year_time_instructions", session, str(years_stepped)]
    subprocess.run(command, cwd=REPO_ROOT, env=environment, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    with open(out_file, encoding="utf-8") as handle:
        return total_instructions(handle.read())


def count_instructions(session, years):
    """A Refusal, or the report fields: instructions of the load, of the first stepped year and of each warm year."""
    refusal = valgrind_refusal(shutil.which("valgrind"))
    if refusal is not None:
        return refusal
    warm_kernel_cache()
    with tempfile.TemporaryDirectory(prefix="year_time_instructions_") as directory:
        totals = [counted_run(os.path.abspath(session), stepped, directory) for stepped in range(years + 1)]
    if None in totals:
        return Refusal("no_instruction_total", "cachegrind wrote no summary line, so no count was made")
    load, per_year = per_year_instructions(totals)
    first, warm = split_first_and_warm(per_year)
    return {"instructions_load": load, "instructions_per_year": per_year,
            "instructions_first_year": first, "instructions_warm_years": warm}


def _child(session, years_stepped):
    from sim.engine.ui_port import load
    from .cli_year_time import loaded
    _tree, _prices, nodes, _wages, _goods = load()
    game = loaded(session, nodes)
    for _year in range(years_stepped):
        game.step()


if __name__ == "__main__":
    _child(sys.argv[1], int(sys.argv[2]))
