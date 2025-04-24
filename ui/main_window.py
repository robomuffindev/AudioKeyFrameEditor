# START OF FILE ui/main_window.py
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import sys # For sys.exit
import pygame # For timer/ticks
import traceback # For printing detailed errors
# Matplotlib import removed

# Need to import AppState and utils before handlers/UI that use them
try:
    from app_state import AppState
    from utils import RESIZE_DEBOUNCE_MS, WAVEFORM_UPDATE_INTERVAL_MS, format_time
except ImportError as e:
    print(f"ERROR: Failed to import core modules (app_state, utils): {e}")
    traceback.print_exc()
    # Show error immediately if possible
    try: messagebox.showerror("Import Error", f"Failed to import core modules: {e}")
    except: pass
    sys.exit(1)


# UI Components - Add error handling for these imports too
try:
    from ui.menu_bar import create_menu_bar
    from ui.slides_viewer import SlidesViewer
    from ui.audio_controls import AudioControls
    from ui.timeline_canvas import TimelineCanvas # <<< Import new timeline
    # from ui.waveform_display import WaveformDisplay # Removed
    from ui.keyframes_list import KeyframesList
    from ui.status_bar import StatusBar
except ImportError as e:
    print(f"ERROR: Failed to import UI component: {e}")
    traceback.print_exc()
    try: messagebox.showerror("Import Error", f"Failed to import UI component: {e}")
    except: pass
    sys.exit(1)

# Handlers - Add error handling
try:
    from handlers.audio_handler import AudioHandler
    from handlers.slide_handler import SlideHandler
    from handlers.keyframe_handler import KeyframeHandler
    from handlers.event_handler import EventHandler
except ImportError as e:
    print(f"ERROR: Failed to import handler module: {e}")
    traceback.print_exc()
    try: messagebox.showerror("Import Error", f"Failed to import handler module: {e}")
    except: pass
    sys.exit(1)


