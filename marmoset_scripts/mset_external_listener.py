import mset
import os
import json
import time
import threading

# Path to the trigger file
TRIGGER_FILE = os.path.join(os.path.expanduser("~"), "mset_bake_trigger.json")
# Path to the report file
REPORT_FILE = os.path.join(os.path.expanduser("~"), "mset_bake_report.json")

# Lock to prevent race condition between thread and onPeriodicUpdate
_file_lock = threading.Lock()

# Global counter for heartbeat
_poll_counter = 0

def check_for_commands():
    global _poll_counter
    _poll_counter += 1
    
    # Heartbeat every ~100 calls
    if _poll_counter % 100 == 0:
        print("Marmoset Listener: Heartbeat (counter: {})".format(_poll_counter))

    # Use lock to prevent double processing
    if not _file_lock.acquire(blocking=False):
        return
    
    try:
        if not os.path.exists(TRIGGER_FILE):
            return
        
        print("Marmoset Listener: TRIGGER FILE DETECTED")
        
        with open(TRIGGER_FILE, "r") as f:
            data = json.load(f)
        
        # Remove file FIRST to prevent double processing
        os.remove(TRIGGER_FILE)
        print("Marmoset Listener: Trigger file removed.")
        
        print("Marmoset Listener: Data: " + str(data))
        
        command = data.get("command")
        result = {"status": "error", "message": "Unknown command"}

        if command == "rebake":
            print("Marmoset Listener: Executing rebake...")
            result = rebake_selected()
        else:
            print("Marmoset Listener: Unknown command: " + str(command))
            result = {"status": "error", "message": "Unknown command: " + str(command)}
        
        # Write report file
        try:
            with open(REPORT_FILE, "w") as f:
                json.dump(result, f)
            print("Marmoset Listener: Report written to " + REPORT_FILE)
        except Exception as e:
            print("Marmoset Listener: Failed to write report: " + str(e))

    except Exception as e:
        print("Marmoset Listener Error: " + str(e))
    finally:
        _file_lock.release()

def rebake_selected():
    try:
        selected = mset.getSelectedObjects()
        print("Marmoset Listener: Selected objects: " + str(len(selected)))
        
        bakers = [obj for obj in selected if isinstance(obj, mset.BakerObject)]
        
        if not bakers:
            msg = "No Baker in selection!"
            print("Marmoset Listener: " + msg)
            for obj in selected:
                print("  - " + str(type(obj).__name__) + ": " + obj.name)
            return {"status": "error", "message": msg}

        baked_count = 0
        errors = []
        for baker in bakers:
            print("Marmoset Listener: Baking " + baker.name + "...")
            try:
                baker.bake()
                print("Marmoset Listener: Bake done for " + baker.name)
                baked_count += 1
            except Exception as e:
                err_msg = "Bake error for " + baker.name + ": " + str(e)
                print("Marmoset Listener: " + err_msg)
                errors.append(err_msg)
        
        if errors:
            return {"status": "error", "message": "; ".join(errors)}
        
        return {"status": "success", "message": "Bake Ready"}

    except Exception as e:
        return {"status": "error", "message": "Exception during rebake: " + str(e)}



# Register callback via mset.callbacks instance
try:
    mset.callbacks.onPeriodicUpdate = check_for_commands
    print("Marmoset Listener: Callback registered.")
except Exception as e:
    print("Marmoset Listener: Callback registration failed: " + str(e))

print("Marmoset External Listener started. Polling: " + TRIGGER_FILE)
print("NOTE: Marmoset freezes Python when not in focus.")
print("      Maya trigger will auto-focus Marmoset before sending commands.")
