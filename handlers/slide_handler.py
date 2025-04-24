import os
import glob
from tkinter import messagebox
from PIL import Image, ImageTk, UnidentifiedImageError
# Ensure utils is importable
try:
    from utils import natural_sort_key
except ImportError:
    print("ERROR: Cannot import from utils.py in slide_handler. Ensure it's accessible.")
    # Define fallback
    def natural_sort_key(s): return s # Basic fallback

class SlideHandler:
    '''Handles loading and managing slide images.'''

    def __init__(self, app_state, update_callback):
        self.state = app_state
        self.update_ui = update_callback

    def load_slides(self, folder_path):
        '''Loads slide image paths from a folder.'''
        if not folder_path or not os.path.isdir(folder_path):
            messagebox.showerror("Error", f"Invalid folder path selected:\n{folder_path}")
            return False

        try:
            print(f"Attempting to load slides from: {folder_path}")
            previous_dir = self.state.slides_directory
            self.state.reset_slide_state() # Clear previous slides
            self.state.slides_directory = folder_path

            # Find all png files in the folder (case-insensitive)
            slide_files_found = []
            for pattern in ["*.png", "*.PNG"]:
                 # Use os.path.join for cross-platform compatibility
                 search_pattern = os.path.join(folder_path, pattern)
                 found = glob.glob(search_pattern)
                 # Filter out potential directories if any match the pattern (unlikely for .png)
                 slide_files_found.extend([f for f in found if os.path.isfile(f)])


            # Remove duplicates and sort naturally based on filename
            if slide_files_found:
                # Use a set for uniqueness then sort
                unique_files = sorted(list(set(slide_files_found)), key=lambda x: natural_sort_key(os.path.basename(x)))
                self.state.slide_files = unique_files
                print(f"Found {len(self.state.slide_files)} unique PNG files.")
            else:
                 self.state.slide_files = [] # Ensure it's an empty list
                 print("No PNG files found in the selected directory.")


            if not self.state.slide_files:
                messagebox.showwarning("No Slides Found",
                                       f"No PNG files found directly in the selected folder:\n{folder_path}")
                # Keep folder path selected, but no slides loaded
                self.state.status_message = f"Selected folder: {self.state.get_slides_basename()} (No slides found)"
                # Update UI to show empty state
                self.update_ui(slides=True, file_paths=True, status=True)
                return False # Indicate no slides were actually loaded

            # Check numbering convention (optional but helpful)
            self._validate_slide_numbering()

            # Start with the first slide displayed
            self.state.current_slide_index = 0

            self.state.status_message = f"Loaded {len(self.state.slide_files)} slides from {self.state.get_slides_basename()}"
            # Update slide display, file paths in UI, and status bar
            # Trigger 'slides' update which handles finding and showing the correct initial slide
            self.update_ui(slides=True, file_paths=True, status=True)
            print("Slide loading successful.")
            return True

        except Exception as e:
            import traceback
            traceback.print_exc()
            self.state.reset_slide_state() # Reset fully on error
            # Keep failed folder path selected for user reference
            # self.state.slides_directory = folder_path # Already set
            self.state.status_message = "Error loading slides."
            messagebox.showerror("Error", f"Failed to load slides from '{os.path.basename(folder_path)}':\n{e}")
            # Update UI to reflect failure
            self.update_ui(slides=True, file_paths=True, status=True)
            return False

    def _validate_slide_numbering(self):
        '''Checks if slide filenames seem to follow the 1.png, 2.png... convention.'''
        if not self.state.slide_files: return
        expected_number = 1
        mismatch_found = False
        details = []
        for i, slide_path in enumerate(self.state.slide_files):
            basename = os.path.basename(slide_path)
            name_part, ext = os.path.splitext(basename)
            if ext.lower() == '.png':
                try:
                    file_number = int(name_part)
                    if file_number != expected_number:
                        details.append(f"  - Expected '{expected_number}.png', found '{basename}' at position {i+1}")
                        mismatch_found = True
                        # Don't break, report all mismatches? Let's just flag first.
                        break
                    expected_number += 1
                except ValueError:
                    # Filename is not purely numeric
                    details.append(f"  - Expected '{expected_number}.png', found non-numeric name '{basename}' at position {i+1}")
                    mismatch_found = True
                    break
            else:
                 # Should not happen due to glob pattern, but safety check
                 details.append(f"  - Found non-PNG file? '{basename}' at position {i+1}")
                 mismatch_found = True
                 break

        if mismatch_found:
            warning_msg = ("Slide filenames might not follow the expected sequential numbering (1.png, 2.png, ...).\n"
                           "Slides were loaded based on natural sort order.\n"
                           "Ensure this matches your intended slide sequence.\n\n"
                           "First mismatch found:\n" + "\n".join(details))

            print(f"WARNING: Slide numbering mismatch detected.\n{warning_msg}")
            # Use root window as parent if available, otherwise None
            parent_window = None
            # Access root window via the update_ui callback's __self__ attribute (if it's a method)
            if hasattr(self.update_ui, '__self__') and hasattr(self.update_ui.__self__, 'root'):
                 parent_window = self.update_ui.__self__.root # Assuming update_ui is a method of main_window
            messagebox.showwarning("Slide Numbering Warning", warning_msg, parent=parent_window)


    def get_slide_for_display(self, index, target_width, target_height):
        '''Loads, resizes, and returns a slide image (PIL) and PhotoImage (Tk) for display.'''
        # Check index bounds first
        if not (0 <= index < len(self.state.slide_files)):
            # print(f"get_slide_for_display: Invalid index {index}")
            # Clear cache if index is invalid but was previously valid
            if self.state.loaded_slide_photo:
                self.state.loaded_slide_image = None
                self.state.loaded_slide_photo = None
            return None, None # No image, no photo

        # Check target dimensions are positive
        if target_width <= 1 or target_height <= 1:
            # print(f"Slide load skipped: Invalid target dimensions ({target_width}x{target_height})")
            return None, None # Cannot resize to invalid dimensions

        slide_path = self.state.slide_files[index]

        # --- Load and Resize ---
        try:
            # print(f"Loading and resizing slide {index}: {slide_path} for target {target_width}x{target_height}")
            image = Image.open(slide_path)
            # Convert to RGBA *after* loading to handle various PNG modes (e.g., P, LA)
            image = image.convert("RGBA")

            img_width, img_height = image.size
            if img_width <= 0 or img_height <= 0:
                 raise ValueError("Image has zero or negative dimensions")

            # Calculate resize ratio
            ratio = min(target_width / img_width, target_height / img_height)
            ratio = max(0.001, ratio) # Prevent zero ratio

            new_width = max(1, int(img_width * ratio))
            new_height = max(1, int(img_height * ratio))

            # Resize using LANCZOS for best quality downscaling
            resized_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)

            # Convert to Tkinter PhotoImage
            photo = ImageTk.PhotoImage(resized_image)

            # --- Update Cache ---
            # Store the results (photo reference is essential)
            # self.state.loaded_slide_image = resized_image # Cache PIL image (optional)
            self.state.loaded_slide_photo = photo # MUST cache Tk PhotoImage

            return resized_image, photo # Return both PIL and Tk image

        except FileNotFoundError:
             error_msg = f"Slide file not found:\n{os.path.basename(slide_path)}"
             print(error_msg)
        except UnidentifiedImageError:
             error_msg = f"Cannot identify image file (corrupted or invalid format):\n{os.path.basename(slide_path)}"
             print(error_msg)
        except ValueError as ve:
             error_msg = f"Invalid image data for slide {index+1}:\n{os.path.basename(slide_path)}\n{ve}"
             print(error_msg)
        except Exception as e:
             import traceback
             print(f"--- Error Loading Slide {index+1} ---")
             traceback.print_exc()
             error_msg = f"Error loading slide {index+1}:\n{os.path.basename(slide_path)}\n{e}"
             print(error_msg) # Also print error details

        # --- Handle Failure ---
        # Return None if loading failed, ensure cache is cleared
        self.state.loaded_slide_image = None
        self.state.loaded_slide_photo = None
        return None, None


    def find_slide_index_for_time(self, time_seconds):
         '''Determines which slide's index (0-based) should be displayed at a given time.'''
         if not self.state.has_slides():
             return -1 # No slides loaded

         if not self.state.keyframes:
             # If slides exist but no keyframes, always show the first slide
             return 0

         # Keyframes are sorted by time. Find the last keyframe whose time is <= current time.
         target_kf_index = -1 # Index in the keyframes list
         for i, kf in enumerate(self.state.keyframes):
              # Use a small epsilon for comparison robustness? Maybe not needed if times are rounded.
              if time_seconds >= kf['time'] - 0.0001: # Allow time to be exactly on keyframe
                  target_kf_index = i
              else:
                  # We've passed the time, the previous keyframe's index is correct.
                  break # Exit loop early

         # If time is before the very first keyframe, use the first keyframe's slide
         if target_kf_index == -1:
              target_kf_index = 0


         # Get the slideIndex associated with the determined keyframe
         # This slideIndex directly corresponds to the intended slide file order (0-based)
         # Protect against missing 'slideIndex' key just in case
         try:
             target_slide_index = self.state.keyframes[target_kf_index].get('slideIndex', 0)
         except IndexError:
              print(f"Error: target_kf_index {target_kf_index} out of bounds for keyframes.")
              return 0 # Default to first slide on error


         # Ensure the target_slide_index is valid for the number of *loaded* slides
         num_loaded_slides = len(self.state.slide_files)
         if num_loaded_slides == 0:
              return -1 # No slides available to show

         if not (0 <= target_slide_index < num_loaded_slides):
              print(f"Warning: Keyframe {target_kf_index+1} points to slide index {target_slide_index}, "
                    f"but only {num_loaded_slides} slides are loaded.")
              # Clamp to the last available slide index
              target_slide_index = max(0, min(target_slide_index, num_loaded_slides - 1))

         return target_slide_index


# END OF FILE handlers/slide_handler.py
