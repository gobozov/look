#!/usr/bin/env python3
import os
import sys
import stat
import pwd
import tty
import termios
import select
import re
from datetime import datetime

# --- Logic: Metadata & Files ---

def strip_ansi(s):
    return re.sub(r'\x1b\[[0-9;]*[mK]', '', s)

def visible_len(s):
    return len(strip_ansi(s))

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
                extra = os.read(fd, 10).decode('utf-8', errors='ignore')
                ch += extra
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch

def render(current_path, entries, selection, scroll, height, width, prompt=None, input_text="", view_mode="list", search_text=None):
    # Colors
    BLUE_BG = "\033[44m\033[37m"
    BLUE = "\033[34m"
    YELLOW = "\033[33m"
    WHITE = "\033[1m"
    RESET = "\033[0m"

    lines = []

    # 1. Top Border
    top_label = f" {current_path} "
    if scroll > 0: top_label += f" [ ↑ {scroll} more ] "
    # Truncate path if it's too long to avoid wrapping
    while visible_len(top_label) > width - 4:
        top_label = "..." + top_label[-(width - 8):]
    
    padding = width - visible_len(top_label) - 2
    lines.append(f"{YELLOW}─{top_label}{'─' * max(0, padding)}{RESET}")

    # 2. Entries
    for i in range(height):
        idx = i + scroll
        if idx < len(entries):
            item = entries[idx]
            if view_mode == "list":
                meta = f"{item.get('perms','')}  {item.get('author',''):>8}  {item.get('size',''):>8}  {item.get('ctime','')} | {item.get('mtime','')}"
                name_w = width - len(meta) - 2
                name = item['name'][:max(0, name_w)].ljust(max(0, name_w))
                line_content = f"{name} {meta}"
                color = BLUE if item.get('is_dir') else ""
            else:
                # view_mode == "view": entries contains raw lines
                # Replace tabs with spaces and strictly truncate to avoid wrapping
                line_content = str(item).replace('\t', '    ')[:width]
                color = ""
            
            if idx == selection:
                lines.append(f"{BLUE_BG}{line_content.ljust(width)}{RESET}")
            else:
                lines.append(f"{color}{line_content.ljust(width)}{RESET}")
        else:
            lines.append(" " * width)

    # 3. Bottom Border
    remaining = len(entries) - (scroll + height)
    if view_mode == "list":
        if search_text is not None:
            bot_label = f" [{WHITE}{YELLOW}⌕ {search_text}{RESET} {YELLOW}| {RESET}^N: file | ^D: folder | Space: page | 'q': quit ] "
        else:
            bot_label = " [ ^N: file | ^D: folder | Space: page | 'q': quit ] "
    else:
        bot_label = " [ 'q'/Esc: back | Space: page ] "
        
    if remaining > 0: bot_label = f" [ ↓ {remaining} more ]" + bot_label
    
    # Use visible_len to account for ANSI codes in bot_label
    padding = width - visible_len(bot_label) - 2
    lines.append(f"{YELLOW}─{bot_label}{'─' * max(0, padding)}{RESET}")

    # 4. Patch with Dialog if active
    if prompt:
        dialog_w = min(40, width - 4)
        dialog_h = 3
        start_y = (height - dialog_h) // 2 + 1
        start_x = (width - dialog_w) // 2
        
        if 0 <= start_y < len(lines) - 4:
            lines[start_y] = f"{' ' * start_x}┌{'─' * (dialog_w - 2)}┐".ljust(width)
            lines[start_y + 1] = f"{' ' * start_x}│ {prompt[:dialog_w-4].ljust(dialog_w-4)} │".ljust(width)
            lines[start_y + 2] = f"{' ' * start_x}│ > {input_text[:dialog_w-6].ljust(dialog_w-6)} │".ljust(width)
            lines[start_y + 3] = f"{' ' * start_x}└{'─' * (dialog_w - 2)}┘".ljust(width)

    # 5. Final Output
    # Move cursor to top-left, print lines, and clear the rest of the screen
    sys.stdout.write("\033[H")
    for i, line in enumerate(lines):
        sys.stdout.write(line)
        if i < len(lines) - 1:
            sys.stdout.write("\n")
    sys.stdout.write("\033[J")
    sys.stdout.flush()

