# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

**Look** is a single-file (`look.py`), zero-dependency terminal file explorer written in Python 3. Installed as the `lk` command via `install.sh`.

## Architecture

- `look.py` — all logic in one file (~285 lines). No tests, no build step.
- **Key functions**: `get_file_info()` reads directory entries with metadata; `get_key()` handles raw terminal input with escape sequence parsing; `render()` draws the TUI using ANSI codes; `main()` is the event loop.
- **State management**: `path_states` dict remembers cursor position per directory; `view_mode` toggles between directory listing and file content viewing.
- **Shell integration**: Writes final cwd to `/tmp/lk-cwd` for the `lk()` shell wrapper to `cd` into after exit.

## Development

- **Run**: `python3 look.py` from any directory.
- **Install**: `./install.sh` (copies `look.py` to `/usr/local/bin/lk-bin` and adds `lk()` shell wrapper to your config).
- **Uninstall**: Manually remove `/usr/local/bin/lk-bin` and the `lk()` function from `~/.zshrc` or `~/.bashrc`.
