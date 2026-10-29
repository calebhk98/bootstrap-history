"""The content package's only door: the mod loader (manifests, ids, removals, civilisations, world data, constants,
strategies), the tree's field defaults and the household need data."""

WALL = "two-way"  # nothing here imports sim/engine/; the engine and the front ends ask for the mods of a directory they name

from .mods import MANIFEST_KEYS, get_ordered_mods, load_mod_production, load_mod_tree
from .mods_base import (MissingVariantBase, ModError, ModManifest, ancestors, check_not_removed, claim_fields, claim_removal,
                        deep_merge)
from .mods_civ import (SEPARATOR, apply_mod_civilization, check_all_civilizations, check_starting_techs, is_hidden,
                       mod_civ_ids)
from .mods_constants import apply_override, constant_overrides
from .mods_ids import MOD_ID_PATTERN, check_new_id, is_mod_content
from .mods_remove import RECIPE, TRADE, check_trade_references, scan_removed
from .mods_strategies import mod_strategy_names, mod_strategy_path
from .mods_world import merge_mod_list, merge_mod_map
from .need_data import load_needs
from .node_defaults import NUMERIC_FIELDS, OPTIONAL_DEFAULTS, STATED_NUMERIC_FIELDS, STRUCTURAL_DEFAULTS
from .actor_kinds_data import load_kind_declarations
from .catalog import (Trade, load_mod_tree_nodes, load_production_catalog, load_trade_registry, material_namespace,
                      reset_catalog_caches, trade_fields, trade_from, validate_mod_material_paths)
from .tree_merge import build_tree, merge_problems
from .tree_source import load_base_tree
from .commands import OpenContent
from .mod_stores import base_declarations as base_store_declarations
from .mod_stores import data_declarations as data_store_declarations
