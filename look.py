#!/usr/bin/env python3
import os
import sys
import stat
import pwd
import tty
import termios
from datetime import datetime

# --- Logic: Metadata & Files ---

def format_size(size):
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024: return f"{size:4.1f}{unit}"
        size /= 1024
    return f"{size:.1f}TB"

def get_file_info(path):
    try:
        files = os.listdir(path)
        files = [".."] + sorted(files, key=lambda s: s.lower())
        data = []
        for f in files:
            full_path = os.path.join(path, f)
            is_dir = os.path.isdir(full_path)
            name = f + ("/" if is_dir and f != ".." else "")
            try:
                s = os.stat(full_path)
                perms = stat.filemode(s.st_mode)
                size = "DIR" if is_dir else format_size(s.st_size)
                author = pwd.getpwuid(s.st_uid).pw_name
                ctime = datetime.fromtimestamp(s.st_ctime).strftime('%b %d %Y')
                mtime = datetime.fromtimestamp(s.st_mtime).strftime('%b %d %Y')
            except:
                perms, size, author, ctime, mtime = "----------", "???", "???", "---", "---"
            data.append({"name": name, "perms": perms, "size": size, "author": author, "ctime": ctime, "mtime": mtime, "is_dir": is_dir})
        return data
    except PermissionError:
        return [{"name": "..", "is_dir": True}, {"name": "!! PERMISSION DENIED !!", "is_dir": False}]

# --- UI: ANSI Rendering ---

def get_key():
    """Reads a single keypress, including multi-byte arrow keys."""
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
        if ch == '\x1b': # Escape sequence
            ch += sys.stdin.read(2)
            if ch.endswith('['): # Further sequences (like PageUp)
                ch += sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch

def render(current_path, entries, selection, scroll, height, width):
    output = []
    
    # Colors
    BLUE_BG = "\033[44m\033[37m"
    BLUE = "\033[34m"
    YELLOW = "\033[33m"
    RESET = "\033[0m"
    CLEAR_LINE = "\033[K"

    # Border: Top
    top_label = f" {current_path} "
    if scroll > 0: top_label += f" [ ↑ {scroll} more ] "
    output.append(f"{YELLOW}─ {top_label}{'─' * (width - len(top_label) - 2)}{RESET}{CLEAR_LINE}")

    # File List
    for i in range(height):
        idx = i + scroll
        if idx < len(entries):
            item = entries[idx]
            meta = f"{item.get('perms','')}  {item.get('author',''):>8}  {item.get('size',''):>8}  {item.get('ctime','')} | {item.get('mtime','')}"
            name_w = width - len(meta) - 2
            name = item['name'][:name_w].ljust(name_w)
            
            line = f"{name} {meta}"
            if idx == selection:
                output.append(f"{BLUE_BG}{line[:width]}{RESET}{CLEAR_LINE}")
            else:
                color = BLUE if item.get('is_dir') else ""
                output.append(f"{color}{line[:width]}{RESET}{CLEAR_LINE}")
        else:
            output.append(CLEAR_LINE) # Empty space if directory is small

    # Border: Bottom
    remaining = len(entries) - (scroll + height)
    bot_label = " [ 'q': quit ] "
    if remaining > 0: bot_label = f" [ ↓ {remaining} more ]" + bot_label
    output.append(f"{YELLOW}─ {bot_label}{'─' * (width - len(bot_label) - 2)}{RESET}{CLEAR_LINE}")

    # Print all at once
    sys.stdout.write("\n".join(output))
    # Move cursor back up to the start of the widget
    sys.stdout.write(f"\033[{len(output) - 1}A\r")
    sys.stdout.flush()

def main():
    current_path = os.getcwd()
    selection = 0
    scroll = 0
    
    # Hide cursor
    sys.stdout.write("\033[?25l")
    sys.stdout.flush()

    try:
        while True:
            # Get terminal dimensions
            rows, cols = os.popen('stty size', 'r').read().split()
            rows, cols = int(rows), int(cols)
            view_height = (rows // 2) - 2
            if view_height < 1: view_height = 5

            entries = get_file_info(current_path)
            render(current_path, entries, selection, scroll, view_height, cols)

            key = get_key()
            if key == 'q':
                # Move cursor to the bottom of the widget before exiting
                sys.stdout.write(f"\033[{view_height + 2}B\n")
                break
            elif key == '\x1b[A': # Up
                if selection > 0: selection -= 1
            elif key == '\x1b[B': # Down
                if selection < len(entries) - 1: selection += 1
            elif key == '\x1b[D': # Left
                selection = 0
            elif key == '\x1b[C': # Right
                selection = len(entries) - 1
            elif key == '\x1b[5~': # Page Up
                selection = max(0, selection - view_height)
            elif key == '\x1b[6~': # Page Down
                selection = min(len(entries) - 1, selection + view_height)
            elif key in ['\r', '\n']: # Enter
                item = entries[selection]
                if item.get('is_dir'):
                    current_path = os.path.abspath(os.path.join(current_path, item['name']))
                    selection = 0
                    scroll = 0
            
            # Auto-scroll logic
            if selection < scroll:
                scroll = selection
            elif selection >= scroll + view_height:
                scroll = selection - view_height + 1

    finally:
        # Show cursor again
        sys.stdout.write("\033[?25h")
        sys.stdout.flush()

if __name__ == "__main__":
    main()