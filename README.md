# Audio Keyframe Editor

A simple, browser-based tool for creating slide timing data from audio narrations. This tool allows you to mark keyframes while listening to your audio narration, helping you synchronize slides or images with your audio content.

![AudioKeyframeEditor_screenshot](https://github.com/user-attachments/assets/15636c6f-a6f5-430c-94e0-0f13fa9b5a36)


## Features

- **Easy Audio Upload**: Works with MP3, WAV, and any browser-supported audio format
- **Intuitive Controls**: Play, pause, skip forward/backward 5 seconds
- **Simple Keyframe Creation**: Mark transition points with a single click
- **Visual Timeline**: See all your keyframes in a clear list
- **Edit Functionality**: Easily delete or adjust keyframe positions
- **Live Preview**: View the formatted JSON output before saving
- **Standardized Export**: Save timing data in both human-readable text and structured JSON format

## Use Cases

- Creating timed presentations with synchronized audio
- Developing slide-based educational content
- Building automated video slideshows
- Creating storyboards for animations
- Timing image transitions for audiobooks or narrated stories

## How It Works

1. **Upload**: Select your audio narration file
2. **Listen & Mark**: Play the audio and press the "Add Keyframe" button at each point where you want a slide transition
3. **Review**: Click on any keyframe to jump to that point in the audio
4. **Edit**: Remove unwanted keyframes if needed
5. **Export**: Save the timing data as JSON for use in your presentation software or custom applications

## Output Format

The tool exports a JSON file with the following structure:

```json
[
  {
    "image_number": 1,
    "image_name": "1.png",
    "Duration": 5.0
  },
  {
    "image_number": 2,
    "image_name": "2.png",
    "Duration": 20.0
  },
  ...
]
```

This format can be easily integrated with various presentation tools and custom applications.

## No Installation Required

This is a standalone HTML application that runs entirely in your browser. No server, dependencies, or internet connection required after downloading.

## Getting Started

### Option 1: Direct Download and Run
1. Download the `audio-keyframe-editor.html` file
2. Open the file in any modern browser
3. That's it!

### Option 2: Clone the Repository
```bash
git clone https://github.com/yourusername/audio-keyframe-editor.git
cd audio-keyframe-editor
# Just open the HTML file in your browser
```

## Browser Compatibility

- Chrome (recommended)
- Firefox
- Edge
- Safari

## Privacy

All processing is done entirely on your device. Your audio files and timing data never leave your computer.

## Development

This tool is built with vanilla JavaScript, HTML, and CSS. No frameworks or dependencies are required.

### Project Structure

- `audio-keyframe-editor.html` - The standalone application with HTML, CSS, and JavaScript

### Customization

You can easily customize the tool by editing the HTML file:

- Modify the CSS in the `<style>` section to change the appearance
- Adjust the JavaScript functionality in the `<script>` section to add features

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

Distributed under the MIT License. See `LICENSE` for more information.

## Contact

contact@robomuffin.com

Project Link: [https://github.com/yourusername/audio-keyframe-editor](https://github.com/yourusername/audio-keyframe-editor)

## Acknowledgments

- [Lucide Icons](https://lucide.dev/) - SVG icon system
