#!/usr/bin/env python3
import os
import sys
import stat
import pwd
import tty
import termios
import select
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

def read_file_lines(path):
    try:
        with open(path, 'r', encoding='utf-8', errors='replace') as f:
            return f.read().splitlines()
    except Exception as e:
        return [f"!! ERROR READING FILE !!", str(e)]

# --- UI: ANSI Rendering ---

def get_key():
    """Reads a single keypress, including multi-byte escape sequences like arrows and Page Up/Down."""
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        # Read the first byte (blocks until a key is pressed)
        ch = os.read(fd, 1).decode('utf-8', errors='ignore')
        if ch == '\x1b':
            # Use a slightly longer timeout to ensure we capture the full sequence on macOS
            dr, dw, de = select.select([fd], [], [], 0.1)
            if dr:
                # Read all available data in the buffer (up to 10 bytes)
                ch += os.read(fd, 10).decode('utf-8', errors='ignore')
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch

def render(current_path, entries, selection, scroll, height, width, prompt=None, input_text="", view_mode="list"):
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

    # File List / File Content
    for i in range(height):
        idx = i + scroll
        if idx < len(entries):
            item = entries[idx]
            if view_mode == "list":
                meta = f"{item.get('perms','')}  {item.get('author',''):>8}  {item.get('size',''):>8}  {item.get('ctime','')} | {item.get('mtime','')}"
                name_w = width - len(meta) - 2
                name = item['name'][:name_w].ljust(name_w)
                line = f"{name} {meta}"
            else:
                # view_mode == "view": entries contains raw lines
                line = str(item)[:width].ljust(width)
            
            if idx == selection:
                output.append(f"{BLUE_BG}{line[:width]}{RESET}{CLEAR_LINE}")
            else:
                color = BLUE if view_mode == "list" and item.get('is_dir') else ""
                output.append(f"{color}{line[:width]}{RESET}{CLEAR_LINE}")
        else:
            output.append(CLEAR_LINE) # Empty space if directory/file is small

    # Overlay Dialog if prompt is active
    if prompt:
        dialog_w = min(40, width - 4)
        dialog_h = 3
        start_y = (height - dialog_h) // 2 + 1
        start_x = (width - dialog_w) // 2
        
        # Draw dialog over the file list
        output[start_y] = f"{' ' * start_x}┌{'─' * (dialog_w - 2)}┐{CLEAR_LINE}"
        output[start_y + 1] = f"{' ' * start_x}│ {prompt[:dialog_w-4].ljust(dialog_w-4)} │{CLEAR_LINE}"
        output[start_y + 2] = f"{' ' * start_x}│ > {input_text[:dialog_w-6].ljust(dialog_w-6)} │{CLEAR_LINE}"
        output[start_y + 3] = f"{' ' * start_x}└{'─' * (dialog_w - 2)}┘{CLEAR_LINE}"

    # Border: Bottom
    remaining = len(entries) - (scroll + height)
    if view_mode == "list":
        bot_label = " [ ^N: file | ^D: folder | Space: page | 'q': quit ] "
    else:
        bot_label = " [ 'q'/Esc: back | Space: page ] "
        
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
    input_type = None # None, "file", or "folder"
    input_text = ""
    view_mode = "list" # "list" or "view"
    file_lines = []
    
    # Store list state to restore after viewing
    entries_list = []
    selection_list = 0
    scroll_list = 0
    
    # Memory for directory positions: { path: (selection, scroll) }
    path_states = {}
    
    # Enter Alternate Screen Buffer and Hide cursor
    sys.stdout.write("\033[?1049h\033[?1h\033[?25l")
    sys.stdout.flush()

    try:
        while True:
            # Get terminal dimensions
            rows, cols = os.popen('stty size', 'r').read().split()
            rows, cols = int(rows), int(cols)
            # Use full screen height
            view_height = rows - 4
            if view_height < 5: view_height = 5

            if view_mode == "list":
                entries = get_file_info(current_path)
                header_path = current_path
            else:
                entries = file_lines
                header_path = os.path.join(current_path, entries_list[selection_list]['name'])

            prompt = None
            if input_type == "file": prompt = "Create New File:"
            elif input_type == "folder": prompt = "Create New Folder:"
            
            render(header_path, entries, selection, scroll, view_height, cols, 
                   prompt=prompt, input_text=input_text, view_mode=view_mode)

            key = get_key()
            
            if input_type:
                if key in ['\r', '\n']:
                    if input_text:
                        full_path = os.path.join(current_path, input_text)
                        if input_type == "file":
                            with open(full_path, 'w') as f: pass
                        elif input_type == "folder":
                            os.makedirs(full_path, exist_ok=True)
                    input_type = None
                    input_text = ""
                elif key == '\x1b': # Escape
                    input_type = None
                    input_text = ""
                elif key in ['\x7f', '\x08']: # Backspace
                    input_text = input_text[:-1]
                elif len(key) == 1 and ord(key) >= 32:
                    input_text += key
                continue

            if key in ['q', '\x1b']:
                if view_mode == "view":
                    view_mode = "list"
                    entries = entries_list
                    selection = selection_list
                    scroll = scroll_list
                    continue
                else:
                    break
            elif key == '\x0e' and view_mode == "list": # Ctrl+N
                input_type = "file"
                input_text = ""
            elif key == '\x04' and view_mode == "list": # Ctrl+D (Directory)
                input_type = "folder"
                input_text = ""
            elif key in ['\x1b[A', '\x1bOA', 'k']: # Up
                if selection > 0: selection -= 1
            elif key in ['\x1b[B', '\x1bOB', 'j']: # Down
                if selection < len(entries) - 1: selection += 1
            elif key in ['\x1b[D', '\x1bOD', '\x1b[H', '\x1b[1~', 'g']: # Left / Home / g
                selection = 0
            elif key in ['\x1b[C', '\x1bOC', '\x1b[F', '\x1b[4~', 'G']: # Right / End / G
                selection = len(entries) - 1
            elif key in ['\x1b[5~', '\x1b[5;2~', '\x1b[V', '\x02', 'u', 'b', '\x1b[1;2A', '\x1b[1;3A', '\x1b\x1b[A']: # Page Up variants
                selection = max(0, selection - view_height)
            elif key in ['\x1b[6~', '\x1b[6;2~', '\x1b[U', '\x06', 'd', ' ', '\x1b[1;2B', '\x1b[1;3B', '\x1b\x1b[B']: # Page Down variants
                selection = min(len(entries) - 1, selection + view_height)
            elif key in ['\r', '\n']: # Enter
                if view_mode == "list":
                    item = entries[selection]
                    if item.get('is_dir'):
                        # Save current state before leaving
                        path_states[current_path] = (selection, scroll)
                        
                        old_dir = os.path.basename(current_path.rstrip(os.sep))
                        new_path = os.path.abspath(os.path.join(current_path, item['name']))
                        
                        current_path = new_path
                        if current_path in path_states:
                            # Restore previous state for this directory
                            selection, scroll = path_states[current_path]
                        elif item['name'] == "..":
                            # Moving up to a parent we haven't "saved" yet
                            entries = get_file_info(current_path)
                            selection = 0
                            for idx, e in enumerate(entries):
                                if e['name'].rstrip('/') == old_dir:
                                    selection = idx
                                    break
                            # Place at the bottom of the screen as requested
                            scroll = max(0, selection - view_height + 1)
                        else:
                            # Moving down to a new directory
                            selection = 0
                            scroll = 0
                    else:
                        # Save list state
                        entries_list = entries
                        selection_list = selection
                        scroll_list = scroll
                        # Enter view mode
                        file_lines = read_file_lines(os.path.join(current_path, item['name']))
                        view_mode = "view"
                        selection = 0
                        scroll = 0
            
            # Auto-scroll logic
            if selection < scroll:
                scroll = selection
            elif selection >= scroll + view_height:
                scroll = selection - view_height + 1

    finally:
        # Exit Alternate Screen and show cursor again
        sys.stdout.write("\033[?1049l\033[?1l\033[?25h")
        sys.stdout.flush()

if __name__ == "__main__":
    main()