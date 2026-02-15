import maya.cmds as cmds
import maya.mel as mel
import os
import json
import time
import ctypes
import ctypes.wintypes
import threading
import maya.utils

# --- Win32 API Setup ---
user32 = ctypes.windll.user32
user32.GetWindowTextLengthW.argtypes = [ctypes.wintypes.HWND]
user32.GetWindowTextW.argtypes = [ctypes.wintypes.HWND, ctypes.wintypes.LPWSTR, ctypes.c_int]
user32.IsWindowVisible.argtypes = [ctypes.wintypes.HWND]
user32.IsIconic.argtypes = [ctypes.wintypes.HWND]
user32.ShowWindow.argtypes = [ctypes.wintypes.HWND, ctypes.c_int]
user32.SetForegroundWindow.argtypes = [ctypes.wintypes.HWND]
user32.EnumWindows.argtypes = [ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.wintypes.HWND, ctypes.wintypes.LPARAM), ctypes.wintypes.LPARAM]

# Define callback type once
EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.wintypes.HWND, ctypes.wintypes.LPARAM)

def load_config():
    """Load configuration from config.json in the user's home directory."""
    try:
        # 1. Try to find config in the current directory (if script is in maya_mset_integration)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        package_config = os.path.join(current_dir, "config.json")
        
        if os.path.exists(package_config):
            with open(package_config, "r", encoding="utf-8") as f:
                return json.load(f)

        # 2. Try to find config in the parent directory
        parent_dir = os.path.dirname(current_dir)
        local_config = os.path.join(parent_dir, "config.json")
        
        if os.path.exists(local_config):
            with open(local_config, "r", encoding="utf-8") as f:
                return json.load(f)
        
        # 3. Fallback to user home
        config_path = os.path.join(os.path.expanduser("~"), "config.json")
        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)
                
    except Exception as e:
        print("Maya Utils: Could not load config.json: {}".format(e))
    return {}

