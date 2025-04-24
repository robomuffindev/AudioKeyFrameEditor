# START OF FILE handlers/audio_handler.py
import os
import pygame
import librosa
import numpy as np
from tkinter import messagebox
# Ensure utils is importable
try:
    from utils import DEFAULT_SAMPLE_RATE_TARGET, MAX_WAVEFORM_SAMPLES, format_time
except ImportError:
    print("ERROR: Cannot import from utils.py in audio_handler. Ensure it's accessible.")
    # Fallback values if import fails, though app likely won't work fully
    DEFAULT_SAMPLE_RATE_TARGET = 22050
    MAX_WAVEFORM_SAMPLES = 500000
    def format_time(s): return f"{s:.3f}s" # Basic fallback


class AudioHandler:
    '''Handles audio loading and playback.'''

    def __init__(self, app_state, update_callback):
        '''
        Args:
            app_state (AppState): The shared application state.
            update_callback (callable): Function to call for UI updates after actions.
        '''
        self.state = app_state
        self.update_ui = update_callback
        try:
            pygame.init()
            pygame.mixer.init()
        except pygame.error as e:
            messagebox.showerror("Audio Error", f"Failed to initialize audio playback: {e}\\nPlayback will be disabled.")
            self.mixer_initialized = False
        else:
            self.mixer_initialized = True

    def load_audio(self, file_path):
        '''Loads an audio file, updates state, and triggers UI update.'''
        if not file_path: return False
        try:
            self.stop_playback()
            self.state.reset_audio_state()
            self.state.audio_file = file_path
            target_sr = DEFAULT_SAMPLE_RATE_TARGET
            print(f"Loading audio: {file_path} at target SR: {target_sr}")
            try:
                 self.state.audio_data, self.state.sample_rate = librosa.load(file_path, sr=target_sr, mono=True)
            except Exception as librosa_err:
                 print(f"Librosa load failed: {librosa_err}. Trying simple load for duration.")
                 try:
                     self.state.audio_duration = librosa.get_duration(filename=file_path)
                     effective_sr = target_sr or 44100
                     self.state.audio_data = np.zeros(int(self.state.audio_duration * effective_sr))
                     self.state.sample_rate = effective_sr
                     messagebox.showwarning("Audio Load Warning", f"Could not fully load audio data with Librosa: {librosa_err}\\nWaveform accuracy might be limited.")
                 except Exception as duration_err:
                      raise RuntimeError(f"Failed to load audio or get duration: {duration_err}") from duration_err

            if self.state.audio_data is None: raise ValueError("Loaded audio data is None.")

            if np.any(self.state.audio_data): self.state.audio_data = librosa.util.normalize(self.state.audio_data)
            else: print("Warning: Loaded audio appears silent or empty.")

            if self.state.sample_rate and len(self.state.audio_data) > 0:
                 self.state.audio_duration = len(self.state.audio_data) / self.state.sample_rate
            elif self.state.audio_duration <= 0.0:
                 if len(self.state.audio_data) > 0 and self.state.sample_rate > 0:
                      self.state.audio_duration = len(self.state.audio_data) / self.state.sample_rate
                 else: raise ValueError("Could not determine audio duration.")

            print(f"Audio loaded. Duration: {self.state.audio_duration:.3f}s, Sample Rate: {self.state.sample_rate}")

            # No waveform data needed anymore

            if self.mixer_initialized:
                pygame.mixer.music.load(file_path)
                print("Audio loaded into Pygame mixer.")
            else: messagebox.showwarning("Audio Warning", "Audio mixer not initialized. Playback disabled.")

            self.state.status_message = f"Loaded audio: {self.state.get_audio_basename()}"
            # Trigger main UI update AFTER loading is complete
            # Include timeline_keyframes to ensure it redraws with the new duration/markers
            self.update_ui(time=True, status=True, file_paths=True, keyframes=True, timeline_keyframes=True)
            return True

        except Exception as e:
            print(f"ERROR loading audio: {e}")
            import traceback
            traceback.print_exc()
            self.state.reset_audio_state()
            self.state.status_message = "Error loading audio."
            messagebox.showerror("Error", f"Failed to load audio file '{os.path.basename(file_path)}':\\n{e}")
            # Include timeline_keyframes to ensure it redraws in error state
            self.update_ui(time=True, status=True, file_paths=True, keyframes=True, timeline_keyframes=True)
            return False


    def _start_internal_playback_tracking(self):
         '''Resets the timer used for manual position tracking.'''
         self.state._playback_start_offset = self.state.current_position
         self.state._last_update_tick = pygame.time.get_ticks()

    def toggle_playback(self):
        '''Toggles audio playback between play and pause.'''
        if not self.state.has_audio() or not self.mixer_initialized:
            messagebox.showinfo("Playback Info", "Please load an audio file first.")
            return

        if self.state.is_playing:
            pygame.mixer.music.pause()
            self.state.is_playing = False
            self.state.current_position = self.get_current_playback_position()
            self.state.status_message = f"Playback paused at {format_time(self.state.current_position)}"
            print(f"Playback paused at {self.state.current_position:.3f}s")
        else:
            is_resuming = pygame.mixer.music.get_busy()
            if self.state.audio_duration > 0 and abs(self.state.audio_duration - self.state.current_position) < 0.05:
                 print("Near end, restarting playback from beginning.")
                 self.state.current_position = 0.0
            try:
                if is_resuming:
                     pygame.mixer.music.unpause()
                     print(f"Resuming playback from {self.state.current_position:.3f}s")
                else:
                     pygame.mixer.music.stop()
                     pygame.mixer.music.play(start=self.state.current_position)
                     print(f"Starting playback at {self.state.current_position:.3f}s")
                self._start_internal_playback_tracking()
                self.state.is_playing = True
                self.state.status_message = "Playback started."
            except pygame.error as e:
                 messagebox.showerror("Playback Error", f"Could not start or resume playback: {e}")
                 self.state.is_playing = False
                 self.state.status_message = "Playback error."

        # Time update will trigger timeline marker update via update_ui
        self.update_ui(play_button=True, status=True, time=True)


    def stop_playback(self):
        '''Stops audio playback and resets position to 0.'''
        if not self.state.has_audio() or not self.mixer_initialized: return

        pygame.mixer.music.stop()
        self.state.is_playing = False
        self.state.current_position = 0.0
        self.state._playback_start_offset = 0.0
        self.state._last_update_tick = pygame.time.get_ticks()
        print("Playback stopped and reset to 0.")
        self.state.status_message = "Playback stopped."
        # Time update will trigger timeline marker update
        self.update_ui(play_button=True, status=True, time=True, current_slide=True)


    def seek(self, time_seconds):
        '''Seeks to a specific time in the audio.'''
        if not self.state.has_audio(): return
        if not self.mixer_initialized:
             new_position = max(0, min(time_seconds, self.state.audio_duration))
             self.state.current_position = new_position
             self.state.status_message = f"Seeked to {format_time(self.state.current_position)} (Playback disabled)"
             # Time update will trigger timeline marker update
             self.update_ui(time=True, current_slide=True, status=True)
             return

        new_position = max(0, min(time_seconds, self.state.audio_duration))
        if abs(new_position - self.state.current_position) < 0.001:
             # Update UI even if no seek needed, in case state was slightly off
             self.update_ui(time=True, current_slide=True)
             return

        self.state.current_position = new_position
        print(f"Seeking to {new_position:.3f}s")
        was_playing = self.state.is_playing
        if was_playing:
             try:
                 pygame.mixer.music.stop()
                 pygame.mixer.music.play(start=self.state.current_position)
                 self._start_internal_playback_tracking()
                 print("Restarted playback after seek.")
             except pygame.error as e:
                 messagebox.showerror("Playback Error", f"Could not seek during playback: {e}")
                 self.state.is_playing = False
                 self.update_ui(play_button=True)
                 self.state.status_message = "Playback error during seek."
        else:
             self._start_internal_playback_tracking()

        self.state.status_message = f"Seeked to {format_time(self.state.current_position)}"
        # Time update will trigger timeline marker update
        self.update_ui(time=True, current_slide=True, status=True)


    def skip_time(self, delta_seconds):
        '''Skips forward or backward by a relative amount.'''
        if not self.state.has_audio(): return
        current_time = self.get_current_playback_position()
        new_time = current_time + delta_seconds
        self.seek(new_time)


    def get_current_playback_position(self):
         '''Gets the most accurate current position, using internal timer if playing.'''
         if self.state.is_playing and self.mixer_initialized:
              current_real_time = pygame.time.get_ticks()
              delta_time_ms = current_real_time - self.state._last_update_tick
              elapsed_since_start = (delta_time_ms / 1000.0) * self.state.playback_speed
              estimated_position = self.state._playback_start_offset + elapsed_since_start
              # Clamp, ensuring duration is positive before using it
              max_pos = self.state.audio_duration if self.state.audio_duration > 0 else 0
              return max(0, min(estimated_position, max_pos))
         else:
              return self.state.current_position


    def update_playback_position(self):
        '''Called periodically to update the current playback time state.'''
        if not self.mixer_initialized:
             if self.state.is_playing:
                 self.state.is_playing = False
                 self.update_ui(play_button=True)
             return False

        if self.state.is_playing:
            if not pygame.mixer.music.get_busy():
                final_estimated_pos = self.get_current_playback_position()
                if self.state.audio_duration > 0 and abs(final_estimated_pos - self.state.audio_duration) < 0.15 :
                     self.state.current_position = self.state.audio_duration
                     self.state.status_message = "Playback finished."
                     print("Playback finished (mixer not busy, near end).")
                else:
                     print(f"Warning: Playback stopped unexpectedly. Mixer not busy. Estimated pos: {final_estimated_pos:.3f}s")
                     self.state.current_position = final_estimated_pos
                self.state.is_playing = False
                self.update_ui(play_button=True, status=True, time=True) # Time update triggers timeline marker update
                return False

            else:
                new_position = self.get_current_playback_position()
                position_changed = abs(new_position - self.state.current_position) > 0.001
                self.state.current_position = new_position

                if self.state.audio_duration > 0 and self.state.current_position >= self.state.audio_duration:
                     self.state.current_position = self.state.audio_duration
                     self.state.is_playing = False
                     pygame.mixer.music.stop()
                     self.state.status_message = "Playback finished."
                     self.update_ui(play_button=True, status=True, time=True) # Time update triggers timeline marker update
                     print("Playback finished (timer reached duration).")
                     return False

                if position_changed:
                    # Time update triggers timeline marker update
                    self.update_ui(time=True, current_slide=True)
                return True

        elif pygame.mixer.music.get_busy():
             print("Warning: Internal state is NOT playing, but Pygame mixer IS busy. Stopping mixer.")
             pygame.mixer.music.stop()
             return False

        return False


    def set_playback_speed(self, speed_str):
        '''Sets the playback speed (currently affects internal timer only).'''
        try:
            speed = float(speed_str.rstrip('x'))
            if speed <= 0: raise ValueError("Speed must be positive.")
            if abs(speed - self.state.playback_speed) > 0.01:
                 print(f"Setting visual playback speed to {speed:.2f}x")
                 self.state.playback_speed = speed
                 if self.state.is_playing:
                      self._start_internal_playback_tracking()
                 self.state.status_message = f"Visual playback speed set to {speed:.2f}x"
                 self.update_ui(status=True)

        except ValueError as e:
            messagebox.showerror("Error", f"Invalid speed value: {speed_str}\\n{e}")


# END OF FILE handlers/audio_handler.py