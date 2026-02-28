# MarmosetLink

A universal bridge for integrating Autodesk Maya and Marmoset Toolbag.
Enables FBX export and automated baking in a single click.

## Installation

### 1. Marmoset Toolbag (General Setup)
1. In Marmoset Toolbag, go to `Edit -> Plugins -> Show User Plugin Folder`.
2. Copy `marmoset_scripts/mset_external_listener.py` to this folder.
3. In Marmoset, select `Edit -> Plugins -> Refresh`.
4. Find `mset_external_listener` in `Edit -> Plugins` and activate it (ensure the checkbox is checked).
   - The plugin is now listening for commands from any 3D DCC.

### 2. Autodesk Maya
1. Copy the `maya_mset_integration` folder to your Maya scripts directory (e.g., `C:\Users\user\Documents\maya\2025\scripts`).

### Quick Shelf Installation
To automatically create a dedicated **Marmoset** shelf with all tools:
1. Locate `maya_mset_integration/install_shelf.mel`.
2. Drag & Drop the file into the Maya viewport.
3. A new **Marmoset** shelf will be created with 4 buttons (**HP**, **LP**, **Bake**, **Reload**).

## Configuration

To configure export paths, the Marmoset window title, and mesh parameters (Unlock Normals, Freeze Normals, Triangulate), use the GUI.

### Via Shelf (Recommended)
On the **Marmoset** shelf, **Right-Click** the **HP** or **LP** buttons and select **Settings**.

### Via Script
```python
import importlib
import maya_mset_integration.maya_mset_settings_gui as mset_gui
importlib.reload(mset_gui) 
mset_gui.main()
```

## Usage

### Shelf Commands

#### Primary Actions (Left-Click)
* **HP**: Export High Poly mesh and trigger bake in Marmoset.
* **LP**: Process geometry (triangulation, normals), export Low Poly, and trigger bake.
* **Bake**: Re-trigger baking in Marmoset without re-exporting.
* **Reload**: Force refresh textures in Maya viewport.

#### Additional Options (Right-Click)
* **Open in Explorer**: Opens the export folder and selects the file.
* **Export Only**: Exports the mesh (with LP processing) without triggering Marmoset.
* **Settings**: Open the configuration dialog.

## How It Works (Linking Technical Details)

The integration uses a file-based Inter-Process Communication (IPC) mechanism to bypass application isolation.

1. **Trigger**: When you click a button in Maya, the script writes a small JSON file named `mset_bake_trigger.json` to the user's home directory.
2. **Focus**: Since Marmoset Toolbag only processes Python commands when it has window focus, the Maya script uses the **Win32 API** (`SetForegroundWindow`) to briefly bring the Marmoset window to the foreground.
3. **Listener**: Inside Marmoset, the `mset_external_listener.py` script runs a persistent callback (`onPeriodicUpdate`). It polls for the existence of the trigger file.
4. **Execution**: Once detected, the listener reads the command (e.g., `"rebake"`), deletes the trigger file, and executes the corresponding Marmoset API calls (e.g., `baker.bake()`).
5. **Reporting**: After the operation, Marmoset writes a `mset_bake_report.json`. Maya polls for this report to show a success notification or error message directly in the viewport (**In-View Message**).

## Troubleshooting
* If Marmoset is unresponsive, ensure `mset_external_listener.py` is active in the Plugins menu.
* If buttons fail after an update, reinstall the shelf by dragging `install_shelf.mel` again.
* Check the Maya Script Editor and Marmoset Console for error logs.

## Roadmap
* **Render Trigger**: Automated rendering from Maya/ZBrush.
* **ZBrush Integration**: SubTool export and scene updates.
* **Other DCC Support**: Integration for Blender, Cinema 4D, and 3ds Max.
