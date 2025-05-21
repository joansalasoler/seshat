# Seshat

A GTK-based command palette application with generative AI capabilities for quick text transformations. Named after **Seshat**, the ancient Egyptian goddess of writing, wisdom, and knowledge who was the divine measurer and recorder of time.

![Demo](https://raw.githubusercontent.com/joansalasoler/assets/master/demos/seshat.gif)

## Overview

**Seshat** is a command palette application that provides a quick way to transform selected text using various operations. It integrates with Ollama to provide custom AI-powered text transformations.

### How It Works

Seshat operates by:

1. Capturing text selected by the user on the running app (using X11 clipboard).
2. Providing a command palette interface to choose transformations.
3. Applying the selected operation to the text.
4. Returning the transformed text to the clipboard and automatically sending a "Shift+Insert" keybinding to paste it back into the application

**Note:** Seshat currently works only on X11-based Linux environments due to its dependency on xdotool and X11 clipboard mechanisms. Wayland support is not available at this time.

Key features:

- Mathematical operations.
- Text transformations (case conversion, sorting, formatting).
- AI-powered text generation and transformation via Ollama.
- Customizable through configuration.

## Installation

### Prerequisites

- GTK 4.0
- Python 3.10 or higher
- Poetry package manager
- xdotool (for clipboard operations)
- Ollama (for AI features)

### Install with Poetry

```bash
# Clone the repository
git clone https://github.com/joansala/seshat.git
cd seshat

# Install dependencies
poetry install
```

## Usage

### Running the Application

You can run Seshat directly with:

```bash
poetry run seshat
```

Show the command palette immediately:

```
poetry run seshat --show-palette
```

### Setting Up Global Hotkey

Add this to your OS keybindings to activate Seshat with a keyboard shortcut:

```bash
/usr/bin/env poetry -C /path/to/seshat/directory run seshat --show-palette
```

## Configuration

Create or edit the configuration file in your home directory:

```bash
nano ~/.config/seshat/config.json
```

### User Configuration Example

```json
{
    "window_width": 500,
    "window_height": 360,
    "paste_delay": 0.3,
    "paste_keybinding": "shift+Insert",
    "hotkey_poll_interval": 0.05,
    "hotkey_modifiers": ["KEY_LEFTMETA", "KEY_RIGHTMETA"],
    "hotkey_trigger": "KEY_SPACE",
    "max_user_commands": 100,
    "chat_base_url": "http://localhost:11434",
    "chat_default_model": "gemma3:4b",
    "chat_user_context": { // Any information you want the LLM to know
        "User name": "John",
        "Full user name": "John Doe",
        "User location": "England"
    }
}
```

## Development

### Setup Development Environment

```bash
# Install development dependencies
poetry install --with dev
```

### Project Structure

- `seshat/actions/`: Action providers for text, math, and AI operations
- `seshat/application/`: GTK application and UI components
- `seshat/resources/`: UI definitions, configuration, and themes
- `seshat/tasks/`: Task execution framework
- `seshat/utils/`: Utility functions for clipboard, config, and hotkeys

## License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.