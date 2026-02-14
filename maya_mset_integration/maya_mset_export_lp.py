import maya.cmds as cmds
import os

try:
    from . import maya_mset_utils
except ImportError:
    import maya_mset_utils

def export_selection_advanced():
    """
    Process and Export selected objects to FBX (Low Poly).
    Workflow: Duplicate -> Unlock Normals -> Del History -> Freeze Normals -> Del History -> Triangulate -> Export -> Delete Duplicate
    """
    with maya_mset_utils.PreserveSelection():
        # Ensure object selection (handle components)
        if not maya_mset_utils.convert_selection_to_object():
            cmds.inViewMessage(amg='<hl>Export Error</hl>: No objects selected for export.', pos='topCenter', fade=True)
            return False

        # Check for selection
        selected = cmds.ls(selection=True)
        if not selected:
            cmds.inViewMessage(amg='<hl>Export Error</hl>: No objects selected for export.', pos='topCenter', fade=True)
            return False

        # Load Config using utility
        config = maya_mset_utils.load_config()
        export_path = config.get("lp_path", os.path.join(os.path.expanduser("~"), "Desktop", "LP_drop.fbx"))
        
        # Read export settings
        unlock_normals = config.get("unlock_normals", True)
        freeze_normals = config.get("freeze_normals", True)
        triangulate = config.get("triangulate", True)

        # Ensure the directory exists
        export_dir = os.path.dirname(export_path)
        if not os.path.exists(export_dir):
            try:
                os.makedirs(export_dir)
            except OSError as e:
                cmds.error("Maya Trigger: Could not create export directory: {}".format(e))
                return False

        print("Maya Trigger: Processing and Exporting LP to {}...".format(export_path))
        
        duplicated_nodes = []
        
        try:
            # 1. Duplicate
            # returnRootsOnly=True ensures we just get the top nodes of the duplication
            duplicated_nodes = cmds.duplicate(selected, returnRootsOnly=True)
            cmds.select(duplicated_nodes, replace=True)
            print("  - Duplicated objects: {}".format(duplicated_nodes))
            
            # 2. Unlock Normals (Conditional)
            if unlock_normals:
                cmds.polyNormalPerVertex(duplicated_nodes, unFreezeNormal=True)
                # Delete History for these objects specifically
                cmds.delete(duplicated_nodes, constructionHistory=True)
            
            # 4. Freeze Normals (Conditional)
            # Note: The numbering in comments might be slightly off due to conditional logic, 
            # but I'm keeping the flow consistent with the previous version's intent.
            if freeze_normals:
                cmds.polyNormalPerVertex(duplicated_nodes, freezeNormal=True)
                # Delete History for these objects specifically
                cmds.delete(duplicated_nodes, constructionHistory=True)
            
            # 6. Triangulate (Conditional)
            if triangulate:
                cmds.polyTriangulate(duplicated_nodes)
                print("  - Mesh processed (Triangulated)")
            else:
                 print("  - Mesh processed (Triangulation skipped)")

            # Load FBX plugin if not loaded
            if not cmds.pluginInfo("fbxmaya", query=True, loaded=True):
                cmds.loadPlugin("fbxmaya")
                
            # 7. Perform Export
            cmds.file(
                export_path,
                force=True,
                options="v=0;",
                type="FBX export",
                exportSelected=True
            )
            
            # Verify export
            if not os.path.exists(export_path):
                raise Exception("Export file was NOT created at: {}".format(export_path))
                
            if os.path.getsize(export_path) == 0:
                raise Exception("Export file is empty: {}".format(export_path))
                
            print("Maya Trigger: Export successful: {}".format(export_path))
            
            # 8. Delete Duplicated Object
            if duplicated_nodes:
                cmds.delete(duplicated_nodes)
                print("  - Cleanup: Duplicated objects deleted.")
                
            return True

        except Exception as e:
            cmds.error("Maya Trigger: Export/Processing failed: {}".format(e))
            # Cleanup if failed
            if duplicated_nodes and cmds.objExists(duplicated_nodes[0]):
                 cmds.delete(duplicated_nodes)
            return False

def main():
    """
    Main entry point for LP Export + Bake.
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

    # Use the advanced export function defined above
    maya_mset_utils.perform_bake_cycle(export_selection_advanced)

if __name__ == "__main__":
    main()
