"""Computes one layer from the dataset option chosen for it in sim/geography/map_data_sources.py."""
from sim.geography import map_data_sources

from .catalog import LAYERS


def compute_layer(layer_id, option, tiles, side, cache_dir):
    """Values {tile id: number} from the loader of `option`, called with the source record."""
    source = map_data_sources.SOURCES[layer_id][option]
    loader = map_data_sources.loader_of(source)
    needs_side = layer_id in LAYERS and LAYERS[layer_id].needs_side  # sea_links has no catalogue entry
    arguments = (tiles, side, cache_dir) if needs_side else (tiles, cache_dir)
    return loader(*arguments, source)