def main():
    current_path = os.getcwd()
    selection = 0
    scroll = 0
    input_type = None # None, "file", or "folder"
    input_text = ""
    view_mode = "list" # "list" or "view"
    file_lines = []
    search_text = None

    # Cache for entries to avoid re-fetching every loop
    entries = []
    needs_refresh = True

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
            view_height = rows - 4
            if view_height < 5: view_height = 5

            # Refresh entries if needed
            if needs_refresh:
                if view_mode == "list":
                    entries = get_file_info(current_path)
                else:
                    entries = file_lines
                needs_refresh = False

            # Ensure selection is in bounds
            if not entries:
                selection = 0
            else:
                selection = max(0, min(selection, len(entries) - 1))

            # Auto-scroll logic (must be before render)
            if selection < scroll:
                scroll = selection
            elif selection >= scroll + view_height:
                scroll = max(0, selection - view_height + 1)

            # Additional check to ensure scroll is sane
            if scroll > max(0, len(entries) - view_height):
                scroll = max(0, len(entries) - view_height)

            if view_mode == "list":
                header_path = current_path
            else:
                header_path = os.path.join(current_path, entries_list[selection_list]['name'])

            prompt = None
            if input_type == "file": prompt = "Create New File:"
            elif input_type == "folder": prompt = "Create New Folder:"

            render(header_path, entries, selection, scroll, view_height, cols,
                   prompt=prompt, input_text=input_text, view_mode=view_mode, search_text=search_text)

            key = get_key()

            # 1. Dialog Input Mode (Ctrl+N / Ctrl+D)
            if input_type:
                if key in ['\r', '\n']:
                    if input_text:
                        full_path = os.path.join(current_path, input_text)
                        if input_type == "file":
                            with open(full_path, 'w') as f: pass
                        elif input_type == "folder":
                            os.makedirs(full_path, exist_ok=True)
                        needs_refresh = True
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

            # 2. Automatic Search & Navigation
            is_printable = len(key) == 1 and 32 <= ord(key) < 127 and key != '/'

            # Start search on printable char or '/'
            if view_mode == "list" and search_text is None and (is_printable or key == '/'):
                search_text = "" if key == '/' else key
                if search_text:
                    for idx, entry in enumerate(entries):
                        if entry['name'].lower().startswith(search_text.lower()):
                            selection = idx
                            break
                if key != '/': continue # Key handled as start of search
                else: continue # Key handled as search trigger

            if view_mode == "list" and search_text is not None:
                if key == '\x1b':
                    search_text = None
                    continue
                elif key in ['\x7f', '\x08']: # Backspace (Priority check)
                    if search_text == "":
                        search_text = None # Exit search if buffer already empty
                    else:
                        search_text = search_text[:-1]
                        if search_text:
                            for idx, entry in enumerate(entries):
                                if entry['name'].lower().startswith(search_text.lower()):
                                    selection = idx
                                    break
                    continue
                elif len(key) == 1 and 32 <= ord(key) < 127:
                    search_text += key
                    for idx, entry in enumerate(entries):
                        if entry['name'].lower().startswith(search_text.lower()):
                            selection = idx
                            break
                    continue
                elif key in ['\r', '\n']:
                    search_text = None
                    # Fall through to allow Enter to open selection
                else:
                    # Navigation keys (arrows, etc.) cancel search but perform action
                    search_text = None
            # 3. Main Navigation and Commands
            if key in ['q', '\x1b']:

                if view_mode == "view":
                    view_mode = "list"
                    entries = entries_list
                    selection = selection_list
                    scroll = scroll_list
                    needs_refresh = False # Already restored
                    continue
                else:
                    break
            elif key == '\x0e' and view_mode == "list": # Ctrl+N
                input_type = "file"
                input_text = ""
            elif key == '\x04' and view_mode == "list": # Ctrl+D
                input_type = "folder"
                input_text = ""
            elif key in ['\x1b[A', '\x1bOA', 'k']: # Up
                selection -= 1
            elif key in ['\x1b[B', '\x1bOB', 'j']: # Down
                selection += 1
            elif key in ['\x1b[D', '\x1bOD', '\x1b[H', '\x1b[1~', 'g']: # Left / Home / g
                selection = 0
            elif key in ['\x1b[C', '\x1bOC', '\x1b[F', '\x1b[4~', 'G']: # Right / End / G
                selection = len(entries) - 1
            elif key in ['\x1b[5~', '\x1b[5;2~', '\x1b[V', '\x02', 'u', 'b', '\x1b[1;2A', '\x1b[1;3A', '\x1b\x1b[A']: # Page Up
                selection -= view_height
            elif key in ['\x1b[6~', '\x1b[6;2~', '\x1b[U', '\x06', 'd', ' ', '\x1b[1;2B', '\x1b[1;3B', '\x1b\x1b[B']: # Page Down
                selection += view_height
            elif key in ['\r', '\n']: # Enter
                if view_mode == "list" and entries:
                    item = entries[selection]
                    if item.get('is_dir'):
                        path_states[current_path] = (selection, scroll)
                        old_dir = os.path.basename(current_path.rstrip(os.sep))
                        new_path = os.path.abspath(os.path.join(current_path, item['name']))
                        current_path = new_path
                        needs_refresh = True
                        if current_path in path_states:
                            selection, scroll = path_states[current_path]
                        elif item['name'] == "..":
                            # We'll find the selection after refresh
                            pass
                        else:
                            selection, scroll = 0, 0
                    else:
                        entries_list = entries
                        selection_list = selection
                        scroll_list = scroll
                        file_lines = read_file_lines(os.path.join(current_path, item['name']))
                        view_mode = "view"
                        selection, scroll = 0, 0
                        needs_refresh = True

            # Post-action: find selection if we just moved up
            if needs_refresh and view_mode == "list" and current_path not in path_states and item.get('name') == "..":
                # This is a bit tricky since entries isn't refreshed yet. 
                # We'll handle it by checking needs_refresh at top of loop.
                pass

            # Special case for ".." navigation to parent
            if needs_refresh and view_mode == "list" and 'old_dir' in locals():
                # Fetch immediately to find the old directory in the new list
                entries = get_file_info(current_path)
                needs_refresh = False
                selection = 0
                for idx, e in enumerate(entries):
                    if e['name'].rstrip('/') == old_dir:
                        selection = idx
                        break
                scroll = max(0, selection - view_height + 1)
                del old_dir


    finally:
        # Save final path for the shell wrapper
        try:
            with open("/tmp/lk-cwd", "w") as f:
                f.write(current_path)
        except:
            pass
            
        # Exit Alternate Screen and show cursor again
        sys.stdout.write("\033[?1049l\033[?1l\033[?25h")
        sys.stdout.flush()

if __name__ == "__main__":
    main()