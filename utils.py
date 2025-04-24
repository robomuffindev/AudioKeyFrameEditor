import re
import numpy as np

# --- Constants ---
SKIP_TIME_SECONDS = 5
WAVEFORM_UPDATE_INTERVAL_MS = 50 # More frequent updates for smoother playback marker
RESIZE_DEBOUNCE_MS = 250
DEFAULT_SAMPLE_RATE_TARGET = 22050 # Lower SR for faster loading/plotting if needed
MAX_WAVEFORM_SAMPLES = 500000 # Limit samples for waveform display performance

# --- Utility Functions ---

def natural_sort_key(s):
    '''Sort strings containing numbers naturally (1, 2, 10 instead of 1, 10, 2).'''
    return [int(text) if text.isdigit() else text.lower()
            for text in re.split(r'(\d+)', s)]

def format_time(seconds):
    '''Format time in seconds to MM:SS.mmm format.'''
    if seconds is None or not isinstance(seconds, (int, float)):
        return "00:00.000"
    seconds = max(0, seconds) # Ensure non-negative
    minutes = int(seconds // 60)
    sec = seconds % 60
    return f"{minutes:02d}:{sec:06.3f}"

def clamp(value, min_value, max_value):
    '''Clamps a value within a range.'''
    return max(min_value, min(value, max_value))

def find_nearest_keyframe_index(keyframes, time_seconds, tolerance=0.05):
    '''Finds the index of the nearest keyframe within a tolerance.'''
    min_dist = float('inf')
    nearest_index = -1
    for i, kf in enumerate(keyframes):
        dist = abs(kf['time'] - time_seconds)
        if dist < min_dist and dist <= tolerance:
            min_dist = dist
            nearest_index = i
    return nearest_index

# END OF FILE utils.py
