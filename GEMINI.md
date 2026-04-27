# Gemini CLI Project Context: Look-Gemini

## Project Overview
**Look-Gemini** is a lightweight, terminal-based file explorer written in Python. It provides a simple TUI (Terminal User Interface) to navigate the file system, view file metadata (permissions, owner, size, and modification dates), and traverse directories.

### Key Technologies
- **Python 3**: The core language used for the implementation.
- **Standard Library**: Uses `os`, `sys`, `stat`, `pwd`, `tty`, `termios`, and `datetime`.
- **ANSI Escape Sequences**: Used for rendering the UI, colors, and cursor manipulation.
- **Low-level Input**: Utilizes `termios` and `tty` to handle raw keyboard input (e.g., arrow keys).

### Architecture
The project is contained within a single executable script: `look.py`.
- **Metadata Logic**: `get_file_info` and `format_size` handle file system interactions and data formatting.
- **UI Rendering**: `render` handles drawing the file list, borders, and metadata to the terminal.
- **Input Handling**: `get_key` captures single-character and multi-byte escape sequences for navigation.
- **Main Loop**: `main` manages the application state (current path, selection, scroll) and the event loop.

## Building and Running
The application requires Python 3 and runs on Unix-like systems (macOS, Linux) due to its dependence on `termios` and `tty`.

### Running the Application
```bash
python3 look.py
```
Or, if the file has execution permissions:
```bash
./look.py
```

### Controls
- **Up/Down Arrows**: Move selection.
- **Left/Right Arrows**: Jump to the top/bottom of the directory.
- **Page Up/Page Down**: Scroll through long lists.
- **Enter**: Navigate into the selected directory or go up (via `..`).
- **q**: Quit the application.

## Development Conventions
- **Single File Implementation**: The current design prioritizes simplicity by keeping all logic in `look.py`.
- **No External Dependencies**: To maintain portability, only Python's standard library is used.
- **Direct Terminal Manipulation**: UI is rendered using manual ANSI codes rather than a library like `curses` or `urwid`.
- **Error Handling**: Basic `try-except` blocks are used to handle permission issues or missing file metadata.
