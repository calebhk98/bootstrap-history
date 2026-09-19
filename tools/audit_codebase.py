"""Unified non-blocking diagnostic runner for repository code health.

Runs Semgrep, Import-Linter, Mypy, Lizard, and JSCPD strictly in diagnostic/
reporting mode. Never exits with non-zero code or blocks workflows.
"""

import argparse
import os
import subprocess
import sys

# Ensure UTF-8 output encoding on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
	try:
		sys.stdout.reconfigure(encoding="utf-8", errors="replace")
	except Exception as encoding_err:
		pass

DEFAULT_TIMEOUT_SECONDS = 180
DEFAULT_COMPLEXITY_THRESHOLD = 15
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)


def safe_print(text):
	"""Prints text safely without raising UnicodeEncodeError on Windows."""
	try:
		print(text)
	except UnicodeEncodeError:
		encoded = text.encode(sys.stdout.encoding or "ascii", errors="replace")
		print(encoded.decode(sys.stdout.encoding or "ascii", errors="replace"))


def run_command(command, description, timeout=DEFAULT_TIMEOUT_SECONDS):
	"""Runs a CLI command and returns its output, handling errors gracefully."""
	safe_print(f"\n{'=' * 60}")
	safe_print(f"--- {description} ---")
	safe_print(f"Command: {' '.join(command)}")
	safe_print(f"{'=' * 60}\n")
	try:
		process = subprocess.run(
			command,
			cwd=REPO_ROOT,
			capture_output=True,
			text=True,
			timeout=timeout,
			encoding="utf-8",
			errors="replace"
		)
		output = process.stdout.strip()
		if output:
			safe_print(output)
		if process.stderr.strip():
			safe_print(f"\n[STDERR]\n{process.stderr.strip()}")
		return {
			"description": description,
			"returncode": process.returncode,
			"stdout": output,
			"stderr": process.stderr.strip()
		}
	except subprocess.TimeoutExpired:
		safe_print(f"[TIMEOUT] {description} timed out after {timeout} seconds.")
		return {
			"description": description,
			"returncode": -1,
			"stdout": "",
			"stderr": f"Timed out after {timeout}s"
		}
	except Exception as err:
		safe_print(f"[ERROR] Failed to run {description}: {err}")
		return {
			"description": description,
			"returncode": -1,
			"stdout": "",
			"stderr": str(err)
		}


def _find_binary(binary_name):
	"""Finds binary in Python Scripts directory or fallback to system PATH."""
	scripts_dir = os.path.join(os.path.dirname(sys.executable), "Scripts")
	candidate = os.path.join(scripts_dir, f"{binary_name}.exe")
	if os.path.exists(candidate):
		return candidate
	candidate_no_ext = os.path.join(scripts_dir, binary_name)
	if os.path.exists(candidate_no_ext):
		return candidate_no_ext
	return binary_name


def run_semgrep():
	"""Runs Semgrep with local custom rules (.semgrep/rules.yaml)."""
	exe = _find_binary("semgrep")
	cmd = [exe, "scan", "--config", ".semgrep/rules.yaml", "sim/"]
	return run_command(cmd, "Semgrep Custom Architecture Rules")


def run_import_linter():
	"""Runs Import-Linter to check boundary contracts."""
	exe = _find_binary("lint-imports")
	cmd = [exe]
	return run_command(cmd, "Import-Linter Layer Boundary Contracts")


def run_mypy():
	"""Runs Mypy with existing repo configuration."""
	exe = _find_binary("mypy")
	cmd = [exe, "--config-file", "mypy.ini"]
	return run_command(cmd, "Mypy Type Checking (Permissive Baseline)")


def run_lizard(threshold=DEFAULT_COMPLEXITY_THRESHOLD):
	"""Runs Lizard to check cyclomatic complexity and function length."""
	exe = _find_binary("lizard")
	cmd = [
		exe,
		"-C", str(threshold),
		"-w",
		"-x", "*/tests/*",
		"sim/"
	]
	return run_command(cmd, f"Lizard Cyclomatic Complexity (CCN > {threshold})")


def run_jscpd():
	"""Runs JSCPD via npx for token-based clone detection."""
	npx_cmd = "npx.cmd" if sys.platform == "win32" else "npx"
	cmd = [npx_cmd, "jscpd", "sim/", "--config", ".jscpd.json"]
	return run_command(cmd, "JSCPD Token-Based Clone Detection")


def main():
	parser = argparse.ArgumentParser(
		description="Run non-blocking diagnostic tools to inspect debt and compare metrics."
	)
	parser.add_argument("--all", action="store_true", help="Run all diagnostic tools")
	parser.add_argument("--semgrep", action="store_true", help="Run Semgrep custom rules")
	parser.add_argument("--imports", action="store_true", help="Run Import-Linter")
	parser.add_argument("--mypy", action="store_true", help="Run Mypy")
	parser.add_argument("--lizard", action="store_true", help="Run Lizard complexity scanner")
	parser.add_argument("--clones", action="store_true", help="Run JSCPD clone detector")
	parser.add_argument(
		"--threshold",
		type=int,
		default=DEFAULT_COMPLEXITY_THRESHOLD,
		help=f"Lizard complexity threshold (default: {DEFAULT_COMPLEXITY_THRESHOLD})"
	)

	args = parser.parse_args()

	# If no specific tool is flagged, default to running all
	run_all = args.all or not (args.semgrep or args.imports or args.mypy or args.lizard or args.clones)

	print("Starting non-blocking codebase diagnostic pass...")
	results = []

	if run_all or args.semgrep:
		results.append(run_semgrep())

	if run_all or args.imports:
		results.append(run_import_linter())

	if run_all or args.mypy:
		results.append(run_mypy())

	if run_all or args.lizard:
		results.append(run_lizard(args.threshold))

	if run_all or args.clones:
		results.append(run_jscpd())

	print("\n" + "=" * 60)
	print("DIAGNOSTIC PASS COMPLETE (Non-blocking: exit code 0)")
	print("=" * 60)
	for res in results:
		status = "SUCCESS" if res["returncode"] == 0 else f"FINDINGS / CODE {res['returncode']}"
		print(f"- {res['description']}: {status}")

	return 0


if __name__ == "__main__":
	sys.exit(main())
