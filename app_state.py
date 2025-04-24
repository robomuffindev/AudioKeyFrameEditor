# START OF FILE app_state.py
import os
import numpy as np

class AppState:
    '''Centralized class to hold and manage application state.'''

    def __init__(self):
        # Audio related state
        self.audio_file = None
        self.audio_data = None # Keep audio data for duration calculation etc.
        # self.waveform_data = None # Removed - No longer displaying waveform
        self.sample_rate = None
        self.audio_duration = 0.0
        self.is_playing = False
        self.current_position = 0.0 # Playback position in seconds
        self.playback_speed = 1.0 # Currently visual only for Pygame playback
        self._playback_start_offset = 0.0 # Time where current playback segment started
        self._last_update_tick = 0 # For manual time tracking during playback

        # Slide related state
        self.slides_directory = None
        self.slide_files = [] # List of full slide file paths
        self.current_slide_index = -1 # Index in slide_files for current display
        self.loaded_slide_image = None # PIL image (cache if needed)
        self.loaded_slide_photo = None # Tkinter PhotoImage (cache, IMPORTANT ref)

        # Keyframe related state
        self.keyframes = [] # List of dicts: {'time': float, 'slideIndex': int}
        self.selected_keyframe_index = -1

        # UI / Interaction State
        # self.waveform_zoom_level = 1.0 # Removed
        # self.waveform_pan_active = False # Removed
        # self.waveform_pan_start_x_pixel = None # Removed
        # self.waveform_pan_start_x_data_limits = None # Removed
        # self.dragging_keyframe_index = -1 # Removed - No waveform to drag on
        self.status_message = "Ready"
        self.create_keyframe_at_zero = True # Flag to add initial keyframe

    def reset_audio_state(self):
        self.audio_file = None
        self.audio_data = None
        # self.waveform_data = None # Removed
        self.sample_rate = None
        self.audio_duration = 0.0
        self.is_playing = False
        self.current_position = 0.0
        self._playback_start_offset = 0.0
        self._last_update_tick = 0
        self.keyframes = []
        self.selected_keyframe_index = -1
        # self.dragging_keyframe_index = -1 # Removed
        # Don't reset create_keyframe_at_zero here

    def reset_slide_state(self):
        self.slides_directory = None
        self.slide_files = []
        self.current_slide_index = -1
        self.loaded_slide_image = None
        self.loaded_slide_photo = None

    def get_audio_basename(self):
        return os.path.basename(self.audio_file) if self.audio_file else "None selected"

    def get_slides_basename(self):
        return os.path.basename(self.slides_directory) if self.slides_directory else "None selected"

    def get_current_keyframe(self):
        if 0 <= self.selected_keyframe_index < len(self.keyframes):
            return self.keyframes[self.selected_keyframe_index]
        return None

    def get_slide_path_for_index(self, index):
        if 0 <= index < len(self.slide_files):
            return self.slide_files[index]
        return None

    def get_slide_filename_for_index(self, index):
        path = self.get_slide_path_for_index(index)
        return os.path.basename(path) if path else "N/A"

    def has_audio(self):
        return self.audio_file is not None and self.audio_duration > 0

    def has_slides(self):
        return bool(self.slide_files)

    def has_keyframes(self):
        return bool(self.keyframes)

# END OF FILE app_state.py