class AudioKeyframeEditor(tk.Tk):
    '''Main application window orchestrating UI and handlers.'''

    def __init__(self):
        super().__init__()
        print("Initializing application window...")
        self.title("Audio Keyframe Editor")
        self.geometry("1280x800")
        self.minsize(800, 600) # Reduced minimum size slightly

        # Initialize Pygame timer subsystem (mixer is init'd in AudioHandler)
        try:
            pygame.init() # Safely initialize all Pygame modules
            pygame.time.Clock() # Create a clock object if needed
            print("Pygame initialized.")
        except pygame.error as e:
            print(f"CRITICAL ERROR: Pygame initialization failed: {e}")
            messagebox.showerror("Initialization Error", f"Pygame failed to initialize:\\n{e}\\nApplication cannot continue.")
            # Attempt graceful early exit
            try: self.destroy()
            except: pass
            sys.exit(1) # Exit process


        # Core Components
        print("Initializing state and handlers...")
        self.state = AppState()
        # Pass self.update_ui method reference to handlers
        self.audio_handler = AudioHandler(self.state, self.update_ui)
        self.slide_handler = SlideHandler(self.state, self.update_ui)
        self.keyframe_handler = KeyframeHandler(self.state, self.update_ui)

        # UI Elements (initialized to None, created in _create_layout)
        self.menu_bar = None
        self.slides_viewer = None
        self.audio_controls = None
        self.timeline_canvas = None # <<< Added timeline canvas reference
        # self.waveform_display = None # Removed
        self.keyframes_list = None
        self.status_bar = None
        self.event_handler = None # Initialize later

        # UI State
        self.resize_timer = None
        self._update_loop_id = None # Store the ID of the 'after' job

        # Create UI and Handlers
        print("Configuring style...")
        self._configure_style()
        print("Creating layout...")
        self._create_layout() # This creates UI widgets

        # Event Handler (needs UI widgets to exist)
        print("Initializing event handler...")
        self._initialize_event_handler() # This now initializes handler and starts loop


        # Handle window close event
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        print("Window initialization sequence complete.")


    def _configure_style(self):
        '''Configure the application's visual style.'''
        style = ttk.Style()
        try:
            # Prefer modern themes if available
            available_themes = style.theme_names()
            preferred_themes = ['clam', 'alt', 'vista'] # Order of preference
            chosen_theme = style.theme_use() # Get default
            for theme in preferred_themes:
                 if theme in available_themes:
                      try:
                          style.theme_use(theme)
                          chosen_theme = theme
                          print(f"Using theme: '{chosen_theme}'")
                          break
                      except tk.TclError:
                          continue # Try next theme if one fails
            print(f"Final theme in use: '{chosen_theme}'")

        except Exception as e: # Catch broader exceptions during theme setup
            print(f"Theme configuration error: {e}. Using default.")

        # Configure specific styles (add more as needed)
        style.configure('TButton', font=('Segoe UI', 10), padding=5)
        style.configure('Primary.TButton', foreground='white', background='#3b82f6') # Blue
        style.map('Primary.TButton', background=[('active', '#2563eb'), ('disabled', '#9ca3af')])
        style.configure('Success.TButton', foreground='white', background='#10b981') # Green
        style.map('Success.TButton', background=[('active', '#059669'), ('disabled', '#9ca3af')])
        style.configure('TLabel', font=('Segoe UI', 10))
        style.configure('TEntry', font=('Segoe UI', 10), padding=(3, 3)) # Add padding to entry
        style.configure('TCombobox', font=('Segoe UI', 10))
        style.configure('TLabelframe.Label', font=('Segoe UI', 10, 'bold'), padding=(0, 2))
        style.configure('TLabelframe', padding=(5, 5)) # Padding inside labelframe border


    def _create_layout(self):
        '''Creates the main UI layout panels.'''
        # Main content frame
        main_frame = ttk.Frame(self, padding="5")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Top panel: User-resizable split between slides and controls/waveform
        top_pane = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        top_pane.pack(fill=tk.BOTH, expand=True, pady=(0, 5))

        # Left Panel (Slides)
        left_frame_outer = ttk.Frame(top_pane, width=350, height=600) # Initial size guess
        left_frame_outer.pack_propagate(False) # Prevent shrinking below initial size
        self.slides_viewer = SlidesViewer(left_frame_outer, self.state, self._get_ui_commands())
        self.slides_viewer.pack(fill=tk.BOTH, expand=True)
        top_pane.add(left_frame_outer, weight=1) # Resizing weight


        # Right Panel (Audio/Timeline/Keyframes)
        right_frame_outer = ttk.Frame(top_pane, width=850, height=600) # Initial size guess
        right_frame_outer.pack_propagate(False)

        # *** CORRECTED PACKING ORDER FOR RIGHT PANEL ***
        # 1. Audio controls at the top
        self.audio_controls = AudioControls(right_frame_outer, self.state, self._get_ui_commands())
        self.audio_controls.pack(fill=tk.X, expand=False, pady=(0, 2))

        # 2. Timeline Canvas below controls
        self.timeline_canvas = TimelineCanvas(right_frame_outer, self.state, self._get_ui_commands())
        self.timeline_canvas.pack(fill=tk.X, expand=False, pady=(2, 5))

        # 3. Keyframes list takes the remaining space
        self.keyframes_list = KeyframesList(right_frame_outer, self.state, self._get_ui_commands())
        self.keyframes_list.pack(fill=tk.BOTH, expand=True, pady=(0, 0)) # Fill and expand

        top_pane.add(right_frame_outer, weight=3) # Give right side more resize weight


        # Bottom Status Bar
        self.status_bar = StatusBar(main_frame, self.state)
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM, pady=(5, 0))

        # Menu Bar
        self.menu_bar = create_menu_bar(self, self._get_ui_commands())

        # Bind window-level resize event
        self.bind("<Configure>", self._on_window_resize)

    def _initialize_event_handler(self):
         '''Creates and initializes the event handler after UI widgets exist.'''
         kf_listbox = self.keyframes_list.get_listbox() if hasattr(self, 'keyframes_list') and self.keyframes_list else None
         timeline_widget = self.timeline_canvas.canvas if hasattr(self, 'timeline_canvas') and self.timeline_canvas else None

         listbox_ready = isinstance(kf_listbox, tk.Listbox) and kf_listbox.winfo_exists()
         timeline_ready = isinstance(timeline_widget, tk.Canvas) and timeline_widget.winfo_exists()

         if not listbox_ready or not timeline_ready:
             print(f"WARNING: UI elements not ready for event handler. Listbox:{listbox_ready}, Timeline:{timeline_ready}. Retrying...")
             if self.winfo_exists():
                  self.after(100, self._initialize_event_handler)
             return

         print("UI elements ready, initializing event handler...")
         try:
             self.event_handler = EventHandler(
                self.state, self.audio_handler, self.slide_handler, self.keyframe_handler,
                self.update_ui, self, timeline_widget, kf_listbox # Pass actual timeline canvas widget
             )
             self.event_handler.bind_events() # Bind events explicitly
             print("Event handler initialized and events bound.")

             # Start periodic update loop only AFTER handler is ready
             print("Starting periodic update loop...")
             if self.winfo_exists():
                  self._update_loop_id = self.after(100, self.periodic_update) # Store ID

         except Exception as e:
              print(f"ERROR initializing EventHandler: {e}")
              traceback.print_exc()
              messagebox.showerror("Initialization Error", f"Failed to initialize event handler:\\n{e}")


    def _get_ui_commands(self):
        '''Returns a dictionary of commands, safely checking handler existence.'''
        handlers_ready = all(hasattr(self, name) and getattr(self, name) is not None
                            for name in ['audio_handler', 'slide_handler', 'keyframe_handler'])
        event_handler_ready = hasattr(self, 'event_handler') and self.event_handler is not None

        safe_lambda = lambda *args, **kwargs: None
        expected_keys = [
            'open_audio', 'select_slides', 'import_keyframes', 'export_keyframes', 'exit',
            'toggle_play', 'stop_play', 'seek', 'skip_fwd', 'skip_bwd', 'set_speed', 'get_current_time',
            'add_keyframe', 'delete_keyframe', 'edit_keyframe', 'get_formatted_keyframes', 'select_keyframe',
            'goto_start', 'goto_end', 'get_slide_for_display', 'show_instructions', 'show_about'
        ]
        all_commands = {k: safe_lambda for k in expected_keys}

        if not handlers_ready: return all_commands

        all_commands.update({
            'open_audio': self.open_audio_file,
            'select_slides': self.select_slides_folder,
            'import_keyframes': self.import_keyframes,
            'export_keyframes': self.export_keyframes,
            'exit': self._on_close,
            'toggle_play': self.audio_handler.toggle_playback,
            'stop_play': self.audio_handler.stop_playback,
            'seek': self.audio_handler.seek,
            'skip_fwd': lambda: self.audio_handler.skip_time(5),
            'skip_bwd': lambda: self.audio_handler.skip_time(-5),
            'set_speed': self.audio_handler.set_playback_speed,
            'get_current_time': self.audio_handler.get_current_playback_position,
            'add_keyframe': lambda: self.keyframe_handler.add_keyframe(self.audio_handler.get_current_playback_position()),
            'delete_keyframe': lambda: self.keyframe_handler.delete_keyframe(self.state.selected_keyframe_index),
            'get_formatted_keyframes': self.keyframe_handler.get_formatted_keyframes,
            'select_keyframe': self.keyframe_handler.select_keyframe,
            'goto_start': lambda: self.audio_handler.seek(0),
            'goto_end': lambda: self.audio_handler.seek(self.state.audio_duration) if self.state.has_audio() else None,
            'get_slide_for_display': self.slide_handler.get_slide_for_display,
            'show_instructions': self.show_instructions,
            'show_about': self.show_about,
        })
        if event_handler_ready:
            all_commands['edit_keyframe'] = self.event_handler.edit_selected_keyframe_time
        else:
            all_commands['edit_keyframe'] = safe_lambda

        return all_commands

    # --- Action Methods ---
    def open_audio_file(self):
        '''Handles the 'Open Audio' action.'''
        file_path = filedialog.askopenfilename(
            title="Select Audio File",
            filetypes=[("Audio Files", "*.wav *.mp3 *.ogg"), ("All Files", "*.*")],
            parent=self
        )
        if file_path:
            self.state.status_message = f"Loading audio: {os.path.basename(file_path)}..."
            self.update_ui(status=True)
            self.update()

            if self.audio_handler.load_audio(file_path):
                # Update timeline with new duration - USE self.update_ui
                self.update_ui(timeline_keyframes=True) # This implies redraw_all in current timeline code
                if self.state.create_keyframe_at_zero and not self.state.has_keyframes():
                    print("Adding initial keyframe at 0.0s")
                    self.keyframe_handler.add_keyframe(0.0) # This calls update_ui internally
                # Explicitly update slide and list after potential keyframe add
                self.update_ui(current_slide=True, keyframes=True, keyframes_list_selection=True)


    def select_slides_folder(self):
        '''Handles the 'Select Slides Folder' action.'''
        folder_path = filedialog.askdirectory(
             title="Select Slides Folder (containing 1.png, 2.png, ...)",
             parent=self
        )
        if folder_path:
            self.state.status_message = f"Loading slides from: {os.path.basename(folder_path)}..."
            self.update_ui(status=True)
            self.update()

            if self.slide_handler.load_slides(folder_path): pass

    def import_keyframes(self):
        '''Handles the 'Import Keyframes' action.'''
        if not self.state.has_audio():
            messagebox.showerror("Import Error", "Please load the corresponding audio file first.", parent=self)
            return
        file_path = filedialog.askopenfilename(
            title="Import Keyframes",
            defaultextension=".json",
            filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")],
            parent=self
        )
        if file_path:
            self.state.status_message = f"Importing keyframes: {os.path.basename(file_path)}..."
            self.update_ui(status=True)
            self.update()

            if self.keyframe_handler.import_keyframes(file_path):
                 # Update list, timeline, and slide after import
                 self.update_ui(keyframes=True, timeline_keyframes=True, keyframes_list_selection=True, current_slide=True)


    def export_keyframes(self):
        '''Handles the 'Export Keyframes' action.'''
        if not self.state.has_keyframes():
            messagebox.showinfo("Export", "No keyframes defined to export.", parent=self)
            return

        initial_filename = "keyframes.json"
        if self.state.audio_file:
             base, _ = os.path.splitext(os.path.basename(self.state.audio_file))
             initial_filename = f"{base}_keyframes.json"

        file_path = filedialog.asksaveasfilename(
            title="Save Keyframes",
            initialfile=initial_filename,
            defaultextension=".json",
            filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")],
            parent=self
        )
        if file_path:
            self.state.status_message = f"Exporting keyframes to {os.path.basename(file_path)}..."
            self.update_ui(status=True)
            self.update()

            self.keyframe_handler.export_keyframes(file_path)


    # --- UI Update Orchestration ---

    def update_ui(self, **kwargs):
        '''Central function to update specific parts of the UI.'''
        try:
             if not self.winfo_exists(): return
        except tk.TclError: return

        # Helper to safely call update methods on UI components
        def _try_update(widget, method_name, *args, **kw_args):
             if widget and hasattr(widget, method_name) and widget.winfo_exists():
                 try:
                      method = getattr(widget, method_name)
                      result = method(*args, **kw_args)
                      return result
                 except tk.TclError as e: pass
                 except Exception as e:
                      print(f"Error updating UI ({widget.__class__.__name__}.{method_name}): {e}")
                      traceback.print_exc()
             return None

        # --- Apply Updates Based on Flags ---

        if kwargs.get('file_paths', False):
            _try_update(self.audio_controls, 'update_display', update_path=True, update_time=False, update_play_button=False)
            _try_update(self.slides_viewer, 'update_display', update_path=True, update_slide=False)

        if kwargs.get('time', False):
            _try_update(self.audio_controls, 'update_display', update_path=False, update_time=True, update_play_button=False)
            _try_update(self.timeline_canvas, 'update_position_marker') # Update timeline position marker

        if kwargs.get('play_button', False):
            _try_update(self.audio_controls, 'update_display', update_path=False, update_time=False, update_play_button=True)

        if kwargs.get('keyframes', False): # List content update
            _try_update(self.keyframes_list, 'update_list')
            _try_update(self.timeline_canvas, 'update_keyframe_markers') # Update timeline markers too

        if kwargs.get('keyframes_list_selection', False): # List highlight change
            _try_update(self.keyframes_list, 'update_selection_highlight')
            _try_update(self.timeline_canvas, 'update_keyframe_markers') # Redraw timeline to show selection highlight

        # New flag specifically for timeline keyframe updates (if separate from list update)
        if kwargs.get('timeline_keyframes', False):
             _try_update(self.timeline_canvas, 'update_keyframe_markers')

        # Slide updates
        if kwargs.get('slides', False): # On load slides
             if self.slides_viewer and self.slide_handler:
                  try:
                      slide_idx = self.slide_handler.find_slide_index_for_time(self.state.current_position)
                      self.state.current_slide_index = slide_idx
                      _try_update(self.slides_viewer, 'update_display', update_path=False, update_slide=True)
                  except Exception as e: print(f"Error finding/displaying slide after load: {e}")

        elif kwargs.get('current_slide', False): # During playback/seek
             if self.slides_viewer and self.slide_handler and self.state.has_slides():
                  try:
                      current_time = self.audio_handler.get_current_playback_position()
                      new_slide_idx = self.slide_handler.find_slide_index_for_time(current_time)
                      if new_slide_idx != self.state.current_slide_index:
                           self.state.current_slide_index = new_slide_idx
                           _try_update(self.slides_viewer, 'display_slide', new_slide_idx)
                  except Exception as e: print(f"Error updating current slide display: {e}")

        if kwargs.get('status', False):
            _try_update(self.status_bar, 'update_status')


    def periodic_update(self):
        '''Runs periodically to update time-sensitive UI elements.'''
        try:
            if not self.winfo_exists(): return
        except tk.TclError: return

        try:
            self.audio_handler.update_playback_position() # This triggers time, marker, slide updates via update_ui
        except Exception as e:
             print(f"Error during periodic audio update: {e}")
             traceback.print_exc()

        try:
             if self.winfo_exists():
                  self._update_loop_id = self.after(WAVEFORM_UPDATE_INTERVAL_MS, self.periodic_update)
        except tk.TclError: pass


    # --- Window Events ---

    def _on_window_resize(self, event):
        '''Handles window resize with debouncing.'''
        if event.widget != self: return

        if self.resize_timer is not None:
            try: self.after_cancel(self.resize_timer)
            except ValueError: pass
        if self.winfo_exists():
             self.resize_timer = self.after(RESIZE_DEBOUNCE_MS, self._perform_resize_actions)

    def _perform_resize_actions(self):
        '''Actions to perform after resizing stops.'''
        self.resize_timer = None
        if not self.winfo_exists(): return

        print("Window resize finished - performing delayed redraw actions.")
        def _try_update(widget, method_name, *args, **kw_args):
            if widget and hasattr(widget, method_name) and widget.winfo_exists():
                try: getattr(widget, method_name)(*args, **kw_args)
                except Exception as e: print(f"Error redrawing {widget.__class__.__name__}: {e}")

        # Redraw timeline and slide
        _try_update(self.timeline_canvas, 'redraw_all') # Full redraw needed on resize
        _try_update(self.slides_viewer, 'display_slide', self.state.current_slide_index)


    def _on_close(self):
        '''Handles the window closing event.'''
        print("Close requested.")
        try:
            if hasattr(self, '_update_loop_id') and self._update_loop_id:
                try: self.after_cancel(self._update_loop_id)
                except ValueError: pass
                self._update_loop_id = None
            if self.resize_timer:
                 try: self.after_cancel(self.resize_timer)
                 except ValueError: pass
                 self.resize_timer = None
            if hasattr(self.slides_viewer, '_resize_timer') and self.slides_viewer._resize_timer:
                 try: self.slides_viewer.after_cancel(self.slides_viewer._resize_timer)
                 except ValueError: pass
            if hasattr(self.slides_viewer, '_update_slide_timer') and self.slides_viewer._update_slide_timer:
                 try: self.slides_viewer.after_cancel(self.slides_viewer._update_slide_timer)
                 except ValueError: pass

            if hasattr(self, 'audio_handler') and hasattr(self, 'state') and self.state.is_playing:
                 print("Stopping playback...")
                 self.audio_handler.stop_playback()

            print("Cleaning up Pygame...")
            if pygame.get_init():
                pygame.mixer.quit()
                pygame.quit()

        except Exception as e:
             print(f"Error during cleanup: {e}")
        finally:
             print("Destroying window...")
             try: self.destroy()
             except tk.TclError: print("Window already destroyed?")
             except Exception as destroy_e: print(f"Error destroying window: {destroy_e}")


    # --- Help Dialogs ---
    def show_instructions(self):
        instructions = '''
Audio Keyframe Editor - Instructions

1.  **Load Audio:** File -> Open Audio File... (WAV, MP3, OGG) `(Ctrl+O)`
2.  **Load Slides:** File -> Select Slides Folder... (1.png, 2.png, ...) `(Ctrl+L)`
3.  **Playback:**
    *   Click 'Play' or press `Space` to Play/Pause.
    *   Click 'Stop' to stop playback and return to start.
    *   Click `←5s` / `→5s` or press `Left`/`Right` arrow keys to skip.
    *   Use `Home`/`End` keys to go to start/end of audio.
    *   Click on the grey timeline bar to seek to a specific time.
4.  **Keyframes:**
    *   Press 'k' or click '+ Keyframe' to add a keyframe at the current playback position.
    *   Click a keyframe in the list to select it (highlighted orange on timeline).
    *   Press `Delete` or `Backspace` or click 'Delete' button to remove the selected keyframe.
    *   Double-click a keyframe in the list or select it and press `Ctrl+E` (or click 'Edit Time') to modify its time.
5.  **Import/Export:**
    *   File -> Import Keyframes... `(Ctrl+I)` (Load audio first!).
    *   File -> Export Keyframes as JSON... `(Ctrl+S)` (or 'Export JSON' button).

**Tips:**
*   The first keyframe at 0.0s cannot be deleted.
*   Keyframes determine when each corresponding slide *starts* appearing.
*   The exported JSON contains the duration each slide is shown.
'''
        messagebox.showinfo("Instructions", instructions, parent=self)

    def show_about(self):
        about_text = '''
Audio Keyframe Editor v1.4 (Simple Timeline)

Synchronize slideshow images (PNG) with audio narration.

Features:
- Simple timeline visualization with keyframe markers
- Keyframe placement & editing via list/dialog
- Real-time slide preview
- Keyframe import/export (JSON)

Built with Python, Tkinter, Pygame, Librosa.
'''
        messagebox.showinfo("About Audio Keyframe Editor", about_text, parent=self)


# END OF FILE ui/main_window.py