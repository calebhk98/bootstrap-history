"""CLI: python3 -m sim.geography.layer_build [--layers a,b] [--cache DIR]"""
import argparse
import json
import os
import statistics
import time

from .cache import DEFAULT_CACHE
from .catalog import LAYERS
from .tiles import load_tiles

LAYER_DIRECTORY = os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "data", "world", "geography", "layers")


def write_layer(layer_id, layer, values, directory):
    """One file per layer, one tile per line, sorted ids."""
    header = {"_doc": layer.doc, "id": layer_id, "unit": layer.unit, "source": layer.source,
              "method": layer.method, "conf": layer.conf}
    lines = ["{"] + ["%s: %s," % (json.dumps(key), json.dumps(value)) for key, value in header.items()]
    lines.append('"values": {')
    entries = ["  %s: %s" % (json.dumps(tile_id), json.dumps(round(values[tile_id], layer.decimals) if layer.decimals else int(round(values[tile_id]))))
               for tile_id in sorted(values)]
    lines.append(",\n".join(entries))
    lines.append("}\n}\n")
    with open(os.path.join(directory, layer_id + ".json"), "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--layers", help="comma-separated layer ids (default: all)")
    parser.add_argument("--cache", default=DEFAULT_CACHE, help="download cache directory")
    options = parser.parse_args()
    wanted = options.layers.split(",") if options.layers else list(LAYERS)
    unknown = [layer_id for layer_id in wanted if layer_id not in LAYERS]
    if unknown:
        parser.error("unknown layers: %s (known: %s)" % (", ".join(unknown), ", ".join(LAYERS)))
    start = time.time()
    tiles, side = load_tiles(options.cache)
    print("%d tiles, cell side %.1f km (%.0fs)" % (len(tiles), side / 1000.0, time.time() - start))
    os.makedirs(LAYER_DIRECTORY, exist_ok=True)
    for layer_id in wanted:
        layer = LAYERS[layer_id]
        stage = time.time()
        arguments = (tiles, side, options.cache) if layer.needs_side else (tiles, options.cache)
        values = layer.compute(*arguments)
        write_layer(layer_id, layer, values, LAYER_DIRECTORY)
        numbers = sorted(values.values())
        print("%-30s min %10.2f  median %10.2f  max %10.2f  (%.0fs)" % (
            layer_id, numbers[0], statistics.median(numbers), numbers[-1], time.time() - stage))
    print("total %.0fs" % (time.time() - start))


if __name__ == "__main__":
    main()
