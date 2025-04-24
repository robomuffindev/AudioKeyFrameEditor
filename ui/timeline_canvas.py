# START OF FILE ui/timeline_canvas.py
import tkinter as tk
from tkinter import ttk
# Ensure utils is importable
try:
    from utils import format_time
except ImportError:
    print("ERROR: Cannot import from utils.py in timeline_canvas. Ensure it's accessible.")
    def format_time(s): return f"{s:.3f}s" # Basic fallback

class TimelineCanvas(ttk.Frame):
    '''A simple canvas widget to display a timeline, keyframes, and position.'''

    # Define constants for colors and dimensions
    TIMELINE_HEIGHT = 40
    TIMELINE_BG = "#E0E0E0" # Light grey background
    LINE_COLOR = "#555555" # Dark grey for main line
    POS_MARKER_COLOR = "#34D399" # Emerald green
    KF_MARKER_COLOR = "#FF4136" # Red
    KF_SELECTED_COLOR = "#FF8C00" # Orange
    KF_MARKER_HEIGHT = 15 # Height of keyframe lines
    POS_MARKER_HEIGHT = 25 # Height of position marker
    CLICK_PADDING = 5 # Pixels padding for click calculation

    def __init__(self, parent, app_state, commands, **kwargs):
        super().__init__(parent, **kwargs)
        self.state = app_state
        self.commands = commands # Expect 'seek' command

        self._canvas_width = 1 # Initialize width
        # Ratios removed, calculated on the fly

        self.create_widgets()
        # Binding moved to main_window after event_handler is initialized

    def create_widgets(self):
        self.canvas = tk.Canvas(self, height=self.TIMELINE_HEIGHT, bg=self.TIMELINE_BG,
                                highlightthickness=1, highlightbackground="#AAAAAA")
        self.canvas.pack(fill=tk.X, expand=True, padx=5, pady=5)

        # Create reusable canvas items (we'll move/recolor them later)
        self.timeline_line = self.canvas.create_line(0, 0, 0, 0, fill=self.LINE_COLOR, width=2)
        self.pos_marker_line = self.canvas.create_line(0, 0, 0, 0, fill=self.POS_MARKER_COLOR, width=2)
        self._keyframe_lines = [] # Store canvas item IDs for keyframes

    # Binding events is now handled in the main window's event handler setup

    def _time_to_pixel(self, time_sec):
        '''Convert time in seconds to horizontal pixel coordinate.'''
        # Ensure canvas width is current before calculation
        self._canvas_width = self.canvas.winfo_width()
        if self.state.audio_duration <= 0 or self._canvas_width <= (2 * self.CLICK_PADDING):
            return self.CLICK_PADDING # Return start padding if invalid state

        # Calculate ratio based on current width, consider padding
        drawable_width = self._canvas_width - (2 * self.CLICK_PADDING)
        pixel_pos = self.CLICK_PADDING + (time_sec / self.state.audio_duration) * drawable_width
        # Clamp result within the padded area
        return int(max(self.CLICK_PADDING, min(pixel_pos, self._canvas_width - self.CLICK_PADDING)))

    def _pixel_to_time(self, pixel_x):
        '''Convert horizontal pixel coordinate to time in seconds.'''
        self._canvas_width = self.canvas.winfo_width() # Update width
        if self.state.audio_duration <= 0 or self._canvas_width <= (2 * self.CLICK_PADDING):
            return 0

        drawable_width = self._canvas_width - (2 * self.CLICK_PADDING)
        if drawable_width <= 0: return 0

        # Clamp pixel_x within the drawable area before calculating time
        clamped_pixel_x = max(self.CLICK_PADDING, min(pixel_x, self._canvas_width - self.CLICK_PADDING))
        time_sec = ((clamped_pixel_x - self.CLICK_PADDING) / drawable_width) * self.state.audio_duration
        # Clamp result to valid time range
        return max(0, min(time_sec, self.state.audio_duration))


    def _on_resize(self, event):
        '''Handle canvas resize events.'''
        # Update width and redraw everything
        new_width = event.width
        # Prevent excessive redraws if width hasn't changed significantly
        if abs(new_width - self._canvas_width) > 1: # Use smaller threshold
            self._canvas_width = new_width
            # print(f"Timeline resized to: {self._canvas_width}")
            self.redraw_all()


    def _on_click(self, event):
        '''Handle clicks on the timeline to seek.'''
        if not self.state.has_audio(): return
        try:
            target_time = self._pixel_to_time(event.x)
            print(f"Timeline clicked at pixel {event.x}, seeking to time {target_time:.3f}s")
            # Call the seek command provided by the main window
            seek_cmd = self.commands.get('seek')
            if seek_cmd:
                seek_cmd(target_time)
            else:
                print("Warning: Seek command not found.")
        except Exception as e:
            print(f"Error during timeline click handling: {e}")


    def redraw_all(self):
        '''Redraw the entire timeline, markers, and keyframes.'''
        # Avoid errors if widget destroyed during redraw calls (e.g., on close)
        try:
            if not self.winfo_exists(): return
            self._canvas_width = self.canvas.winfo_width() # Ensure width is up-to-date
            if self._canvas_width <= 1: return # Don't draw if not visible yet
        except tk.TclError: return

        # Center Y position for the main timeline
        center_y = self.TIMELINE_HEIGHT // 2

        # 1. Draw main timeline line
        padding = self.CLICK_PADDING
        try:
            self.canvas.coords(self.timeline_line, padding, center_y, self._canvas_width - padding, center_y)
            self.canvas.itemconfig(self.timeline_line, fill=self.LINE_COLOR, state=tk.NORMAL)
        except tk.TclError: return # Stop if canvas destroyed

        # 2. Draw Keyframes (efficiently manage items)
        try:
            num_needed = len(self.state.keyframes)
            num_existing = len(self._keyframe_lines)

            # Add new lines if needed
            for _ in range(num_needed - num_existing):
                line_id = self.canvas.create_line(0, 0, 0, 0, width=1, state=tk.HIDDEN) # Create hidden initially
                self._keyframe_lines.append(line_id)

            # Update positions and colors, hide/show as needed
            kf_y1 = center_y - self.KF_MARKER_HEIGHT // 2
            kf_y2 = center_y + self.KF_MARKER_HEIGHT // 2
            for i in range(max(num_needed, num_existing)):
                line_id = self._keyframe_lines[i]
                if i < num_needed:
                    kf = self.state.keyframes[i]
                    x_pos = self._time_to_pixel(kf['time'])
                    is_selected = (i == self.state.selected_keyframe_index)
                    color = self.KF_SELECTED_COLOR if is_selected else self.KF_MARKER_COLOR
                    width = 2 if is_selected else 1

                    self.canvas.coords(line_id, x_pos, kf_y1, x_pos, kf_y2)
                    self.canvas.itemconfig(line_id, fill=color, width=width, state=tk.NORMAL)
                else: # Hide unused existing lines beyond num_needed
                     self.canvas.itemconfig(line_id, state=tk.HIDDEN)

            # Trim the list if it became shorter
            if num_existing > num_needed:
                self._keyframe_lines = self._keyframe_lines[:num_needed]

        except tk.TclError: return
        except Exception as e: print(f"Error drawing keyframes: {e}")

        # 3. Draw Position Marker
        try:
            self.update_position_marker()
        except tk.TclError: return


    def update_position_marker(self):
        '''Update only the position marker's location.'''
        try:
            if not self.winfo_exists(): return
            if not self.state.has_audio():
                self.canvas.itemconfig(self.pos_marker_line, state=tk.HIDDEN)
                return

            center_y = self.TIMELINE_HEIGHT // 2
            pos_y1 = center_y - self.POS_MARKER_HEIGHT // 2
            pos_y2 = center_y + self.POS_MARKER_HEIGHT // 2
            x_pos = self._time_to_pixel(self.state.current_position)

            self.canvas.coords(self.pos_marker_line, x_pos, pos_y1, x_pos, pos_y2)
            self.canvas.itemconfig(self.pos_marker_line, state=tk.NORMAL, fill=self.POS_MARKER_COLOR)
        except tk.TclError: pass # Ignore if closing
        except Exception as e: print(f"Error updating position marker: {e}")

    def update_keyframe_markers(self):
        '''Update only the keyframe markers (color, position).'''
        # Currently redraws everything for simplicity, could be optimized
        # to only reconfigure existing lines if performance becomes an issue.
        self.redraw_all()


# END OF FILE ui/timeline_canvas.py