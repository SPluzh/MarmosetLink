try:
    from . import maya_mset_utils
except ImportError:
    import maya_mset_utils

def main():
    """
    Main entry point for HP Export + Bake.
    """
    # Force reload of utils
    _reload_utils()

    # Define the export function using the utility
    export_func = lambda: maya_mset_utils.simple_fbx_export("hp_path", "HP_drop.fbx")
    
    # Run the cycle
    maya_mset_utils.perform_bake_cycle(export_func)

def main_export_only():
    """
    Export HP without triggering Marmoset Bake.
    """
    _reload_utils()
    maya_mset_utils.simple_fbx_export("hp_path", "HP_drop.fbx")

def _reload_utils():
    import importlib
    import sys
    utils_name = maya_mset_utils.__name__
    if utils_name in sys.modules:
        importlib.reload(sys.modules[utils_name])
    else:
        importlib.reload(maya_mset_utils)

if __name__ == "__main__":
    main()
