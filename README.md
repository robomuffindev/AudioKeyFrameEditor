
### Key Dependencies

-   **Tkinter/ttk**: Standard Python library for the GUI framework.
-   **Pygame**: Used for reliable cross-platform audio playback (`pygame.mixer`) and high-resolution timing (`pygame.time.get_ticks`).
-   **Librosa**: Powerful library for audio analysis; used here primarily for robust loading of various audio formats (MP3, OGG, WAV) and getting duration/sample rate.
-   **Pillow (PIL Fork)**: Used for loading, processing, and displaying PNG slide images within the Tkinter canvas.
-   **NumPy**: Required by Librosa for numerical operations on audio data.

### Potential Future Enhancements

-   **True Playback Speed Control**: Implement actual audio speed adjustment (potentially using libraries like `soundstretch` or phase vocoding) instead of just visual speed.
-   **Undo/Redo Functionality**: Track changes to keyframes for undo/redo support.
-   **Improved Layout Management**: Use `grid` more extensively or explore alternative Tkinter layout managers for better responsiveness on very small screens.
-   **Keyframe Dragging on Timeline**: Re-implement dragging keyframe markers directly on the `TimelineCanvas` (requires careful coordinate mapping).
-   **Visual Feedback during Import/Export**: Show progress bars for potentially long operations.
-   **Error Handling**: More specific error catching and user-friendly messages for file loading/processing issues.
-   **Cross-Platform Support**: Create equivalent `install.sh`/`run.sh` scripts for macOS/Linux. Test and potentially adjust theme/UI specifics.
-   **Configuration File**: Store user preferences (e.g., default directories, UI settings).
-   **Testing**: Add unit and integration tests.

### Contributing

Contributions are welcome!

1.  **Issues**: Please open an issue on GitHub to discuss bugs or proposed features.
2.  **Fork**: Fork the repository.
3.  **Branch**: Create a new branch for your feature or bug fix.
4.  **Develop**: Make your changes. Adhere to existing code style where possible.
5.  **Test**: Ensure the application still runs and your changes work as expected.
6.  **Pull Request**: Submit a pull request with a clear description of your changes.

## License

This project is licensed under the MIT License. You should include a `LICENSE` file in the repository containing the full MIT License text.

## Acknowledgments

-   [Librosa](https://librosa.org/) - Audio analysis & loading
-   [Pygame](https://www.pygame.org/) - Audio playback & timing
-   [Pillow](https://python-pillow.org/) - Image loading & processing
-   [Tkinter](https://docs.python.org/3/library/tkinter.html) - GUI framework

# END OF FILE README.md