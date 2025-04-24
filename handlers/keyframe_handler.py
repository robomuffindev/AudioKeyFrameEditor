# START OF FILE handlers/keyframe_handler.py
import json
import os
from tkinter import simpledialog, messagebox
# Ensure utils is importable
try:
    from utils import format_time, clamp
except ImportError:
    print("ERROR: Cannot import from utils.py in keyframe_handler. Ensure it's accessible.")
    # Define fallbacks
    def format_time(s): return f"{s:.3f}s"
    def clamp(v, mn, mx): return max(mn, min(v, mx))

class KeyframeHandler:
    '''Handles keyframe creation, deletion, modification, import, and export.'''

    def __init__(self, app_state, update_callback):
        self.state = app_state
        self.update_ui = update_callback

    def add_keyframe(self, time_seconds):
        '''Adds a new keyframe at the specified time.'''
        if not self.state.has_audio():
            messagebox.showinfo("Info", "Please load an audio file first.")
            return False

        time_seconds = clamp(time_seconds, 0, self.state.audio_duration)
        time_seconds = round(time_seconds, 3)

        min_distance = 0.010
        for kf in self.state.keyframes:
            if abs(kf['time'] - time_seconds) < min_distance:
                self.state.status_message = f"Keyframe already exists near {format_time(time_seconds)}"
                self.update_ui(status=True)
                existing_index = self.find_keyframe_index(kf['time'])
                if existing_index != -1:
                     self.select_keyframe(existing_index)
                return False

        new_keyframe = {'time': time_seconds, 'slideIndex': -1}
        self.state.keyframes.append(new_keyframe)
        self._sort_and_update_indices()

        self.state.status_message = f"Added keyframe at {format_time(time_seconds)}"
        new_index = self.find_keyframe_index(time_seconds)
        if new_index != -1:
            self.state.selected_keyframe_index = new_index
            # Update list, timeline, selection, status
            self.update_ui(keyframes=True, timeline_keyframes=True, status=True, keyframes_list_selection=True)
        else:
             print(f"Warning: Could not re-find keyframe just added at {time_seconds:.3f}s after sorting.")
             self.update_ui(keyframes=True, timeline_keyframes=True, status=True)

        return True

    def delete_keyframe(self, index):
        '''Deletes the keyframe at the given index.'''
        if not (0 <= index < len(self.state.keyframes)):
            if self.state.selected_keyframe_index != -1:
                 index = self.state.selected_keyframe_index
            else:
                 self.state.status_message = "No keyframe selected to delete."
                 self.update_ui(status=True)
                 return False

        if not (0 <= index < len(self.state.keyframes)):
            self.state.status_message = "Invalid keyframe index for deletion."
            self.update_ui(status=True)
            return False

        if index == 0 and abs(self.state.keyframes[index]['time']) < 0.001:
            messagebox.showwarning("Delete Warning", "Cannot delete the initial keyframe at 0.0 seconds.")
            return False

        deleted_time = self.state.keyframes[index]['time']
        print(f"Deleting keyframe at index {index}, time {format_time(deleted_time)}")
        del self.state.keyframes[index]

        self.state.selected_keyframe_index = -1
        self._sort_and_update_indices()

        self.state.status_message = f"Deleted keyframe at {format_time(deleted_time)}"
        # Update list, timeline, selection, status
        self.update_ui(keyframes=True, timeline_keyframes=True, keyframes_list_selection=True, status=True)
        return True

    def update_keyframe_time(self, index, new_time_seconds):
        '''Updates the time of a specific keyframe and re-sorts.'''
        if not (0 <= index < len(self.state.keyframes)):
            print(f"Error: update_keyframe_time called with invalid index {index}")
            return False

        original_time = self.state.keyframes[index]['time']
        new_time_seconds = clamp(new_time_seconds, 0, self.state.audio_duration)
        new_time_seconds = round(new_time_seconds, 3)

        if abs(new_time_seconds - original_time) < 0.0005: return False

        min_distance = 0.001
        if index > 0:
             prev_kf_time = self.state.keyframes[index - 1]['time']
             if new_time_seconds <= prev_kf_time:
                  new_time_seconds = prev_kf_time + min_distance
                  print(f"Clamping time to maintain minimum distance from previous keyframe.")

        if index < len(self.state.keyframes) - 1:
             next_kf_time = self.state.keyframes[index + 1]['time']
             if new_time_seconds >= next_kf_time:
                  new_time_seconds = next_kf_time - min_distance
                  print(f"Clamping time to maintain minimum distance from next keyframe.")

        new_time_seconds = clamp(new_time_seconds, 0, self.state.audio_duration)
        new_time_seconds = round(new_time_seconds, 3)

        if abs(new_time_seconds - original_time) < 0.0005: return False

        print(f"Updating keyframe {index} time from {original_time:.3f} to {new_time_seconds:.3f}")
        self.state.keyframes[index]['time'] = new_time_seconds
        self._sort_and_update_indices()

        current_selected_index = self.find_keyframe_index(new_time_seconds)
        if current_selected_index != -1:
            if self.state.selected_keyframe_index != current_selected_index:
                 print(f"Keyframe {index} moved to index {current_selected_index} after sort.")
                 self.state.selected_keyframe_index = current_selected_index
                 self.update_ui(keyframes_list_selection=True)
        else:
             print(f"Warning: Could not find keyframe at {new_time_seconds:.3f} after update/sort.")
             self.state.selected_keyframe_index = -1
             self.update_ui(keyframes_list_selection=True)

        self.state.status_message = f"Updated keyframe {self.state.selected_keyframe_index + 1} time to {format_time(new_time_seconds)}"
        # Update timeline and status. List updated on release if dragging.
        self.update_ui(timeline_keyframes=True, status=True)
        return True

    def _sort_and_update_indices(self):
        '''Sorts keyframes by time, updates slideIndex, and tries to preserve selection.'''
        selected_object_id = None
        if 0 <= self.state.selected_keyframe_index < len(self.state.keyframes):
             try: selected_object_id = id(self.state.keyframes[self.state.selected_keyframe_index])
             except IndexError: self.state.selected_keyframe_index = -1

        self.state.keyframes.sort(key=lambda kf: kf['time'])

        new_selected_index = -1
        for i, kf in enumerate(self.state.keyframes):
            kf['slideIndex'] = i
            if selected_object_id is not None and id(kf) == selected_object_id:
                 new_selected_index = i

        if self.state.selected_keyframe_index != new_selected_index:
            self.state.selected_keyframe_index = new_selected_index


    def select_keyframe(self, index):
        '''Sets the selected keyframe index and updates status + UI highlights.'''
        if not isinstance(index, int): return

        if not (0 <= index < len(self.state.keyframes)):
            index = -1

        if self.state.selected_keyframe_index != index:
            print(f"Selecting keyframe index: {index}")
            self.state.selected_keyframe_index = index
            if index != -1:
                try:
                     kf_time = self.state.keyframes[index]['time']
                     self.state.status_message = f"Selected keyframe {index + 1} at {format_time(kf_time)}"
                except IndexError:
                     self.state.status_message = "Selection error."
                     self.state.selected_keyframe_index = -1
                     index = -1
            else:
                self.state.status_message = "Keyframe selection cleared."

            # Update list selection, timeline highlights, and status bar
            self.update_ui(keyframes_list_selection=True, timeline_keyframes=True, status=True)


    def find_keyframe_index(self, time_seconds):
        '''Finds the index of a keyframe exactly matching the time (within tolerance).'''
        if not self.state.keyframes: return -1
        tolerance = 0.0005
        for i, kf in enumerate(self.state.keyframes):
            if abs(kf['time'] - time_seconds) < tolerance:
                return i
        return -1


    def get_formatted_keyframes(self):
        '''Formats keyframes for display in the listbox.'''
        formatted = []
        if not self.state.keyframes:
            return ["No keyframes defined"]

        num_keyframes = len(self.state.keyframes)
        try: max_slide_num_width = len(str(num_keyframes)) if num_keyframes > 0 else 1
        except: max_slide_num_width = 1

        for i, kf in enumerate(self.state.keyframes):
            time_str = format_time(kf['time'])
            slide_num = i + 1
            slide_num_str = f"{slide_num:<{max_slide_num_width}}"
            formatted.append(f"Slide {slide_num_str}: {time_str}")
        return formatted


    def export_keyframes(self, file_path):
        '''Exports keyframes to a JSON file in the specified format.'''
        if not self.state.has_keyframes():
            messagebox.showinfo("Export Info", "No keyframes to export.")
            return False

        audio_available = self.state.has_audio()
        if not audio_available:
             messagebox.showwarning("Export Warning", "Audio not loaded or has zero duration. Last keyframe duration may be inaccurate (calculated as 0).")

        try:
            export_data = []
            num_keyframes = len(self.state.keyframes)
            if num_keyframes == 0:
                 messagebox.showinfo("Export Info", "No keyframes to export.")
                 return False

            sorted_keyframes = sorted(self.state.keyframes, key=lambda kf: kf['time'])

            for i in range(num_keyframes):
                kf = sorted_keyframes[i]
                start_time = kf['time']
                if i < num_keyframes - 1: end_time = sorted_keyframes[i + 1]['time']
                else: end_time = self.state.audio_duration if audio_available and self.state.audio_duration > 0 else start_time
                duration = max(0, end_time - start_time)
                duration = round(duration, 3)
                image_number = kf['slideIndex'] + 1
                actual_image_name = self.state.get_slide_filename_for_index(kf['slideIndex'])
                image_name = actual_image_name if actual_image_name != "N/A" else f"{image_number}.png"
                export_data.append({"image_number": image_number, "image_name": image_name, "Duration": duration})

            print(f"Exporting {len(export_data)} keyframes to {file_path}")
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2)

            text_path = os.path.splitext(file_path)[0] + '.txt'
            try:
                 print(f"Writing text summary to {text_path}")
                 with open(text_path, 'w', encoding='utf-8') as f_txt:
                      f_txt.write(f"Audio File: {self.state.get_audio_basename()}\\n")
                      f_txt.write(f"Total Duration: {format_time(self.state.audio_duration) if audio_available else 'N/A'}\\n")
                      f_txt.write(f"Slides Folder: {self.state.get_slides_basename()}\\n")
                      f_txt.write("-" * 30 + "\\n")
                      f_txt.write(f"Exported {len(export_data)} Keyframes/Segments:\\n\\n")
                      total_calc_duration = 0
                      for item_index, item in enumerate(export_data):
                           kf_time = sorted_keyframes[item_index]['time']
                           f_txt.write(f"#{item_index + 1}\\n")
                           f_txt.write(f"  Slide: {item['image_name']} (Number: {item['image_number']})\\n")
                           f_txt.write(f"  Appears at: {format_time(kf_time)}\\n")
                           f_txt.write(f"  Duration: {item['Duration']:.3f}s\\n\\n")
                           total_calc_duration += item['Duration']
                      f_txt.write("-" * 30 + "\\n")
                      f_txt.write(f"Sum of durations: {total_calc_duration:.3f}s\\n")
            except Exception as txt_err: print(f"Warning: Could not write text summary file '{text_path}': {txt_err}")

            self.state.status_message = f"Exported {len(export_data)} keyframes to {os.path.basename(file_path)}"
            self.update_ui(status=True)
            messagebox.showinfo("Export Successful", f"Exported {len(export_data)} keyframes to:\\n{file_path}\\n(and .txt summary)")
            return True

        except Exception as e:
            import traceback
            print("Export Error Traceback:")
            traceback.print_exc()
            self.state.status_message = "Keyframe export failed."
            self.update_ui(status=True)
            messagebox.showerror("Export Error", f"Failed to export keyframes:\\n{e}")
            return False


    def import_keyframes(self, file_path):
        '''Imports keyframes from a JSON file, replacing existing ones.'''
        if not self.state.has_audio():
            messagebox.showerror("Import Error", "Please load the corresponding audio file first.")
            return False

        try:
            print(f"Attempting to import keyframes from: {file_path}")
            with open(file_path, 'r', encoding='utf-8') as f:
                imported_data = json.load(f)

            if not isinstance(imported_data, list): raise ValueError("Invalid format: JSON root should be a list.")
            if not imported_data: raise ValueError("Import file is empty or contains no keyframe data.")

            new_keyframes = []
            current_time = 0.0
            total_duration_from_import = 0.0
            slide_match_warning_details = ""
            num_imported = len(imported_data)
            num_slides = len(self.state.slide_files)

            if self.state.has_slides() and num_imported != num_slides:
                 slide_match_warning_details = (f"\\n\\nWarning: File has {num_imported} segments, "
                                                f"but {num_slides} slides are loaded. "
                                                f"Slide assignments may be offset.")

            for i, item in enumerate(imported_data):
                if not isinstance(item, dict): raise ValueError(f"Invalid format: Item {i+1} is not a dictionary.")
                req_keys = ["image_number", "image_name", "Duration"]
                if not all(k in item for k in req_keys):
                     missing = [k for k in req_keys if k not in item]
                     raise ValueError(f"Invalid format: Item {i+1} missing required key(s): {', '.join(missing)}")

                try:
                     duration = float(item["Duration"])
                     image_number = int(item["image_number"])
                except (ValueError, TypeError) as type_err: raise ValueError(f"Invalid data type in item {i+1}: {type_err}") from type_err

                if duration < 0:
                     print(f"Warning: Item {i+1} has negative duration ({duration:.3f}s). Using 0.")
                     duration = 0

                kf_time = round(current_time, 3)
                slide_index = i

                if image_number != (i + 1):
                     print(f"Note: Imported item {i+1} has image_number {image_number}, expected {i+1} based on order.")

                new_keyframes.append({'time': kf_time, 'slideIndex': slide_index})
                current_time += duration
                total_duration_from_import += duration

            duration_diff = abs(total_duration_from_import - self.state.audio_duration)
            duration_warning_details = ""
            if self.state.has_audio() and duration_diff > 0.5:
                 duration_warning_details = (
                     f"\\n\\nWarning: Imported duration ({format_time(total_duration_from_import)}) "
                     f"differs significantly from audio duration ({format_time(self.state.audio_duration)}). "
                     f"Timings relative to audio end may be inaccurate."
                 )

            confirm_msg = f"Replace {len(self.state.keyframes)} existing keyframe(s) with {len(new_keyframes)} imported keyframe(s)?"
            confirm_msg += slide_match_warning_details
            confirm_msg += duration_warning_details

            if self.state.has_keyframes():
                if not messagebox.askyesno("Confirm Import", confirm_msg):
                    self.state.status_message = "Import cancelled by user."
                    self.update_ui(status=True)
                    print("Import cancelled by user.")
                    return False

            print(f"Replacing {len(self.state.keyframes)} keyframes with {len(new_keyframes)} imported.")
            self.state.keyframes = new_keyframes
            self.state.selected_keyframe_index = -1

            self.state.status_message = f"Imported {len(new_keyframes)} keyframes from {os.path.basename(file_path)}"
            # Update UI fully after import - includes timeline now
            self.update_ui(keyframes=True, timeline_keyframes=True, status=True, keyframes_list_selection=True, current_slide=True)
            messagebox.showinfo("Import Successful", f"Successfully imported {len(new_keyframes)} keyframes.")
            print("Import successful.")
            return True

        except json.JSONDecodeError as e:
            self.state.status_message = "Import failed: Invalid JSON."
            self.update_ui(status=True)
            messagebox.showerror("Import Error", f"Failed to parse JSON file:\\n{e}")
            print(f"Import failed: Invalid JSON - {e}")
            return False
        except FileNotFoundError:
            self.state.status_message = "Import failed: File not found."
            self.update_ui(status=True)
            messagebox.showerror("Import Error", f"File not found:\\n{file_path}")
            print(f"Import failed: File not found - {file_path}")
            return False
        except (ValueError, KeyError, TypeError) as e:
            self.state.status_message = "Import failed: Invalid format/data."
            self.update_ui(status=True)
            messagebox.showerror("Import Error", f"Invalid keyframe file format or data:\\n{e}")
            print(f"Import failed: Invalid format/data - {e}")
            return False
        except Exception as e:
            import traceback
            print("Import Error Traceback:")
            traceback.print_exc()
            self.state.status_message = "Import failed (unexpected)."
            self.update_ui(status=True)
            messagebox.showerror("Import Error", f"An unexpected error occurred during import:\\n{e}")
            return False


# END OF FILE handlers/keyframe_handler.py