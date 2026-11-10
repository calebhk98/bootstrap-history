"""How many numpy calls a warm year makes under each function, per call of that function. Run from the repository root:

    python3 tools/measure/numpy_calls_per_good.py SAVE.json [TOP]

A call is a call into numpy from code outside numpy (a numpy function that calls others counts once; a method of an array
counts; a compiled kernel does not). Each call is charged to every `sim` function on the stack, so a function's figure includes
what it calls. The last lines give `clear_good`'s figure (one call per good) per call. Run it with `ROME_NO_JIT` unset."""
import collections
import sys

sys.path.insert(0, ".")
from tools.measure.warm_year_profile import warmed_game   # noqa: E402


def main(save_path, top):
    game = warmed_game(save_path)
    inclusive, calls = collections.Counter(), collections.Counter()
    stack = []                    # one entry per Python frame: the sim function's name, or None
    state = {"numpy_depth": 0}

    def charge():
        for name in {each for each in stack if each}:
            inclusive[name] += 1

    def hook(frame, event, argument):
        if event == "call":
            filename = frame.f_code.co_filename
            if "site-packages/numpy" in filename:
                if state["numpy_depth"] == 0:
                    charge()
                state["numpy_depth"] += 1
                stack.append(None)
            elif "/sim/" in filename and state["numpy_depth"] == 0:
                name = "%s:%s" % (filename.split("/sim/")[-1], frame.f_code.co_name)
                stack.append(name)
                calls[name] += 1
            else:
                stack.append(None)
        elif event == "return":
            if stack:
                popped = stack.pop()
                if popped is None and "site-packages/numpy" in frame.f_code.co_filename:
                    state["numpy_depth"] -= 1
        elif event == "c_call" and state["numpy_depth"] == 0:
            owner = getattr(argument, "__self__", None)
            module = getattr(argument, "__module__", None) or ""
            if module.startswith("numpy") or type(owner).__module__ == "numpy":
                charge()

    import threading
    sys.setprofile(hook)
    threading.setprofile(hook)
    game.step()
    sys.setprofile(None)
    for name, number in inclusive.most_common(top):
        print("%8d %7d %8.1f  %s" % (number, calls[name], number / max(calls[name], 1), name))
    key = "economy/goods_good_clear.py:clear_good"
    print("numpy calls per call of clear_good: %.1f over %d goods" % (inclusive[key] / max(calls[key], 1), calls[key]))


if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 40)
