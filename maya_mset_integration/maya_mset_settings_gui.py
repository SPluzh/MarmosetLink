import maya.cmds as cmds
import os
try:
    from . import maya_mset_utils
except ImportError:
    import maya_mset_utils

class MsetSettingsWindow(object):
    def __init__(self):
        self.window_name = "MsetSettingsWindow"
        self.window_title = "Marmoset Export Settings"
        self.width = 400
        self.height = 250
        
    def show(self):
        # Delete existing window if it exists
        if cmds.window(self.window_name, exists=True):
            cmds.deleteUI(self.window_name)
            
        self.window = cmds.window(self.window_name, title=self.window_title, widthHeight=(self.width, self.height), resizeToFitChildren=True)
        
        main_layout = cmds.columnLayout(adjustableColumn=True, rowSpacing=10, columnOffset=['both', 10])
        
        # --- Paths Section ---
        cmds.frameLayout(label="Export Paths", collapsable=False, parent=main_layout, marginWidth=5, marginHeight=5)
        path_layout = cmds.columnLayout(adjustableColumn=True, rowSpacing=5)
        
        # HP Path
        cmds.text(label="High Poly Export Path:", align="left", parent=path_layout)
        cmds.rowLayout(numberOfColumns=2, adjustableColumn=1, parent=path_layout)
        self.hp_path_field = cmds.textField()
        cmds.button(label="...", command=lambda x: self.browse_file(self.hp_path_field))
        
        # LP Path
        cmds.text(label="Low Poly Export Path:", align="left", parent=path_layout)
        cmds.rowLayout(numberOfColumns=2, adjustableColumn=1, parent=path_layout)
        self.lp_path_field = cmds.textField()
        cmds.button(label="...", command=lambda x: self.browse_file(self.lp_path_field))

        # --- Settings Section ---
        cmds.frameLayout(label="LP Export Options", collapsable=False, parent=main_layout, marginWidth=5, marginHeight=5)
        options_layout = cmds.columnLayout(adjustableColumn=True, rowSpacing=5)
        
        self.unlock_normals_cb = cmds.checkBox(label="Unlock Normals (Soft Edges)", parent=options_layout)
        self.freeze_normals_cb = cmds.checkBox(label="Freeze Normals (Hard Edges)", parent=options_layout)
        self.triangulate_cb = cmds.checkBox(label="Triangulate Mesh", parent=options_layout)

        # --- Buttons ---
        cmds.separator(style='none', height=10, parent=main_layout)
        cmds.rowLayout(numberOfColumns=2, columnWidth2=(190, 190), adjustableColumn=1, parent=main_layout)
        cmds.button(label="Save Settings", height=30, command=lambda x: self.save_settings())
        cmds.button(label="Close", height=30, command=lambda x: cmds.deleteUI(self.window_name))
        
        # Load current settings
        self.load_settings()
        
        cmds.showWindow(self.window)

    def browse_file(self, text_field):
        start_dir = os.path.dirname(cmds.textField(text_field, query=True, text=True))
        if not start_dir or not os.path.exists(start_dir):
            start_dir = os.path.expanduser("~")
            
        path = cmds.fileDialog2(fileMode=0, startingDirectory=start_dir, fileFilter="FBX (*.fbx)", dialogStyle=2)
        if path:
            cmds.textField(text_field, edit=True, text=path[0])

    def load_settings(self):
        config = maya_mset_utils.load_config()
        
        # Paths
        hp_path = config.get("hp_path", "")
        lp_path = config.get("lp_path", "")
        cmds.textField(self.hp_path_field, edit=True, text=hp_path)
        cmds.textField(self.lp_path_field, edit=True, text=lp_path)
        
        # Booleans (Default to True if not present, to match script logic)
        cmds.checkBox(self.unlock_normals_cb, edit=True, value=config.get("unlock_normals", True))
        cmds.checkBox(self.freeze_normals_cb, edit=True, value=config.get("freeze_normals", True))
        cmds.checkBox(self.triangulate_cb, edit=True, value=config.get("triangulate", True))

    def save_settings(self):
        data = {
            "hp_path": cmds.textField(self.hp_path_field, query=True, text=True),
            "lp_path": cmds.textField(self.lp_path_field, query=True, text=True),
            "unlock_normals": cmds.checkBox(self.unlock_normals_cb, query=True, value=True),
            "freeze_normals": cmds.checkBox(self.freeze_normals_cb, query=True, value=True),
            "triangulate": cmds.checkBox(self.triangulate_cb, query=True, value=True)
        }
        
        if maya_mset_utils.save_config(data):
            cmds.inViewMessage(amg='<hl>Settings Saved</hl>', pos='topCenter', fade=True)
        else:
             cmds.confirmDialog(title="Error", message="Could not save settings. See Script Editor for details.", button=["OK"], icon="critical")

def main():
    # Force reload of utils to get new config
    import importlib
    import sys
    
    utils_name = maya_mset_utils.__name__
    if utils_name in sys.modules:
        importlib.reload(sys.modules[utils_name])
    else:
        importlib.reload(maya_mset_utils)
        
    win = MsetSettingsWindow()
    win.show()

if __name__ == "__main__":
    main()
