# START OF FILE ui/slides_viewer.py
import tkinter as tk
from tkinter import ttk
import os
from PIL import Image, ImageTk # Keep PIL import here for type hinting if needed

class SlidesViewer(ttk.Frame):
    '''UI component for displaying slides and selecting the folder.'''

    def __init__(self, parent, app_state, commands, **kwargs):
        super().__init__(parent, **kwargs)
        self.state = app_state
        self.commands = commands # Dictionary of callbacks
        self._resize_timer = None # Timer for debouncing canvas resize
        self._update_slide_timer = None # Timer for debouncing slide updates
        self.slide_info_label = None # Initialize instance variable
        self.folder_entry = None # Initialize instance variable

        self.create_widgets()

    def create_widgets(self):
        # Use a LabelFrame for visual grouping
        slides_frame = ttk.LabelFrame(self, text="Slides Viewer")
        slides_frame.pack(fill=tk.BOTH, expand=True, padx=0, pady=0) # No frame padding

        # Slides canvas for displaying images
        self.slides_canvas = tk.Canvas(slides_frame, bg="#333333", highlightthickness=0) # Darker background
        self.slides_canvas.pack(fill=tk.BOTH, expand=True, padx=5, pady=5) # Padding inside frame
        self.slides_canvas.bind("<Configure>", self._on_canvas_resize) # Debounced resize

        # Slide info label - store the label widget itself
        self.slide_info_var = tk.StringVar(value="No slides loaded")
        # Store the label in self.slide_info_label
        self.slide_info_label = ttk.Label(slides_frame, textvariable=self.slide_info_var, anchor=tk.CENTER) # <-- Stored widget here
        self.slide_info_label.pack(pady=(0, 5), fill=tk.X) # Below canvas

        # Slides folder selection frame
        folder_frame = ttk.Frame(slides_frame)
        folder_frame.pack(fill=tk.X, padx=5, pady=(0, 5)) # Bottom, padded

        ttk.Label(folder_frame, text="Folder:").pack(side=tk.LEFT, padx=(0, 5))

        self.folder_path_var = tk.StringVar(value=self.state.get_slides_basename())
        # Store the Entry widget
        self.folder_entry = ttk.Entry(folder_frame, textvariable=self.folder_path_var, state="readonly") # <-- Stored widget here
        self.folder_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        folder_button = ttk.Button(folder_frame, text="Browse...", width=8,
                                   command=self.commands['select_slides'])
        folder_button.pack(side=tk.LEFT)

    def update_display(self, update_path=True, update_slide=True):
        '''Updates the displayed slide and folder path.'''
        if update_path:
            try:
                 # Check if the ENTRY widget exists before setting the variable
                 if hasattr(self, 'folder_entry') and self.folder_entry.winfo_exists(): # <-- CORRECTED CHECK
                     if hasattr(self.state, 'get_slides_basename'): # Check state method too
                        self.folder_path_var.set(self.state.get_slides_basename())
            except tk.TclError: pass # Ignore if widget destroyed

        if update_slide:
             # Schedule display update slightly deferred to allow state changes to settle
             # Avoid scheduling multiple times rapidly
             if hasattr(self, '_update_slide_timer') and self._update_slide_timer:
                  try: self.after_cancel(self._update_slide_timer)
                  except ValueError: pass # Ignore if timer ID invalid
             # Check if widget still exists before scheduling
             if self.winfo_exists():
                 self._update_slide_timer = self.after(10, self._display_current_slide_from_state)

    def _display_current_slide_from_state(self):
        '''Helper function called by deferred update.'''
        self._update_slide_timer = None # Clear timer ID
        if self.winfo_exists(): # Check if widget still exists
             self.display_slide(self.state.current_slide_index)

    def display_slide(self, index):
         '''Requests the slide handler to prepare and then displays the slide.'''
         if not self.winfo_exists(): return # Exit if widget destroyed

         # Get canvas dimensions, ensure they are valid (> 1 pixel)
         try:
             canvas_width = self.slides_canvas.winfo_width()
             canvas_height = self.slides_canvas.winfo_height()
             if canvas_width <= 1 or canvas_height <= 1:
                  # If canvas not ready, schedule a redisplay if not already pending
                  if not self._resize_timer: # Check if resize isn't already scheduling one
                       self._schedule_redisplay(index, delay_ms=50) # Short delay
                  return
         except tk.TclError: return # Window might be closing


         # Validate index against loaded slides
         if not self.state.has_slides() or not (0 <= index < len(self.state.slide_files)):
             self._clear_canvas_and_info(index)
             return

         # --- Request slide image from handler ---
         img, photo = self.commands['get_slide_for_display'](index, canvas_width, canvas_height)

         # --- Update Canvas ---
         # Clear previous content MUST happen before potentially erroring on create_image
         try: self.slides_canvas.delete("all")
         except tk.TclError: return # Exit if widget destroyed

         if photo and img:
             # PhotoImage reference is kept in AppState by the handler
             # Calculate position to center the image
             x = max(0, (canvas_width - img.width) // 2)
             y = max(0, (canvas_height - img.height) // 2)

             try:
                  self.slides_canvas.create_image(x, y, anchor=tk.NW, image=photo)
                  filename = os.path.basename(self.state.slide_files[index])
                  # Check the LABEL widget exists before setting the variable
                  if hasattr(self, 'slide_info_label') and self.slide_info_label.winfo_exists(): # <-- CORRECTED CHECK
                      self.slide_info_var.set(f"Slide {index + 1} of {len(self.state.slide_files)}: {filename}")
             except tk.TclError as e:
                  print(f"Error displaying slide {index+1} on canvas: {e}")
                  # Check the LABEL widget exists before setting the variable
                  if hasattr(self, 'slide_info_label') and self.slide_info_label.winfo_exists(): # <-- CORRECTED CHECK
                      self.slide_info_var.set(f"Slide {index + 1} (Display Error)")
         else:
             # Display error message on canvas if loading failed
             error_text = f"Error loading slide {index+1}"
             try:
                 if self.slides_canvas.winfo_exists(): # Check again before drawing text
                      self.slides_canvas.create_text(
                           canvas_width // 2, canvas_height // 2,
                           text=error_text, fill="red", font=("Arial", 12), anchor=tk.CENTER
                      )
                      # Check the LABEL widget exists before setting the variable
                      if hasattr(self, 'slide_info_label') and self.slide_info_label.winfo_exists(): # <-- CORRECTED CHECK
                          self.slide_info_var.set(f"Slide {index + 1} (Load Error)")
             except tk.TclError as e:
                  print(f"Error displaying error text on canvas: {e}")
             # Ensure photo ref is cleared if load failed (handler should do this too)
             self.state.loaded_slide_photo = None

    def _clear_canvas_and_info(self, index):
        '''Clears the canvas and updates info label for invalid states.'''
        try:
             if hasattr(self, 'slides_canvas') and self.slides_canvas.winfo_exists():
                 self.slides_canvas.delete("all")
             info_text = "No slides loaded"
             if self.state.has_slides(): # If slides exist but index is bad
                 info_text = f"Slide {index+1} / {len(self.state.slide_files)} (Invalid Index)"
             elif self.state.slides_directory: # If folder selected but no slides found
                  info_text = f"Folder selected (No slides found)"

             # Check the LABEL widget exists before setting the variable
             if hasattr(self, 'slide_info_label') and self.slide_info_label.winfo_exists(): # <-- CORRECTED CHECK
                 self.slide_info_var.set(info_text)
        except tk.TclError: pass # Ignore if closing
        self.state.loaded_slide_photo = None # Clear cached photo reference


    def _on_canvas_resize(self, event):
        '''Called when the canvas size changes, schedules redraw with debounce.'''
        if hasattr(self, '_resize_timer') and self._resize_timer:
            try: self.after_cancel(self._resize_timer)
            except ValueError: pass
        # Schedule the redisplay after a short delay
        if self.winfo_exists(): # Check before scheduling
             self._resize_timer = self.after(150, self._perform_redisplay) # Adjust delay ms

    def _perform_redisplay(self):
         '''Actually redraws the slide after the resize debounce timer.'''
         self._resize_timer = None
         if self.winfo_exists(): # Check if widget still exists
            # print("Debounced resize: Redisplaying slide")
            self.display_slide(self.state.current_slide_index)

    def _schedule_redisplay(self, index, delay_ms=100):
        '''Schedules a single redisplay call, preventing multiple pending calls.'''
        if hasattr(self, '_resize_timer') and self._resize_timer: # Use the same timer as resize debounce
            try: self.after_cancel(self._resize_timer)
            except ValueError: pass
        # Ensure lambda checks winfo_exists before calling display_slide
        if self.winfo_exists(): # Check before scheduling
             self._resize_timer = self.after(delay_ms, lambda idx=index: self.display_slide(idx) if self.winfo_exists() else None)


# END OF FILE ui/slides_viewer.py