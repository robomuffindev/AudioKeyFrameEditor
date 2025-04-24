import tkinter as tk
from tkinter import ttk

class KeyframesList(ttk.Frame):
    '''UI component for displaying keyframes and related actions.'''

    def __init__(self, parent, app_state, commands, **kwargs):
        super().__init__(parent, **kwargs)
        self.state = app_state
        self.commands = commands

        self.create_widgets()

    def create_widgets(self):
        keyframes_frame = ttk.LabelFrame(self, text="Keyframes")
        # Allow this frame to expand vertically, give it some padding
        keyframes_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=(0,5))

        # Container for listbox and scrollbar
        list_container = ttk.Frame(keyframes_frame)
        list_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=(5,0)) # Pad inside LabelFrame

        # Keyframes listbox
        self.keyframes_listbox = tk.Listbox(list_container,
                                            font=("Courier", 10), # Monospace for alignment
                                            selectmode=tk.SINGLE,
                                            exportselection=False, # Prevent selection loss
                                            activestyle='dotbox', # Focus indicator
                                            borderwidth=0, # Remove border if theme adds one
                                            highlightthickness=1, # Use highlight for focus
                                            highlightcolor='#3b82f6', # Primary color
                                            )
        self.keyframes_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Scrollbar
        scrollbar = ttk.Scrollbar(list_container, orient=tk.VERTICAL,
                                  command=self.keyframes_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.keyframes_listbox.config(yscrollcommand=scrollbar.set)

        # --- Keyframe Actions Frame ---
        actions_frame = ttk.Frame(keyframes_frame)
        actions_frame.pack(fill=tk.X, padx=5, pady=(2, 5)) # Reduced padding

        # Edit Button
        edit_button = ttk.Button(actions_frame, text="Edit Time", width=9,
                                 command=self.commands['edit_keyframe'])
        edit_button.pack(side=tk.LEFT, padx=2)

        # Delete Button
        delete_button = ttk.Button(actions_frame, text="Delete", width=8,
                                   command=self.commands['delete_keyframe'])
        delete_button.pack(side=tk.LEFT, padx=2)

        # Spacer to push export button right
        spacer = ttk.Frame(actions_frame)
        spacer.pack(side=tk.LEFT, expand=True, fill=tk.X)

        # Export Button
        export_button = ttk.Button(actions_frame, text="Export JSON...", width=14,
                                   command=self.commands['export_keyframes'])
        export_button.pack(side=tk.RIGHT, padx=2)


    def get_listbox(self):
        return self.keyframes_listbox

    def update_list(self):
        '''Populates the listbox with formatted keyframe data.'''
        if not self.winfo_exists(): return # Avoid errors during shutdown

        # Store current selection index and view fraction
        try: # Wrap in try/except for TclError if widget destroyed during update
            selected_indices = self.keyframes_listbox.curselection()
            selected_index = selected_indices[0] if selected_indices else -1
            top_index = self.keyframes_listbox.nearest(0) # Index of item at top
        except tk.TclError:
            selected_index = -1
            top_index = 0 # Fallback if list empty or widget closing

        # Get formatted strings from handler
        formatted_keyframes = self.commands['get_formatted_keyframes']()

        # --- Repopulate Listbox ---
        try:
            if not self.keyframes_listbox.winfo_exists(): return # Check again before modify
            self.keyframes_listbox.delete(0, tk.END)
            if formatted_keyframes:
                 # Check if it's the placeholder or actual data
                 if formatted_keyframes[0] != "No keyframes defined":
                     self.keyframes_listbox.insert(tk.END, *formatted_keyframes) # Unpack list items
                     # self.keyframes_listbox.config(state=tk.NORMAL) # Ensure enabled
                 else:
                     self.keyframes_listbox.insert(tk.END, formatted_keyframes[0]) # Insert placeholder
                     # Disable listbox if placeholder? Optional visual cue
                     # self.keyframes_listbox.config(state=tk.DISABLED)
        except tk.TclError: return # Exit if widget destroyed during update

        # --- Restore Selection and View ---
        try:
            listbox_size = self.keyframes_listbox.size()
            # Check if the previously selected index is still valid
            if 0 <= selected_index < listbox_size and formatted_keyframes[0] != "No keyframes defined":
                 self.keyframes_listbox.selection_set(selected_index)
                 # Restore scroll position using 'see' on the top index before update
                 if top_index < listbox_size:
                     self.keyframes_listbox.see(top_index)
                 else: # If top index became invalid, just see selection
                     self.keyframes_listbox.see(selected_index)
            else:
                 # If selection became invalid (or was placeholder), ensure state reflects this
                 if self.state.selected_keyframe_index != -1:
                       self.commands['select_keyframe'](-1) # Update state via command
        except tk.TclError: pass # Ignore errors during shutdown


        # Ensure visual highlight matches state (might be redundant)
        self.update_selection_highlight()


    def update_selection_highlight(self):
        '''Sets the listbox selection highlight based on app_state.'''
        if not self.winfo_exists(): return # Avoid errors during shutdown

        listbox = self.keyframes_listbox
        selected_index = self.state.selected_keyframe_index

        try:
            # Check if listbox exists and is not empty before proceeding
            if not listbox or not listbox.winfo_exists() or listbox.size() == 0: return

            current_selection = listbox.curselection()
            current_selected_index = current_selection[0] if current_selection else -1

            # Only change selection if it differs from state
            if current_selected_index != selected_index:
                 # Clear previous selection first
                 if current_selected_index != -1 and 0 <= current_selected_index < listbox.size():
                      listbox.selection_clear(current_selected_index)

                 # Set new selection if valid (and not the placeholder)
                 if 0 <= selected_index < listbox.size() and listbox.get(selected_index) != "No keyframes defined":
                      listbox.selection_set(selected_index)
                      listbox.activate(selected_index) # Make active for keyboard nav
                      listbox.see(selected_index) # Ensure it's visible
        except tk.TclError:
             # Ignore errors, likely during widget destruction
             pass


# END OF FILE ui/keyframes_list.py
