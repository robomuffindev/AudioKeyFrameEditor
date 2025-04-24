# START OF FILE ui/status_bar.py
import tkinter as tk
from tkinter import ttk

class StatusBar(ttk.Frame):
    '''UI component for the status bar at the bottom.'''

    def __init__(self, parent, app_state, **kwargs):
        # Use relief=SUNKEN for the frame itself for visual separation
        super().__init__(parent, relief=tk.SUNKEN, **kwargs)
        self.state = app_state
        self.status_var = tk.StringVar()
        self.status_label = None # Initialize instance variable for the label widget
        self.create_widgets()
        self.update_status() # Initial update

    def create_widgets(self):
        # Label inside the sunken frame - store the label itself
        self.status_label = ttk.Label(self, textvariable=self.status_var, # <-- Assign to self.status_label
                                 anchor=tk.W, padding=(5, 2)) # West anchor, add padding
        self.status_label.pack(fill=tk.X, expand=True)

    def update_status(self):
        '''Updates the status bar text from the app state.'''
        # Add a space for padding if message exists
        message = self.state.status_message
        display_text = f" {message}" if message else ""
        try:
             # Update only if text changed to avoid unnecessary flickering?
             # Check if the LABEL widget exists before getting/setting the variable
             if hasattr(self, 'status_label') and self.status_label.winfo_exists(): # <-- CORRECTED CHECK (using status_label)
                 if self.status_var.get() != display_text:
                      self.status_var.set(display_text)
        except tk.TclError:
             # Can happen during shutdown if variable is destroyed or widget disappears
             pass

# END OF FILE ui/status_bar.py