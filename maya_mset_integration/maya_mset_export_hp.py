try:
    from . import maya_mset_utils
except ImportError:
    import maya_mset_utils

def main():
    """
    Main entry point for HP Export + Bake.
    """
    # Force reload of utils to ensure latest changes (like in-view messages) are picked up
    import importlib
    import sys
    
    # Check if we can find the exact module name to reload it properly
    utils_name = maya_mset_utils.__name__
    if utils_name in sys.modules:
        importlib.reload(sys.modules[utils_name])
    else:
        importlib.reload(maya_mset_utils)

    # Define the export function using the utility
    # config_key="hp_path", default_name="HP_drop.fbx"
    export_func = lambda: maya_mset_utils.simple_fbx_export("hp_path", "HP_drop.fbx")
    
    # Run the cycle
    maya_mset_utils.perform_bake_cycle(export_func)

if __name__ == "__main__":
    main()
