"""Regression coverage for placeholder markers in the population screen
(complaint 172). Trades with placeholder density estimates show an asterisk marker."""
from .harness import *

_SIMULATOR = os.path.join(HERE, "simulator.py")
_scratch = tempfile.mkdtemp()


def _env(name, config=None):
    saves = os.path.join(_scratch, name)
    os.makedirs(saves, exist_ok=True)
    config_file = os.path.join(_scratch, name + "-config.json")
    if config is not None:
        with open(config_file, "w") as handle:
            json.dump(config, handle)
    env = dict(os.environ, ROME_SAVE_DIR=saves, ROME_SIM_CONFIG=config_file)
    env.pop("ROME_DEFAULT_SEED", None)
    return saves, env


def _run(arguments, text, env, cwd=None):
    return subprocess.run([sys.executable, _SIMULATOR] + arguments, input=text,
                          capture_output=True, text=True, timeout=120, env=env, cwd=cwd)


def _get_population_text(name):
    """Run population command and get the rendered text output."""
    saves, env = _env(name)
    session = os.path.join(saves, "test.json")
    result = _run(["play", "--civ", "rome_100ad", "--seed", "1", "--session", session],
                  "population\nquit\n", env)
    lines = result.stdout.split('\n')
    in_population = False
    population_lines = []
    for line in lines:
        if 'POPULATION:' in line:
            in_population = True
            population_lines.append(line)
        elif in_population:
            if line.strip().startswith('[') and 'AD' in line:
                break
            population_lines.append(line)
    return '\n'.join(population_lines)


# Test 1: Population screen contains table with trades
text_output = _get_population_text("test_output")
check("population: output contains POPULATION header", "POPULATION:" in text_output,
      text_output[:200])
check("population: output contains trade table header", "TRADE" in text_output and "IN THE COUNTRY" in text_output,
      text_output[:500])

# Test 2: Known placeholder trades have asterisk marker
placeholder_trades = ("engraver", "glassblower", "master", "millwright", "chemist",
                     "electrician", "engineer", "machinist", "optician", "merchant",
                     "scholar", "scribe")
if text_output:
    marked_placeholders = []
    for trade in placeholder_trades:
        if trade in text_output:
            # Find the line with this trade
            for line in text_output.split('\n'):
                if trade in line.lower():
                    if line.strip() and line.strip()[0].isalpha():
                        # This is a trade line (not a header or note)
                        if "*" in line:
                            marked_placeholders.append(trade)
                    break

    check("population: placeholder trades show asterisk marker",
          len(marked_placeholders) >= 5,
          "found %d placeholder trades with marker: %s" % (len(marked_placeholders), marked_placeholders))

# Test 3: Non-placeholder common trades do not have asterisk
non_placeholder_trades = ("artisan", "carpenter", "furnaceman", "labourer", "miner",
                         "potter", "smith", "mason", "plumber", "sailor")
if text_output:
    unmarked_non_placeholders = []
    for trade in non_placeholder_trades:
        if trade in text_output:
            for line in text_output.split('\n'):
                if trade in line.lower():
                    if line.strip() and line.strip()[0].isalpha():
                        # Check if first word is the trade name without asterisk
                        first_word = line.split()[0].lower()
                        if trade in first_word and not first_word.endswith("*"):
                            unmarked_non_placeholders.append(trade)
                    break

    check("population: non-placeholder trades do not show asterisk",
          len(unmarked_non_placeholders) >= 5,
          "found %d non-placeholder trades without marker: %s" % (len(unmarked_non_placeholders), unmarked_non_placeholders))

# Test 4: Legend line explains the asterisk marker
has_legend = "* =" in text_output and "placeholder" in text_output.lower()
check("population: has legend line for asterisk marker",
      has_legend,
      text_output.split('\n')[-15:] if has_legend else text_output[-500:])

# Test 5: Verify is_placeholder consistency with REGISTRY
# This test imports the engine and checks that is_placeholder matches the
# kind field of the constant that computes the trade's density, so the
# answer stays in sync with declarations rather than being hand-copied.
from ..engine.labour_population import PopulationMixin
from ..constants import REGISTRY
from .harness import *

# Create a minimal test sim instance
test_sim = sim(civ="rome_100ad")
pop_report = test_sim.population_report()
trades = pop_report.get("trades", [])

is_placeholder_mismatches = []
for trade_row in trades:
    trade = trade_row.get("trade")
    is_placeholder = trade_row.get("is_placeholder")

    # Get the source constant name
    source_name = test_sim._trade_density_source(trade)

    if source_name is None:
        # Taught trades or unavailable trades have no source
        expected_placeholder = False
    elif source_name not in REGISTRY:
        expected_placeholder = False
    else:
        expected_placeholder = REGISTRY[source_name].get("kind") == "temporary_heuristic"

    if is_placeholder != expected_placeholder:
        is_placeholder_mismatches.append({
            "trade": trade,
            "source": source_name,
            "reported_is_placeholder": is_placeholder,
            "expected_from_registry": expected_placeholder,
        })

check("population: is_placeholder field matches REGISTRY kind for all trades",
      len(is_placeholder_mismatches) == 0,
      is_placeholder_mismatches if is_placeholder_mismatches else "all trades consistent")
