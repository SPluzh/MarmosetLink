import os
import subprocess
import maya.cmds as cmds

try:
    from . import maya_mset_utils
except ImportError:
    import maya_mset_utils

def open_in_explorer(file_path):
    """
    Opens Windows Explorer with the specified file selected.
    """
    if not file_path:
        cmds.warning("No path specified.")
        return False
        
    if not os.path.exists(file_path):
        cmds.warning("File does not exist: {}".format(file_path))
        return False
        
    # Windows-specific command to open explorer and select a file
    # Uses 'explorer /select,"path"'
    try:
        norm_path = os.path.normpath(file_path)
        subprocess.Popen(['explorer', '/select,', norm_path])
        return True
    except Exception as e:
        cmds.error("Failed to open explorer: {}".format(e))
        return False

def main(mode='hp'):
    """
    Main entry point for the explorer action.
    
    Args:
        mode (str): 'hp' or 'lp' to determine which path to open.
    """
    config = maya_mset_utils.load_config()
    
    config_key = "hp_path" if mode == 'hp' else "lp_path"
    file_path = config.get(config_key)
    
    if not file_path:
        cmds.confirmDialog(
            title="Path Not Set",
            message="The export path for {} is not set in settings.".format(mode.upper()),
            button=["OK"],
            icon="warning"
        )
        return

    if not open_in_explorer(file_path):
        cmds.confirmDialog(
            title="File Not Found",
            message="The file was not found:\n{}\n\nPlease export it first.".format(file_path),
            button=["OK"],
            icon="warning"
        )

if __name__ == "__main__":
    main('hp')
