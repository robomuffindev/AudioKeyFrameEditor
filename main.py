import sys
import os
import platform
import tkinter as tk # Import tkinter early for version check?
import traceback # For printing detailed errors

# --- Path Setup ---
# Ensure the script directory is in the path for relative imports
# This allows running 'python main.py' from the project root
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
     sys.path.insert(0, script_dir)
     print(f"Added {script_dir} to sys.path")

# --- Environment Checks ---
print(f"Python Version: {sys.version}")
try:
    print(f"Tkinter Version: {tk.Tcl().eval('info patchlevel')}") # Get Tk version
except tk.TclError as e:
    print(f"Could not get Tkinter version: {e}")
print(f"Platform: {platform.system()} {platform.release()}")


# --- DPI Awareness (Windows specific) ---
# Attempt to set DPI awareness BEFORE importing tkinter or creating the root window
# This helps with UI scaling on high-resolution displays.
def set_dpi_awareness():
    try:
        if platform.system() == "Windows":
            # Check Windows version for API availability
            win_ver = sys.getwindowsversion()
            if win_ver.major >= 6: # Vista+ for SetProcessDPIAware
                # Check for Per Monitor V2 API (requires Win 10 Creators Update+)
                # Need GetProcAddress to check for SetProcessDpiAwareness, as it might not exist
                try:
                    from ctypes import windll, c_int, WINFUNCTYPE, HRESULT, byref, POINTER
                    # Define necessary constants if not available
                    PROCESS_PER_MONITOR_DPI_AWARE = 2
                    MDT_EFFECTIVE_DPI = 0

                    # Attempt to load shcore.dll and get function pointers
                    shcore = windll.shcore
                    SetProcessDpiAwareness = shcore.SetProcessDpiAwareness
                    SetProcessDpiAwareness.argtypes = [c_int]
                    SetProcessDpiAwareness.restype = HRESULT

                    res = SetProcessDpiAwareness(PROCESS_PER_MONITOR_DPI_AWARE)
                    if res == 0: # S_OK
                        print("Set DPI Awareness to Per Monitor Aware V2.")
                        # Optional: Get current DPI if needed later
                        # GetDpiForMonitor = windll.shcore.GetDpiForMonitor
                        # GetDpiForMonitor.argtypes = [wintypes.HMONITOR, wintypes.UINT, POINTER(wintypes.UINT), POINTER(wintypes.UINT)]
                        # GetDpiForMonitor.restype = HRESULT
                        # ... (Getting monitor handle and calling is more complex)
                        return True
                    else:
                        print(f"SetProcessDpiAwareness(2) failed with HRESULT {res}, trying System Aware...")
                except (ImportError, AttributeError, OSError, ValueError, NameError):
                    print("Per Monitor Aware V2 API check failed or not available, trying System Aware...")
                    pass # Fall through to System Aware

                # Try System Aware if V2 failed or not available
                try:
                    from ctypes import windll
                    res = windll.user32.SetProcessDPIAware()
                    if res != 0: # Non-zero typically means success here
                        print("Set DPI Awareness to System Aware.")
                        return True
                    else:
                        # Check GetLastError? Might not be necessary.
                        print("SetProcessDPIAware() returned 0. DPI awareness not set.")
                        return False
                except (ImportError, AttributeError, OSError, ValueError):
                    print("System Aware DPI API check failed. DPI awareness not set.")
                    return False
            else: # Older than Vista
                 print("OS version too old for DPI awareness APIs.")
                 return False
    except ImportError:
         print("ctypes module not found, cannot set DPI awareness.")
         return False
    except Exception as e:
         print(f"Error setting DPI awareness: {e}")
         return False
    return False # Default if not Windows or failed

set_dpi_awareness()

# --- Main Application Import and Run ---
# Import the main window class AFTER setting DPI awareness
# Add detailed error handling for potential import issues
try:
    print("Importing application modules...")
    from ui.main_window import AudioKeyframeEditor
    print("Application modules imported successfully.")
except ImportError as e:
     print("\n--- ImportError ---")
     print(f"Failed to import application components: {e}")
     print("This might happen if:")
     print(" 1. You haven't run install.bat successfully.")
     print(" 2. You are not running 'run.bat' or 'python main.py' from the correct directory.")
     print(" 3. There's an issue with the Python environment or installed packages.")
     print(" 4. A file is missing or corrupted (check handlers/ ui/ folders).")
     print("\nPlease check the console output from install.bat and ensure requirements.txt is correct.")
     traceback.print_exc() # Print traceback for more details
     input("Press Enter to exit.") # Keep console open
     sys.exit(1)
except Exception as general_import_error:
     print("\n--- Unexpected Error During Import ---")
     traceback.print_exc()
     print(f"\nError: {general_import_error}")
     input("An unexpected error occurred while importing application modules. Press Enter to exit.")
     sys.exit(1)


def run_application():
    '''Initializes and runs the main application loop.'''
    print("\nStarting Audio Keyframe Editor...")

    # Check if running in a detected virtual environment (optional but good practice)
    in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
    if not in_venv:
         print("Warning: Not running in a detected virtual environment (venv).")
         print("         Consider using install.bat and run.bat for proper dependency management.")

    app = None # Initialize app to None
    try:
        app = AudioKeyframeEditor()
        # Check if app initialization failed somehow (e.g., pygame init error)
        # Checking winfo_exists here might be too early if init itself failed before mainloop
        # Rely on try/except around mainloop instead.

        print("Starting Tkinter main loop...")
        app.mainloop()
        print("Application closed normally.")
    except tk.TclError as tk_error:
         # Catch common Tkinter errors, often related to display or backend issues
         print("\n--- Tkinter Runtime Error ---")
         print(f"Error: {tk_error}")
         print("This might be related to display drivers, graphical environment setup, or")
         print("conflicts with other GUI toolkits. Ensure your system environment is stable.")
         traceback.print_exc()
         input("A Tkinter error occurred. Press Enter to exit.")
         sys.exit(1)

    except Exception as e:
         # Catch any other unexpected error during app execution
         print("\n--- UNEXPECTED APPLICATION ERROR ---")
         traceback.print_exc()
         print(f"\nError: {e}")
         # Try to show a message box if tkinter might still be partially working
         try:
             # Check if app window was created before trying messagebox
             if app and app.winfo_exists():
                 from tkinter import messagebox
                 messagebox.showerror("Application Error", f"An unexpected error occurred:\n\n{e}\n\nSee console for details.", parent=app)
             else: # If app window doesn't exist, showing messagebox might fail
                  print("Cannot show error messagebox because main window does not exist.")
         except Exception as mb_error:
             print(f"Could not display error messagebox: {mb_error}")
         input("An unexpected error occurred. Press Enter to exit.")
         sys.exit(1)
    finally:
         # Ensure pygame is quit even if mainloop fails (might already be handled in _on_close)
         try:
             import pygame
             if pygame.get_init():
                 print("Ensuring Pygame quits...")
                 pygame.quit()
         except NameError: pass # Pygame wasn't imported successfully
         except Exception as pq_err:
             print(f"Error during final Pygame quit: {pq_err}")


if __name__ == "__main__":
    # Example: Add command-line argument parsing here if needed in the future
    # import argparse
    # parser = argparse.ArgumentParser(description="Audio Keyframe Editor")
    # parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    # args = parser.parse_args()
    # if args.debug: print("Debug mode enabled.")

    run_application()

# END OF FILE main.py
