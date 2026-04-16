# Look

**Look** is a lightweight, zero-dependency terminal file explorer written in Python. It provides a fast, visual way to navigate your file system, view metadata, and perform basic file operations without leaving your terminal.

## Features

- ⚡ **Lightning Fast**: Instant directory traversal and rendering.
- 📂 **Metadata at a Glance**: View permissions, owners, sizes, and timestamps.
- ⌨️ **Keyboard Centric**: Full control via intuitive hotkeys.
- 🛠️ **File Operations**: Quickly create new files and folders with built-in dialogs.
- 📦 **Zero Dependencies**: Runs on any Unix-like system with Python 3 (no `pip install` required).

## Installation

To install **Look** as the `lk` command on your system, run the provided installation script:

```bash
# Clone the repository and run the script
chmod +x install.sh
./install.sh
```

The script will:
1. Make `look.py` executable.
2. Install it as the `lk` command in a directory in your PATH (e.g., `/usr/local/bin`).

Now you can launch the explorer from any directory by simply typing:
```bash
lk
```

## Controls

| Key | Action |
| :--- | :--- |
| `↑` / `↓` | Move selection (or `j` / `k`) |
| `←` / `→` | Jump to top / bottom of directory (or `g` / `G`) |
| `Space` / `d` | **Page Down** (Reliable on macOS) |
| `b` / `u` | **Page Up** (Reliable on macOS) |
| `PgUp` / `PgDn` | Standard Scroll (may be intercepted by some terminals) |
| `Enter` | Navigate into the selected directory |
| `Ctrl+N` | **New File**: Open dialog to create a file |
| `Ctrl+D` | **New Folder**: Open dialog to create a directory |
| `Esc` | Dismiss new file/folder dialog |
| `q` | Quit the application |

## Requirements

- **Python 3.6+**
- **Unix-like OS** (macOS, Linux, BSD)

## License

This project is open-source and available under the [MIT License](LICENSE).