def save_config(data):
    """Save configuration to config.json, preferring script directory."""
    try:
        # 1. Try to save to the script's directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        local_config = os.path.join(current_dir, "config.json")
        
        try:
            with open(local_config, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            print("Maya Utils: Config saved to {}".format(local_config))
            return True
        except (IOError, OSError):
             # 2. Fallback to user home
            print("Maya Utils: Could not save to script dir, falling back to user home.")
            config_path = os.path.join(os.path.expanduser("~"), "config.json")
            
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
                
            print("Maya Utils: Config saved to {}".format(config_path))
            return True

    except Exception as e:
        cmds.error("Maya Utils: Could not save config.json: {}".format(e))
        return False

class UndoDisabled:
    """Context manager to temporarily disable Maya's undo queue without flushing it."""
    def __enter__(self):
        # Record initial undo length
        self.initial_length = cmds.undoInfo(q=True, length=True)
        self.state = cmds.undoInfo(q=True, stateWithoutFlush=True)
        cmds.undoInfo(stateWithoutFlush=False)
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Force pending UI updates (like Attribute Editor callbacks) 
        # to record into "nowhere" before re-enabling undo
        cmds.refresh()
        cmds.undoInfo(stateWithoutFlush=self.state)
        
        # Cleanup leaked "ghost" steps (internal Maya UI callbacks)
        new_length = cmds.undoInfo(q=True, length=True)
        leaks = new_length - self.initial_length
        if leaks > 0:
            print("Maya Utils: Cleaning up {} leaked undo steps...".format(leaks))
            for _ in range(leaks):
                try:
                    cmds.undo()
                except:
                    break

# -- Deferred undo cleanup --
_undo_target_length = None

def _schedule_undo_cleanup():
    """Schedule a deferred cleanup pass to remove ghost undo steps 
    that Maya's UI callbacks create after script execution."""
    global _undo_target_length
    _undo_target_length = cmds.undoInfo(q=True, length=True)
    maya.utils.executeDeferred(_deferred_undo_cleanup)

def _deferred_undo_cleanup():
    """Runs after all pending Maya UI callbacks have executed.
    Undos any ghost steps that appeared since the target was set."""
    global _undo_target_length
    if _undo_target_length is None:
        return
    current_length = cmds.undoInfo(q=True, length=True)
    leaks = current_length - _undo_target_length
    if leaks > 0:
        print("Maya Utils: Cleaning up {} deferred ghost undo steps...".format(leaks))
        for _ in range(leaks):
            try:
                cmds.undo()
            except:
                break
    _undo_target_length = None

def find_and_focus_marmoset():
    """Find Marmoset Toolbag window and bring it to foreground using Win32 API."""
    found_hwnd = None
    
    def enum_callback(hwnd, lparam):
        nonlocal found_hwnd
        if user32.IsWindowVisible(hwnd):
            length = user32.GetWindowTextLengthW(hwnd)
            if length > 0:
                buf = ctypes.create_unicode_buffer(length + 1)
                user32.GetWindowTextW(hwnd, buf, length + 1)
                title = buf.value.lower()
                
                # Load configured window title
                config = load_config()
                target_title = config.get("mset_window_title", "marmoset toolbag").lower()
                
                if title.startswith(target_title):
                    found_hwnd = hwnd
                    return False  # Stop enumerating
        return True
    
    # Use the pre-defined callback type to wrap the python function
    user32.EnumWindows(EnumWindowsProc(enum_callback), 0)
    
    if found_hwnd:
        # Show window if minimized
        SW_RESTORE = 9
        if user32.IsIconic(found_hwnd):
            user32.ShowWindow(found_hwnd, SW_RESTORE)
        
        # Bring to foreground
        user32.SetForegroundWindow(found_hwnd)
        print("Maya Utils: Marmoset window activated (hwnd: {})".format(found_hwnd))
        return True
    else:
        cmds.confirmDialog(
            title="Marmoset Not Found",
            message="Marmoset Toolbag window was not found.\n\nPlease ensure Marmoset Toolbag is running.",
            button=["OK"],
            icon="critical"
        )
        print("Maya Utils: Marmoset window NOT found!")
        return False

class PreserveSelection:
    """
    Context manager to save and restore selection, selection mode (Object/Component),
    component type (vertex/edge/face/UV), and hilite state.
    """
    def __init__(self):
        self.selection = []
        self.mode = None
        self.component_masks = {}
        self.hilite = []

    def __enter__(self):
        self.selection = cmds.ls(selection=True)
        self.hilite = cmds.ls(hilite=True)
        
        # Check active mode
        if cmds.selectMode(q=True, component=True):
            self.mode = 'component'
            # Save all polymesh component type masks
            self.component_masks = {
                'polymeshVertex': cmds.selectType(q=True, polymeshVertex=True),
                'polymeshEdge': cmds.selectType(q=True, polymeshEdge=True),
                'polymeshFace': cmds.selectType(q=True, polymeshFace=True),
                'polymeshUV': cmds.selectType(q=True, polymeshUV=True),
            }
        else:
            self.mode = 'object'
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.mode == 'component':
            # Mimic Maya's own flow to enter component mode:
            # 1. Go to object mode first (clean slate)
            cmds.selectMode(object=True)
            cmds.select(clear=True)
            
            # 2. Select the original objects and hilite them
            if self.hilite:
                cmds.select(self.hilite, replace=True)
                cmds.hilite(self.hilite, replace=True)
            
            # 3. Now switch to component mode (objects must be hilited first)
            cmds.selectMode(component=True)
            
            # 4. Set component type mask (face/edge/vertex/uv)
            if self.component_masks:
                cmds.selectType(
                    polymeshVertex=self.component_masks.get('polymeshVertex', False),
                    polymeshEdge=self.component_masks.get('polymeshEdge', False),
                    polymeshFace=self.component_masks.get('polymeshFace', False),
                    polymeshUV=self.component_masks.get('polymeshUV', False),
                )
            
            # 5. Re-select the saved components
            if self.selection:
                try:
                    cmds.select(self.selection, replace=True)
                except Exception:
                    pass
        else:
            cmds.selectMode(object=True)
            if self.selection:
                try:
                    cmds.select(self.selection, replace=True)
                except Exception:
                    pass
            else:
                cmds.select(clear=True)

def convert_selection_to_object():
    """
    If components (faces, verts, etc.) are selected, convert selection to objects (transforms).
    Returns True if selection exists (objects or components), False otherwise.
    """
    sel = cmds.ls(selection=True)
    if not sel:
        return False

    # Check if we have components (by checking filterExpand)
    # 31: Vertex, 32: Edge, 34: Face, 35: UVs, 70: Components
    # If any components are selected, we convert EVERYTHING to objects
    if cmds.filterExpand(sm=(31, 32, 34, 35)):
        # ls -o returns the shape (usually) for components
        objects = cmds.ls(selection=True, objectsOnly=True)
        # We generally want transforms for export
        transforms = []
        for obj in objects:
            if cmds.nodeType(obj) == 'transform':
                transforms.append(obj)
            else:
                # Try to get parent transform of the shape
                parents = cmds.listRelatives(obj, parent=True, fullPath=True)
                if parents:
                    transforms.extend(parents)
        
        if transforms:
            # Deduplicate and select
            cmds.select(list(set(transforms)), replace=True)
            return True
            
    return True

def simple_fbx_export(config_key, default_filename):
    """
    Standard FBX export for selected objects.
    
    Args:
        config_key (str): Key in config.json to look for the export path (e.g., 'hp_path').
        default_filename (str): Fallback filename if config is missing (e.g., 'HP_drop.fbx').
        
    Returns:
        bool: True if export successful, False otherwise.
    """
    with UndoDisabled():
        with PreserveSelection():
            # Ensure object selection
            if not convert_selection_to_object():
                cmds.inViewMessage(amg='<hl>Export Error</hl>: No objects selected for export.', pos='topCenter', fade=True)
                return False
                
            # Check for selection (double check after conversion)
            selected = cmds.ls(selection=True)
            if not selected:
                cmds.inViewMessage(amg='<hl>Export Error</hl>: No objects selected for export.', pos='topCenter', fade=True)
                return False

            # Load Config
            config = load_config()
            export_path = config.get(config_key, os.path.join(os.path.expanduser("~"), "Desktop", default_filename))
            
            # Ensure the directory exists
            export_dir = os.path.dirname(export_path)
            if not os.path.exists(export_dir):
                try:
                    os.makedirs(export_dir)
                except OSError as e:
                    cmds.error("Maya Utils: Could not create export directory: {}".format(e))
                    return False

            print("Maya Utils: Exporting to {}...".format(export_path))
            
            try:
                # Load FBX plugin if not loaded
                if not cmds.pluginInfo("fbxmaya", query=True, loaded=True):
                    cmds.loadPlugin("fbxmaya")
                
                    
                # Perform Export
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
                    
                print("Maya Utils: Export successful: {}".format(export_path))
                cmds.inViewMessage(amg='<hl>Export Successful</hl>: {}'.format(os.path.basename(export_path)), pos='topCenter', fade=True)
                return True
            except Exception as e:
                cmds.error("Maya Utils: Export failed: {}".format(e))
                return False

def perform_bake_cycle(export_callback=None):
    """
    Orchestrates the bake cycle: Export -> Trigger -> Wait -> Result.
    
    Args:
        export_callback (callable, optional): function to function to call for export. 
                                              If None, skips export and just triggers bake.
                                              If it returns False, the cycle stops.
    """
    with UndoDisabled():
        # Step 0: Export (if callback provided)
        # Use PreserveSelection manually since we are going async
        selection_guard = PreserveSelection()
        selection_guard.__enter__()
        
        if export_callback:
            if not export_callback():
                print("Maya Utils: Export step failed or cancelled.")
                # Restore immediately
                selection_guard.__exit__(None, None, None)
                return

        trigger_file = os.path.join(os.path.expanduser("~"), "mset_bake_trigger.json")
        
        # Step 1: Write the trigger file
        data = {
            "command": "rebake",
            "timestamp": time.time()
        }
        
        try:
            with open(trigger_file, "w") as f:
                json.dump(data, f)
            print("Maya Utils: Command 'rebake' written.")
        except Exception as e:
            cmds.error("Maya Utils Error: " + str(e))
            selection_guard.__exit__(None, None, None)
            return
        
        # Step 2: Bring Marmoset to focus so its Python unfreezes
        if not find_and_focus_marmoset():
            # If we can't find Marmoset, restore and return
            selection_guard.__exit__(None, None, None)
            return

        # Step 3: Start polling in a separate thread to avoid freezing Maya UI
        print("Maya Utils: Waiting for Marmoset report (Async)...")
        t = threading.Thread(target=_poll_marmoset_thread, args=(selection_guard,))
        t.daemon = True # Ensure thread dies if Maya closes
        t.start()

def _poll_marmoset_thread(selection_guard):
    """
    Runs in a background thread. Polls for the report file.
    Does NOT touch Maya API directly.
    """
    report_file = os.path.join(os.path.expanduser("~"), "mset_bake_report.json")
    max_retries = 60 # 30 seconds
    
    result = None
    
    for i in range(max_retries):
        if os.path.exists(report_file):
            try:
                # Small delay to ensure write completion
                time.sleep(0.1)
                
                with open(report_file, "r") as f:
                    result = json.load(f)
                
                # Cleanup
                os.remove(report_file)
                break 
            except Exception as e:
                print("Maya Utils: Thread error reading report: " + str(e))
        
        time.sleep(0.5)
        
    # Schedule the completion handler on the main thread
    maya.utils.executeDeferred(_on_bake_complete, result, selection_guard)

def _on_bake_complete(result, selection_guard):
    """
    Runs on the main Maya thread. Handles UI updates and restores selection.
    """
    with UndoDisabled():
        try:
            if result:
                status = result.get("status", "unknown")
                message = result.get("message", "No message")
                
                print("Maya Utils: Marmoset Report - [{}] {}".format(status.upper(), message))
                
                if status == "success":
                    cmds.inViewMessage(amg="<hl>Marmoset Bake Ready</hl>", pos="topCenter", fade=True)
                    
                    # Reload Textures
                    cmds.ogs(reloadTextures=True)
                    print("Maya Utils: Textures reloaded.")
                    
                    # Schedule a deferred cleanup to catch any UI callbacks 
                    # that fire after this function exits
                    _schedule_undo_cleanup()
                else:
                    # Specific error from Marmoset (e.g. No Baker Selected)
                    cmds.confirmDialog(
                        title="Marmoset Error",
                        message="Marmoset reported an error:\n\n{}".format(message),
                        button=["OK"],
                        icon="critical"
                    )
            else:
                # Actual timeout (result is None)
                cmds.confirmDialog(
                    title="Marmoset Timeout",
                    message="Marmoset Toolbag did not respond within 30 seconds.\n\nPlease ensure that 'mset_external_listener.py' is running inside Marmoset Toolbag.",
                    button=["OK"],
                    icon="warning"
                )
                 
        except Exception as e:
            print("Maya Utils: Error in completion handler: {}".format(e))
        finally:
            # Step 4: Restore selection
            if selection_guard:
                selection_guard.__exit__(None, None, None)

def reload_textures():
    """
    Reloads all textures in the Maya VP2.0 (ogs reload) and shows a notification.
    """
    cmds.ogs(reloadTextures=True)
    cmds.inViewMessage(amg='<hl>Textures Reloaded</hl>', pos='topCenter', fade=True)
    print("Maya Utils: Textures reloaded.")
