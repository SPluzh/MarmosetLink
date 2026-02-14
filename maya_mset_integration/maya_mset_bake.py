try:
    from . import maya_mset_utils
except ImportError:
    import maya_mset_utils

def main():
    """
    Main entry point for Bake ONLY.
    """
    # Force reload of utils
    import importlib
    import sys
    
    # Check if we can find the exact module name to reload it properly
    utils_name = maya_mset_utils.__name__
    if utils_name in sys.modules:
        importlib.reload(sys.modules[utils_name])
    else:
        importlib.reload(maya_mset_utils)
        
    print("Maya Trigger: Starting bake cycle...")

    # Run the cycle: No Export -> Trigger -> Wait -> Result
    maya_mset_utils.perform_bake_cycle(None)

if __name__ == "__main__":
    main()
