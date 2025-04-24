# START OF FILE handlers/event_handler.py
import tkinter as tk
from tkinter import simpledialog, messagebox
import numpy as np
import inspect # For checking function signatures
# Ensure utils is importable
try:
    from utils import SKIP_TIME_SECONDS, find_nearest_keyframe_index, format_time
except ImportError:
    print("ERROR: Cannot import from utils.py in event_handler. Ensure it's accessible.")
    # Define fallbacks or re-raise? For now, define basic fallbacks.
    SKIP_TIME_SECONDS = 5
    def find_nearest_keyframe_index(*args, **kwargs): return -1
    def format_time(s): return f"{s:.3f}s"


class EventHandler:
    '''Handles user interactions like key presses, clicks, drags.'''

    # Constructor now expects timeline_canvas instead of waveform_canvas
    def __init__(self, app_state, audio_handler, slide_handler, keyframe_handler, ui_updater, root, timeline_canvas, keyframes_listbox):
        self.state = app_state
        self.audio_h = audio_handler
        self.slide_h = slide_handler
        self.keyframe_h = keyframe_handler
        self.update_ui = ui_updater
        self.root = root
        self.timeline_canvas = timeline_canvas # Store ref to the actual Canvas widget
        self.keyframes_listbox = keyframes_listbox

        # Define key bindings
        self.key_bindings = {
            '<space>': lambda e: self.audio_h.toggle_playback(),
            '<Left>': lambda e: self.audio_h.skip_time(-SKIP_TIME_SECONDS),
            '<Right>': lambda e: self.audio_h.skip_time(SKIP_TIME_SECONDS),
            '<k>': lambda e: self.keyframe_h.add_keyframe(self.audio_h.get_current_playback_position()),
            '<Delete>': lambda e: self.keyframe_h.delete_keyframe(self.state.selected_keyframe_index),
            '<BackSpace>': lambda e: self.keyframe_h.delete_keyframe(self.state.selected_keyframe_index),
            '<Home>': lambda e: self.audio_h.seek(0),
            '<End>': lambda e: self.audio_h.seek(self.state.audio_duration) if self.state.has_audio() else None,
            '<Control-e>': lambda e: self.edit_selected_keyframe_time(),
             '<Control-s>': self._get_command('export_keyframes'),
             '<Control-o>': self._get_command('open_audio'),
             '<Control-l>': self._get_command('select_slides'),
             '<Control-i>': self._get_command('import_keyframes'),
        }

    def _get_command(self, cmd_key):
        '''Safely get command from main window, returns a no-op lambda if not found.'''
        if hasattr(self.root, '_get_ui_commands'):
            commands_dict = self.root._get_ui_commands()
            cmd = commands_dict.get(cmd_key, lambda *args, **kwargs: None)
            return lambda e: cmd(e) if self._accepts_event(cmd) else cmd()
        else:
            print(f"Warning: Cannot get command '{cmd_key}', _get_ui_commands not ready.")
            return lambda *args, **kwargs: None


    def bind_events(self):
        '''Binds all defined events to their respective widgets.'''
        print("Binding application events...")
        # -- Keyboard Shortcuts --
        for key, action in self.key_bindings.items():
            try:
                self.root.bind(key, action)
            except Exception as e: print(f"Error binding key '{key}': {e}")

        # -- Keyframe Listbox Events --
        if self.keyframes_listbox:
            print("Binding keyframe listbox events...")
            try:
                if self.keyframes_listbox.winfo_exists():
                    self.keyframes_listbox.bind('<<ListboxSelect>>', self.on_keyframe_list_select)
                    self.keyframes_listbox.bind('<Double-Button-1>', self.on_keyframe_list_double_click)
                    self.keyframes_listbox.bind('<Control-e>', self.edit_selected_keyframe_time)
                    self.keyframes_listbox.bind('<Delete>', lambda e: self.keyframe_h.delete_keyframe(self.state.selected_keyframe_index))
                    self.keyframes_listbox.bind('<BackSpace>', lambda e: self.keyframe_h.delete_keyframe(self.state.selected_keyframe_index))
            except Exception as e: print(f"Error binding to keyframe listbox: {e}")

        # -- Timeline Canvas Events --
        if self.timeline_canvas: # Check if the canvas widget itself was passed
             print("Binding timeline canvas events...")
             try:
                 if self.timeline_canvas.winfo_exists():
                     # Bind button press directly to the canvas widget's internal method
                     # Get the method from the *instance* of TimelineCanvas if needed
                     timeline_instance = self.timeline_canvas.master # Get the TimelineCanvas frame instance
                     if hasattr(timeline_instance, '_on_click'):
                         self.timeline_canvas.bind("<Button-1>", timeline_instance._on_click)
                     else:
                          print("ERROR: TimelineCanvas instance missing _on_click method.")

             except Exception as e: print(f"Error binding to timeline canvas: {e}")

        print("Event binding process finished.")

    def _accepts_event(self, func):
         '''Checks if a function likely accepts an event argument.'''
         try:
             target_func = func
             while hasattr(target_func, 'func'): target_func = target_func.func
             if not callable(target_func): return False
             sig = inspect.signature(target_func)
             takes_at_least_one = len(sig.parameters) > 0
             return takes_at_least_one
         except (ValueError, TypeError): return False

    # --- Specific Event Handlers ---

    def on_keyframe_list_select(self, event=None):
        '''Handles selection change in the keyframes listbox.'''
        if not self.keyframes_listbox: return
        try:
            if not self.keyframes_listbox.winfo_exists(): return
            selection = self.keyframes_listbox.curselection()
            if selection:
                index = selection[0]
                if 0 <= index < len(self.state.keyframes):
                    self.keyframe_h.select_keyframe(index)
                else: self.keyframe_h.select_keyframe(-1)
            else:
                if self.state.selected_keyframe_index != -1:
                     self.keyframe_h.select_keyframe(-1)
        except tk.TclError: pass

    def on_keyframe_list_double_click(self, event=None):
         '''Handles double-click on keyframe list: edit time.'''
         if not self.keyframes_listbox: return
         try:
             if not self.keyframes_listbox.winfo_exists(): return
             selection = self.keyframes_listbox.curselection()
             if selection and (0 <= selection[0] < len(self.state.keyframes)):
                  self.edit_selected_keyframe_time()
         except tk.TclError: pass


    def edit_selected_keyframe_time(self, event=None):
        '''Opens a dialog to edit the selected keyframe's time.'''
        if not self.root or not self.root.winfo_exists(): return
        if not self.state.has_audio():
             messagebox.showwarning("Edit Time", "Cannot edit keyframes without loaded audio.", parent=self.root)
             return
        if not (0 <= self.state.selected_keyframe_index < len(self.state.keyframes)):
            messagebox.showinfo("Edit Time", "Please select a keyframe in the list first.", parent=self.root)
            return

        kf_index = self.state.selected_keyframe_index
        current_kf = self.state.keyframes[kf_index]
        current_time_str = f"{current_kf['time']:.3f}"

        new_time_str = simpledialog.askstring(
            "Edit Keyframe Time",
            f"Enter new time (in seconds) for Keyframe {kf_index + 1}:"
            f"\nCurrent time: {format_time(current_kf['time'])}",
            initialvalue=current_time_str, parent=self.root
        )

        if new_time_str is not None:
            try:
                new_time = float(new_time_str)
                new_time_clamped = max(0, min(new_time, self.state.audio_duration))
                if abs(new_time - new_time_clamped) > 0.0001:
                     messagebox.showwarning("Input Warning",
                        f"Time {new_time:.3f}s is outside audio duration (0.0s - {self.state.audio_duration:.3f}s).\n"
                        f"Using clamped value: {new_time_clamped:.3f}s.", parent=self.root)
                     new_time = new_time_clamped

                if kf_index == 0 and abs(current_kf['time']) < 0.001 and abs(new_time) > 0.01:
                    if not messagebox.askyesno("Confirm Edit", "The first keyframe is usually at 0.0s. Move it?", parent=self.root):
                         return

                self.keyframe_h.update_keyframe_time(kf_index, new_time)

            except ValueError:
                messagebox.showerror("Invalid Input", "Invalid time format.\nPlease enter a number (e.g., 12.345).", parent=self.root)
            except Exception as e:
                 messagebox.showerror("Error", f"Could not update keyframe time:\n{e}", parent=self.root)

        if self.keyframes_listbox:
             try:
                 if self.keyframes_listbox.winfo_exists(): self.keyframes_listbox.focus_set()
             except tk.TclError: pass


# END OF FILE handlers/event_handler.py