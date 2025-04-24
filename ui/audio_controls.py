# START OF FILE ui/audio_controls.py
import tkinter as tk
from tkinter import ttk
import os
# Ensure utils is importable
try:
    from utils import format_time
except ImportError:
    print("ERROR: Cannot import from utils.py in audio_controls. Ensure it's accessible.")
    def format_time(s): return f"{s:.3f}s" # Basic fallback

class AudioControls(ttk.Frame):
    '''UI component for audio file selection, playback controls, and time display.'''

    def __init__(self, parent, app_state, commands, **kwargs):
        super().__init__(parent, **kwargs)
        self.state = app_state
        self.commands = commands

        # Store button references if needed for state changes (e.g., disable stop button)
        self.stop_button = None
        self.play_button = None
        # Store references to widgets that might be checked with winfo_exists
        self.audio_path_entry = None # <<< Store the Entry widget
        self.time_display_label = None # <<< Store the Label widget

        self.create_widgets()

    def create_widgets(self):
        # Use grid layout for this frame
        self.columnconfigure(1, weight=1) # Allow file path entry (column 1) to expand

        # --- Row 0: File Selection ---
        file_label = ttk.Label(self, text="Audio File:")
        file_label.grid(row=0, column=0, padx=(5, 2), pady=5, sticky='w')

        self.audio_path_var = tk.StringVar(value=self.state.get_audio_basename())
        # Store the entry widget
        self.audio_path_entry = ttk.Entry(self, textvariable=self.audio_path_var, state="readonly", width=40) # <<< Stored here
        self.audio_path_entry.grid(row=0, column=1, padx=2, pady=5, sticky='ew') # Expand horizontally

        file_button = ttk.Button(self, text="Browse...", width=8, command=self.commands['open_audio'])
        file_button.grid(row=0, column=2, padx=(2, 5), pady=5, sticky='e')

        # --- Row 1: Playback Controls ---
        controls_frame = ttk.Frame(self)
        controls_frame.grid(row=1, column=0, columnspan=3, padx=5, pady=(2,5), sticky='ew')
        # Configure columns within this inner frame as needed
        controls_frame.columnconfigure(2, weight=1) # Let time display center itself or expand

        # Play/Pause Button
        self.play_button = ttk.Button(controls_frame, text="Play", width=6,
                                      command=self.commands['toggle_play'], style='Primary.TButton')
        self.play_button.grid(row=0, column=0, padx=(0, 2))

        # Stop Button
        self.stop_button = ttk.Button(controls_frame, text="Stop", width=6,
                                      command=self.commands['stop_play'])
        self.stop_button.grid(row=0, column=1, padx=2)
        self._update_stop_button_state() # Initial state

        # Spacer (optional, for centering time)
        # ttk.Frame(controls_frame).grid(row=0, column=2, sticky='ew', weight=1)

        # Time display Label
        self.time_display_var = tk.StringVar(value="00:00.000 / 00:00.000")
        # Store the time display label widget
        self.time_display_label = ttk.Label(controls_frame, textvariable=self.time_display_var, # <<< Stored here
                                             font=("Courier", 11, "bold"), anchor=tk.CENTER, width=23)
        self.time_display_label.grid(row=0, column=3, padx=10) # Place time display

        # Skip Buttons Frame
        skip_frame = ttk.Frame(controls_frame)
        skip_frame.grid(row=0, column=4, padx=10)
        skip_bwd_button = ttk.Button(skip_frame, text="←5s", width=4, command=self.commands['skip_bwd'])
        skip_bwd_button.pack(side=tk.LEFT, padx=2)
        skip_fwd_button = ttk.Button(skip_frame, text="→5s", width=4, command=self.commands['skip_fwd'])
        skip_fwd_button.pack(side=tk.LEFT, padx=2)

        # Add Keyframe Button
        add_kf_button = ttk.Button(controls_frame, text="+ Keyframe (k)", width=12,
                                   command=self.commands['add_keyframe'], style='Success.TButton')
        add_kf_button.grid(row=0, column=5, padx=10)

        # Speed Control Frame
        speed_frame = ttk.Frame(controls_frame)
        speed_frame.grid(row=0, column=6, padx=(10, 0))

        ttk.Label(speed_frame, text="Speed:").pack(side=tk.LEFT)
        self.speed_var = tk.StringVar()
        initial_speed_str = f"{self.state.playback_speed:.2f}x".replace('.00', '.0').replace('.25x','¼x').replace('.50x','½x').replace('.75x','¾x')
        initial_speed_str = initial_speed_str.replace('.0x','x')
        self.speed_var.set(initial_speed_str)
        speeds = ["0.5x", "0.75x", "1.0x", "1.25x", "1.5x", "1.75x", "2.0x"]
        speed_menu = ttk.Combobox(speed_frame, textvariable=self.speed_var, width=5,
                                  values=speeds, state="readonly")
        speed_menu.pack(side=tk.LEFT, padx=(5, 0))
        # Use lambda to pass the selected value from the event's widget
        speed_menu.bind("<<ComboboxSelected>>", lambda event: self.commands['set_speed'](event.widget.get()))


    def update_display(self, update_path=True, update_time=True, update_play_button=True):
        '''Updates the UI elements in this control section.'''
        if update_path:
            try:
                # Check if the ENTRY widget exists before setting the variable
                if hasattr(self, 'audio_path_entry') and self.audio_path_entry.winfo_exists(): # Check the ENTRY widget
                    self.audio_path_var.set(self.state.get_audio_basename())
            except tk.TclError: pass # Ignore if widget destroyed

        if update_time:
            current_t_val = self.commands.get('get_current_time', lambda: self.state.current_position)()
            current_t = format_time(current_t_val)
            total_t = format_time(self.state.audio_duration)
            try:
                # Check if the LABEL widget exists before setting the variable
                if hasattr(self, 'time_display_label') and self.time_display_label.winfo_exists(): # Check the LABEL widget
                    self.time_display_var.set(f"{current_t} / {total_t}")
            except tk.TclError: pass
            self._update_stop_button_state()

        if update_play_button:
            try:
                if self.play_button and self.play_button.winfo_exists(): # Check button exists
                     self.play_button.config(text="Pause" if self.state.is_playing else "Play")
            except tk.TclError: pass # Ignore if widget destroyed
            self._update_stop_button_state()

    def _update_stop_button_state(self):
        '''Enable/disable the stop button based on state.'''
        if hasattr(self, 'stop_button') and self.stop_button:
            try:
                if self.stop_button.winfo_exists():
                    if self.state.is_playing or self.state.current_position > 0.001:
                        self.stop_button.config(state=tk.NORMAL)
                    else:
                        self.stop_button.config(state=tk.DISABLED)
            except tk.TclError: pass


# END OF FILE ui/audio_controls.py