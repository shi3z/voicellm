# VoiceLLM

A local voice interaction system using sherpa-onnx and LMStudio. Combines voice recognition, LLM responses, and voice synthesis to build a completely private voice assistant.

## Features

- 🎤 **Voice Recognition**: Real-time speech recognition with sherpa-onnx WebAssembly
- 🤖 **LLM Response**: Natural language responses through LMStudio integration
- 🗣️ **Multi-language Voice Synthesis**: Automatic Japanese/English voice synthesis switching
- 💬 **Markdown Support**: Supports markdown formatting in response text
- 🔧 **Tool Calling**: JavaScript/Python code execution capabilities
- 🌐 **Multi-language UI**: Japanese/English interface switching
- 🔒 **Private**: All processing runs locally

## System Architecture

```
Voice Input → sherpa-onnx → Python API → LMStudio → Voice Synthesis
                              ↓
                        Web Interface
```

## Requirements

- Python 3.8+
- LMStudio
- Node.js (for tool execution)
- Modern web browser with microphone support

## Installation

1. Clone the repository
```bash
git clone https://github.com/shi3z/voicellm
cd voiceui
```

2. Install Python dependencies
```bash
pip install -r requirements.txt
```

3. Install and configure LMStudio
   - Download [LMStudio](https://lmstudio.ai/)
   - Load your preferred model (e.g., `openai/gpt-oss-120b`)
   - Start API server on port 1234

## Usage

1. **Start LMStudio**
   ```bash
   # Start API server on localhost:1234 in LMStudio
   ```

2. **Start Python server**
   ```bash
   python main.py
   ```

3. **Access in browser**
   ```
   http://localhost:8000
   ```

4. **Start voice interaction**
   - Click "Start" button for voice input
   - Or use text input box
   - AI responds with both text and voice

## File Structure

```
voiceui/
├── main.py                    # Python server and LMStudio API integration
├── index.html                # Web UI with voice interface
├── app-vad-asr.js            # Voice recognition control
├── sherpa-onnx-*.js          # sherpa-onnx WebAssembly files
├── requirements.txt          # Python dependencies
└── README.md                # This file
```

## Key Features

### Voice Recognition
- VAD (Voice Activity Detection) for speech segment detection
- High-accuracy speech recognition with sherpa-onnx WebAssembly
- Japanese and English speech recognition support
- Browser speech recognition fallback

### LLM Integration
- LMStudio API integration with conversation history
- Tool calling support for JavaScript/Python execution
- Automatic `<thinking>` tag removal
- Error handling with fallback responses
- Model selection and configuration

### Voice Synthesis
- Web Speech API integration
- Automatic Japanese/English language detection
- Natural multi-language voice synthesis
- Quoted text pronunciation in English

### UI Features
- Real-time conversation history display
- Markdown formatted response rendering
- Collapsible settings panel
- Multi-language interface (Japanese/English)
- Responsive design
- Local settings persistence

## Configuration

### Model Settings
Configure through the web interface:
- Model selection from available LMStudio models
- Maximum recommended tokens slider
- System prompt customization
- Tool execution enable/disable

### Voice Settings
Voice synthesis can be customized in `index.html`:
```javascript
utterance.rate = 0.9;    // Speech rate
utterance.pitch = 1.0;   // Pitch
utterance.volume = 1.0;  // Volume
```

### Tool Configuration
Enable JavaScript/Python execution through the settings panel. Tools are executed safely with timeout protection.

## API Endpoints

- `GET /` - Main web interface
- `POST /api/chat` - Chat with LMStudio
- `GET /api/models` - Get available models
- `GET/POST /api/config` - Configuration management
- `GET/DELETE /api/conversation` - Conversation history
- `GET /api/tools` - Available tools
- `GET /api/health` - Health check

## Troubleshooting

### Port 8000 Already in Use
```bash
# Find and kill process using port 8000
lsof -ti:8000 | xargs kill -9
```

### Voice Synthesis Not Working
1. Check browser audio permissions
2. Verify system audio settings
3. Ensure Japanese/English voices are installed
4. Try different browsers (Chrome/Safari recommended)

### LMStudio Connection Error
1. Verify LMStudio is running
2. Check API server is enabled
3. Confirm model is loaded
4. Test API endpoint: `http://localhost:1234/v1/models`

### WebAssembly Loading Issues
1. Ensure all sherpa-onnx files are present
2. Check browser WebAssembly support
3. Fallback to browser speech recognition available

## Technical Details

### Voice Recognition Flow
```
Microphone → VAD → Speech Detection → sherpa-onnx → Text
```

### API Communication Flow
```
JavaScript → Flask API → LMStudio API → Response
```

### Multi-language Voice Synthesis
- Regex-based English text detection
- Segment-wise language configuration
- Sequential voice synthesis playback

### Tool Calling System
- Safe subprocess execution with timeout
- JavaScript execution via Node.js
- Python code execution with output capture
- Error handling and result formatting

## Development

### Adding New Tools
Tools can be added in `main.py`:
```python
def get_available_tools():
    return [
        {
            "type": "function",
            "function": {
                "name": "your_tool_name",
                "description": "Tool description",
                # ... parameters
            }
        }
    ]
```

### Internationalization
Add translations to the `translations` object in `index.html`:
```javascript
const translations = {
  ja: { 'key': '日本語テキスト' },
  en: { 'key': 'English text' }
};
```

## Security Considerations

- Tool execution runs in sandboxed subprocess with timeout
- No network access for executed code
- Input validation for all API endpoints
- CORS configuration for local development

## License

This project is released under the MIT License.

## Contributing

Pull requests and issue reports are welcome.

## Acknowledgments

- [sherpa-onnx](https://github.com/k2-fsa/sherpa-onnx) - Speech recognition engine
- [LMStudio](https://lmstudio.ai/) - Local LLM runtime environment
- [Marked.js](https://marked.js.org/) - Markdown parser
- [Flask](https://flask.palletsprojects.com/) - Python web framework