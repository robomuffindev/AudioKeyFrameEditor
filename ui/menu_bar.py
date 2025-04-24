import tkinter as tk
import inspect # For checking function signatures

def create_menu_bar(root, commands):
    '''Creates the main application menu bar.'''
    menubar = tk.Menu(root)

    # Helper to safely add command if it exists
    def _add_command(menu, label, cmd_key, accelerator=None):
        if cmd_key in commands and commands[cmd_key] is not None: # Check command exists and isn't None
            menu.add_command(label=label, command=commands[cmd_key], accelerator=accelerator)
        # else: # Optionally add disabled menu item if command missing?
            # menu.add_command(label=label, state=tk.DISABLED)

    # --- File menu ---
    file_menu = tk.Menu(menubar, tearoff=0)
    _add_command(file_menu, "Open Audio File...", 'open_audio', "Ctrl+O")
    _add_command(file_menu, "Select Slides Folder...", 'select_slides', "Ctrl+L")
    file_menu.add_separator()
    _add_command(file_menu, "Import Keyframes...", 'import_keyframes', "Ctrl+I")
    _add_command(file_menu, "Export Keyframes as JSON...", 'export_keyframes', "Ctrl+S")
    file_menu.add_separator()
    _add_command(file_menu, "Exit", 'exit')
    menubar.add_cascade(label="File", menu=file_menu)

    # --- Edit menu ---
    edit_menu = tk.Menu(menubar, tearoff=0)
    _add_command(edit_menu, "Add Keyframe", 'add_keyframe', "K")
    _add_command(edit_menu, "Edit Selected Keyframe Time", 'edit_keyframe', "Ctrl+E")
    _add_command(edit_menu, "Delete Selected Keyframe", 'delete_keyframe', "Del/Bksp")
    menubar.add_cascade(label="Edit", menu=edit_menu)

    # --- Navigate menu ---
    navigate_menu = tk.Menu(menubar, tearoff=0)
    _add_command(navigate_menu, "Go to Beginning", 'goto_start', "Home")
    _add_command(navigate_menu, "Go to End", 'goto_end', "End")
    _add_command(navigate_menu, "Skip Forward 5s", 'skip_fwd', "Right Arrow")
    _add_command(navigate_menu, "Skip Backward 5s", 'skip_bwd', "Left Arrow")
    menubar.add_cascade(label="Navigate", menu=navigate_menu)

    # --- Playback menu (Optional) ---
    playback_menu = tk.Menu(menubar, tearoff=0)
    _add_command(playback_menu, "Play / Pause", 'toggle_play', "Space")
    _add_command(playback_menu, "Stop", 'stop_play')
    menubar.add_cascade(label="Playback", menu=playback_menu)

    # --- Help menu ---
    help_menu = tk.Menu(menubar, tearoff=0)
    _add_command(help_menu, "Instructions", 'show_instructions')
    _add_command(help_menu, "About", 'show_about')
    menubar.add_cascade(label="Help", menu=help_menu)

    # --- Apply menubar to root window ---
    root.config(menu=menubar)

    # --- Bind Accelerators ---
    # Bind common accelerators directly to the root window for global access
    # Use a wrapper to prevent passing the event object if command doesn't expect it
    def bind_accel(key, cmd_key):
        # Ensure commands dictionary is available and the specific command exists
        if cmd_key in commands and commands[cmd_key] is not None:
            cmd = commands[cmd_key]
            # Check if command accepts event arg (basic check)
            accepts_event = False
            try:
                target_func = cmd
                # Handle functools.partial or similar wrappers
                while hasattr(target_func, 'func'):
                    target_func = target_func.func
                # Only inspect if it's actually callable
                if callable(target_func):
                    sig = inspect.signature(target_func)
                    accepts_event = len(sig.parameters) > 0
            except (ValueError, TypeError): pass # Ignore errors for non-inspectable items

            try:
                # Ensure root window exists before binding
                if root.winfo_exists():
                    if accepts_event:
                        root.bind_all(key, cmd) # Bind directly if it takes event
                    else:
                        # Wrap command that doesn't take event arg
                        root.bind_all(key, lambda e, c=cmd: c())
            except Exception as bind_error:
                print(f"Error binding key '{key}' to command '{cmd_key}': {bind_error}")


    # Bind file accelerators (Ctrl+O, L, I, S) - Case insensitive binding needed for Tkinter?
    # Bind both lowercase and uppercase versions for robustness
    for key_base in ['o', 'l', 'i', 's']:
         bind_accel(f"<Control-{key_base}>", {'o':'open_audio', 'l':'select_slides', 'i':'import_keyframes', 's':'export_keyframes'}[key_base])
         bind_accel(f"<Control-{key_base.upper()}>", {'o':'open_audio', 'l':'select_slides', 'i':'import_keyframes', 's':'export_keyframes'}[key_base])

    # Edit/Navigate/Playback accelerators are handled by root window/widget bindings defined elsewhere

    return menubar

# END OF FILE ui/menu_bar.py
