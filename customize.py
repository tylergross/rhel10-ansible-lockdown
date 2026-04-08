#!/usr/bin/env python3
# Author: Tyler Gross
# Website: TGTechAcademy.com
#
# RHEL 10 STIG Customizer
# Interactive CLI tool for reviewing and toggling STIG control defaults.
# Reads:  roles/rhel10-stig/defaults/main.yml  (source of truth)
#         roles/rhel10-stig/vars/main.yml       (existing overrides)
# Writes: roles/rhel10-stig/vars/main.yml       (saves only changed values)
#
# Usage: python3 customize.py

import curses
import os
import re
import sys
import textwrap
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SCRIPT_DIR   = Path(__file__).parent.resolve()
DEFAULTS_FILE = SCRIPT_DIR / "roles/rhel10-stig/defaults/main.yml"
VARS_FILE     = SCRIPT_DIR / "roles/rhel10-stig/vars/main.yml"
TASKS_DIR     = SCRIPT_DIR / "roles/rhel10-stig/tasks"

# ---------------------------------------------------------------------------
# Color pair IDs
# ---------------------------------------------------------------------------
C_HEADER   = 1   # Title bar
C_FOOTER   = 2   # Key-hint bar
C_SEL      = 3   # Selected row highlight
C_HIGH     = 4   # HIGH severity
C_MEDIUM   = 5   # MEDIUM severity
C_LOW      = 6   # LOW severity
C_ON       = 7   # Enabled checkmark
C_OFF      = 8   # Disabled checkmark
C_BORDER   = 9   # Popup border
C_POPBG    = 10  # Popup background
C_SEARCH   = 11  # Search bar
C_CHANGED  = 12  # Unsaved change indicator


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------

def parse_defaults():
    """Return list of control dicts parsed from defaults/main.yml."""
    controls = []
    pending = None

    with open(DEFAULTS_FILE, "r") as fh:
        lines = fh.readlines()

    for line in lines:
        line = line.rstrip("\r\n")

        # Comment line with STIG metadata
        m = re.match(
            r"^# (RHEL-10-\d+)\s*\|\s*(HIGH|MEDIUM|LOW)\s*\|\s*(.+)$",
            line, re.IGNORECASE
        )
        if m:
            pending = (m.group(1).upper(), m.group(2).upper(), m.group(3).strip())
            continue

        # Boolean control variable
        m = re.match(r"^(rhel_10_(\d+)):\s*(true|false)\s*$", line)
        if m and pending:
            var, num, raw = m.group(1), m.group(2), m.group(3)
            stig_id, severity, title = pending
            controls.append({
                "var":      var,
                "stig_id":  stig_id,
                "severity": severity,
                "title":    title,
                "default":  raw == "true",
                "enabled":  raw == "true",   # will be overridden by vars/main.yml
                "original": raw == "true",   # tracks what was loaded (to detect changes)
            })
            pending = None
            continue

        # Non-comment, non-blank line resets pending
        if line.strip() and not line.startswith("#"):
            pending = None

    return controls


def apply_var_overrides(controls):
    """Read vars/main.yml and apply any existing overrides in-place."""
    if not VARS_FILE.exists():
        return

    with open(VARS_FILE, "r") as fh:
        lines = fh.readlines()

    overrides = {}
    for line in lines:
        m = re.match(r"^(rhel_10_\d+):\s*(true|false)", line.rstrip("\r\n"))
        if m:
            overrides[m.group(1)] = m.group(2) == "true"

    for ctrl in controls:
        if ctrl["var"] in overrides:
            ctrl["enabled"]  = overrides[ctrl["var"]]
            ctrl["original"] = overrides[ctrl["var"]]


def parse_task_detail(stig_id):
    """Return a dict with Description, Check Text, Fix Text from the task file."""
    filename = stig_id.lower() + ".yml"
    task_file = TASKS_DIR / filename

    if not task_file.exists():
        return {}

    with open(task_file, "r") as fh:
        content = fh.read()

    # Header block sits between the two # ===... lines
    header_match = re.search(r"# =+\n(.*?)# =+\n", content, re.DOTALL)
    if not header_match:
        return {}

    header = header_match.group(1)
    detail = {}

    # Single-line fields
    for field in ("STIG ID", "Rule ID", "Severity", "CCI", "Title"):
        m = re.search(rf"# {re.escape(field)}\s*:\s*(.+)", header)
        if m:
            detail[field] = m.group(1).strip()

    # Multi-line fields (indented comment blocks)
    for field in ("Description", "Check Text", "Fix Text"):
        pattern = rf"# {re.escape(field)}:\n((?:#[^\n]*\n)*)"
        m = re.search(pattern, header)
        if m:
            raw_lines = m.group(1).splitlines()
            text = "\n".join(ln.lstrip("#").lstrip(" ") for ln in raw_lines).strip()
            detail[field] = text

    return detail


def save_vars(controls):
    """Write only overridden values to vars/main.yml.  Returns count saved."""
    # Build override dict: any control whose current value differs from its default
    overrides = {}
    for ctrl in controls:
        if ctrl["enabled"] != ctrl["default"]:
            overrides[ctrl["var"]] = "true" if ctrl["enabled"] else "false"

    lines = [
        "# Author: Tyler Gross\n",
        "# Website: TGTechAcademy.com\n",
        "---\n",
        "# rhel10-stig | vars override file\n",
        "# Generated by customize.py — edit manually with care.\n",
        "# Only controls that differ from defaults/main.yml are listed here.\n",
        "#\n",
    ]

    if overrides:
        lines.append("# Custom overrides:\n")
        for var in sorted(overrides):
            lines.append(f"{var}: {overrides[var]}\n")
    else:
        lines.append("# No overrides — all controls use their default values.\n")

    with open(VARS_FILE, "w") as fh:
        fh.writelines(lines)

    # Update 'original' to reflect the saved state
    for ctrl in controls:
        ctrl["original"] = ctrl["enabled"]

    return len(overrides)


# ---------------------------------------------------------------------------
# TUI helpers
# ---------------------------------------------------------------------------

def init_colors():
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(C_HEADER,  curses.COLOR_BLACK,  curses.COLOR_CYAN)
    curses.init_pair(C_FOOTER,  curses.COLOR_BLACK,  curses.COLOR_WHITE)
    curses.init_pair(C_SEL,     curses.COLOR_BLACK,  curses.COLOR_WHITE)
    curses.init_pair(C_HIGH,    curses.COLOR_RED,    -1)
    curses.init_pair(C_MEDIUM,  curses.COLOR_YELLOW, -1)
    curses.init_pair(C_LOW,     curses.COLOR_GREEN,  -1)
    curses.init_pair(C_ON,      curses.COLOR_GREEN,  -1)
    curses.init_pair(C_OFF,     curses.COLOR_RED,    -1)
    curses.init_pair(C_BORDER,  curses.COLOR_CYAN,   -1)
    curses.init_pair(C_POPBG,   curses.COLOR_WHITE,  curses.COLOR_BLACK)
    curses.init_pair(C_SEARCH,  curses.COLOR_BLACK,  curses.COLOR_YELLOW)
    curses.init_pair(C_CHANGED, curses.COLOR_MAGENTA,-1)


def sev_color(severity):
    return {
        "HIGH":   C_HIGH,
        "MEDIUM": C_MEDIUM,
        "LOW":    C_LOW,
    }.get(severity, 0)


def draw_header(stdscr, title, rows, cols):
    stdscr.attron(curses.color_pair(C_HEADER) | curses.A_BOLD)
    stdscr.addstr(0, 0, title.center(cols)[:cols])
    stdscr.attroff(curses.color_pair(C_HEADER) | curses.A_BOLD)


def draw_footer(stdscr, hint, rows, cols):
    # Truncate to cols-1 to avoid writing to the bottom-right cell,
    # which causes curses to throw when it tries to advance past the screen.
    stdscr.attron(curses.color_pair(C_FOOTER))
    try:
        stdscr.addstr(rows - 1, 0, hint[:cols - 1].ljust(cols - 1))
    except curses.error:
        pass
    stdscr.attroff(curses.color_pair(C_FOOTER))


def draw_stats_bar(stdscr, controls, visible, row, cols):
    total   = len(controls)
    enabled = sum(1 for c in controls if c["enabled"])
    changed = sum(1 for c in controls if c["enabled"] != c["original"])
    shown   = len(visible)
    bar = (
        f"  Total: {total}  |  Shown: {shown}  |"
        f"  Enabled: {enabled}  Disabled: {total - enabled}"
    )
    if changed:
        bar += f"  |  * {changed} unsaved change(s)"
    stdscr.attron(curses.color_pair(C_HEADER))
    stdscr.addstr(row, 0, bar.ljust(cols)[:cols])
    stdscr.attroff(curses.color_pair(C_HEADER))


def draw_list(stdscr, visible, cursor, scroll, list_top, list_height, cols):
    """Render the visible portion of the control list."""
    for i in range(list_height):
        idx = scroll + i
        row = list_top + i
        if idx >= len(visible):
            stdscr.move(row, 0)
            stdscr.clrtoeol()
            continue

        ctrl     = visible[idx]
        selected = idx == cursor
        changed  = ctrl["enabled"] != ctrl["original"]

        check = "[*]" if ctrl["enabled"] else "[ ]"
        sev   = ctrl["severity"][:3]
        title = ctrl["title"]

        # Build the line
        max_title = cols - 30
        if len(title) > max_title:
            title = title[:max_title - 1] + "…"

        line = f" {check} {ctrl['stig_id']:<18} {sev:<6} {title}"

        if selected:
            stdscr.attron(curses.color_pair(C_SEL) | curses.A_BOLD)
            stdscr.addstr(row, 0, line.ljust(cols)[:cols])
            stdscr.attroff(curses.color_pair(C_SEL) | curses.A_BOLD)
        else:
            stdscr.move(row, 0)
            stdscr.clrtoeol()

            # Checkbox
            check_color = C_ON if ctrl["enabled"] else C_OFF
            stdscr.addstr(row, 1, check, curses.color_pair(check_color) | curses.A_BOLD)

            # STIG ID (with unsaved marker)
            col = 5
            if changed:
                stdscr.addstr(row, col, ctrl["stig_id"], curses.color_pair(C_CHANGED) | curses.A_BOLD)
            else:
                stdscr.addstr(row, col, ctrl["stig_id"])
            col += 19

            # Severity badge
            stdscr.addstr(row, col, f"{sev:<6}", curses.color_pair(sev_color(ctrl["severity"])) | curses.A_BOLD)
            col += 7

            # Title
            stdscr.addstr(row, col, title)


# ---------------------------------------------------------------------------
# Info popup
# ---------------------------------------------------------------------------

def show_info_popup(stdscr, ctrl):
    rows, cols = stdscr.getmaxyx()
    detail = parse_task_detail(ctrl["stig_id"])

    # Build content lines
    content = []
    content.append(f"  STIG ID  : {ctrl['stig_id']}")
    content.append(f"  Severity : {ctrl['severity']}")
    content.append(f"  CCI      : {detail.get('CCI', 'N/A')}")
    content.append(f"  Rule ID  : {detail.get('Rule ID', 'N/A')}")
    content.append(f"  Status   : {'ENABLED' if ctrl['enabled'] else 'DISABLED'}")
    content.append("")
    content.append(f"  Title:")

    wrap_width = max(cols - 10, 20)
    for ln in textwrap.wrap(ctrl["title"], wrap_width - 4):
        content.append(f"    {ln}")

    for section in ("Description", "Check Text", "Fix Text"):
        text = detail.get(section)
        if not text:
            continue
        content.append("")
        content.append(f"  {section}:")
        for para in text.split("\n"):
            if para.strip():
                for ln in textwrap.wrap(para.strip(), wrap_width - 4):
                    content.append(f"    {ln}")
            else:
                content.append("")

    # Popup dimensions
    pop_h = min(rows - 4, len(content) + 4)
    pop_w = min(cols - 4, wrap_width + 4)
    pop_y = (rows - pop_h) // 2
    pop_x = (cols - pop_w) // 2

    win = curses.newwin(pop_h, pop_w, pop_y, pop_x)
    win.keypad(True)

    scroll = 0
    view_h = pop_h - 3   # lines available inside border

    title_bar = f" {ctrl['stig_id']} | {ctrl['severity']} "

    while True:
        win.erase()
        win.attron(curses.color_pair(C_BORDER))
        win.box()
        win.attroff(curses.color_pair(C_BORDER))

        # Title
        win.attron(curses.color_pair(C_BORDER) | curses.A_BOLD)
        win.addstr(0, 2, title_bar[:pop_w - 4])
        win.attroff(curses.color_pair(C_BORDER) | curses.A_BOLD)

        # Content
        for i in range(view_h):
            ln_idx = scroll + i
            if ln_idx >= len(content):
                break
            line = content[ln_idx][:pop_w - 2]
            win.addstr(i + 1, 1, line)

        # Scroll indicator + footer
        scroll_pct = int(100 * scroll / max(1, len(content) - view_h)) if len(content) > view_h else 100
        footer = f" ↑↓ scroll  q/ESC close  [{scroll_pct}%] "
        win.attron(curses.color_pair(C_FOOTER))
        win.addstr(pop_h - 1, 1, footer[:pop_w - 2].ljust(pop_w - 2))
        win.attroff(curses.color_pair(C_FOOTER))

        win.refresh()

        key = win.getch()
        if key in (ord("q"), ord("Q"), 27, curses.KEY_ENTER, 10, 13):
            break
        elif key == curses.KEY_UP and scroll > 0:
            scroll -= 1
        elif key == curses.KEY_DOWN and scroll < max(0, len(content) - view_h):
            scroll += 1
        elif key == curses.KEY_PPAGE:
            scroll = max(0, scroll - view_h)
        elif key == curses.KEY_NPAGE:
            scroll = min(max(0, len(content) - view_h), scroll + view_h)

    del win
    stdscr.touchwin()
    stdscr.refresh()


# ---------------------------------------------------------------------------
# Main TUI
# ---------------------------------------------------------------------------

def main(stdscr):
    curses.curs_set(0)
    stdscr.keypad(True)
    init_colors()

    controls = parse_defaults()
    apply_var_overrides(controls)

    sev_filter  = "ALL"   # ALL / HIGH / MEDIUM / LOW
    search_str  = ""
    search_mode = False
    status_msg  = ""
    cursor      = 0
    scroll      = 0

    def get_visible():
        out = controls
        if sev_filter != "ALL":
            out = [c for c in out if c["severity"] == sev_filter]
        if search_str:
            q = search_str.lower()
            out = [c for c in out if q in c["stig_id"].lower() or q in c["title"].lower()]
        return out

    while True:
        rows, cols = stdscr.getmaxyx()
        visible   = get_visible()
        list_top  = 3          # rows 0=header, 1=stats, 2=column labels
        list_bot  = rows - 2   # row -1=footer, row -2=status/search
        list_h    = list_bot - list_top

        # Clamp cursor
        if visible:
            cursor = max(0, min(cursor, len(visible) - 1))
            if cursor < scroll:
                scroll = cursor
            if cursor >= scroll + list_h:
                scroll = cursor - list_h + 1
        else:
            cursor = scroll = 0

        # --- Draw ---
        stdscr.erase()

        draw_header(stdscr,
            "RHEL 10 STIG Customizer  |  Author: Tyler Gross  |  TGTechAcademy.com",
            rows, cols)
        draw_stats_bar(stdscr, controls, visible, 1, cols)

        # Column labels
        labels = f"  {'':3} {'STIG ID':<18} {'SEV':<6} TITLE"
        stdscr.attron(curses.A_UNDERLINE)
        stdscr.addstr(2, 0, labels[:cols])
        stdscr.attroff(curses.A_UNDERLINE)

        draw_list(stdscr, visible, cursor, scroll, list_top, list_h, cols)

        # Status / search bar (second-to-last row)
        safe = cols - 1
        if search_mode:
            stdscr.attron(curses.color_pair(C_SEARCH))
            stdscr.addstr(rows - 2, 0, f" Search: {search_str}_".ljust(safe)[:safe])
            stdscr.attroff(curses.color_pair(C_SEARCH))
        elif status_msg:
            stdscr.attron(curses.A_BOLD)
            stdscr.addstr(rows - 2, 0, f" {status_msg}".ljust(safe)[:safe])
            stdscr.attroff(curses.A_BOLD)
        else:
            filter_indicator = f" Filter: [{sev_filter}]"
            stdscr.addstr(rows - 2, 0, filter_indicator.ljust(safe)[:safe])

        # Footer key hints
        footer = (
            " ↑↓:nav  SPC:toggle  i/ENTER:info"
            "  /:search  f:filter  s:save  q:quit"
        )
        draw_footer(stdscr, footer, rows, cols)

        stdscr.refresh()

        # --- Input ---
        key = stdscr.getch()
        status_msg = ""

        # Search mode
        if search_mode:
            if key in (27, curses.KEY_ENTER, 10, 13):
                search_mode = False
            elif key in (curses.KEY_BACKSPACE, 127, 8):
                search_str = search_str[:-1]
            elif 32 <= key <= 126:
                search_str += chr(key)
                cursor = 0
                scroll = 0
            continue

        # Normal mode
        if key == curses.KEY_UP:
            cursor = max(0, cursor - 1)
        elif key == curses.KEY_DOWN:
            cursor = min(max(0, len(visible) - 1), cursor + 1)
        elif key == curses.KEY_PPAGE:
            cursor = max(0, cursor - list_h)
        elif key == curses.KEY_NPAGE:
            cursor = min(max(0, len(visible) - 1), cursor + list_h)
        elif key == curses.KEY_HOME:
            cursor = 0
        elif key == curses.KEY_END:
            cursor = max(0, len(visible) - 1)

        elif key == ord(" ") and visible:
            visible[cursor]["enabled"] = not visible[cursor]["enabled"]

        elif key in (ord("i"), ord("I"), curses.KEY_ENTER, 10, 13) and visible:
            show_info_popup(stdscr, visible[cursor])

        elif key in (ord("f"), ord("F")):
            cycle = ["ALL", "HIGH", "MEDIUM", "LOW"]
            sev_filter = cycle[(cycle.index(sev_filter) + 1) % len(cycle)]
            cursor = 0
            scroll = 0

        elif key in (ord("/"),):
            search_mode = True
            search_str  = ""
            cursor = 0
            scroll = 0

        elif key in (ord("c"), ord("C")):
            # Clear search
            search_str = ""
            cursor = 0
            scroll = 0

        elif key in (ord("s"), ord("S")):
            n = save_vars(controls)
            if n:
                status_msg = f"Saved — {n} override(s) written to vars/main.yml"
            else:
                status_msg = "Saved — all controls set to defaults (vars/main.yml cleared)"

        elif key in (ord("q"), ord("Q"), 27):
            unsaved = sum(1 for c in controls if c["enabled"] != c["original"])
            if unsaved:
                # Confirm quit
                prompt = f" {unsaved} unsaved change(s). Quit without saving? (y/n) "
                stdscr.attron(curses.color_pair(C_SEARCH) | curses.A_BOLD)
                stdscr.addstr(rows - 2, 0, prompt[:cols - 1].ljust(cols - 1))
                stdscr.attroff(curses.color_pair(C_SEARCH) | curses.A_BOLD)
                stdscr.refresh()
                confirm = stdscr.getch()
                if confirm in (ord("y"), ord("Y")):
                    break
            else:
                break


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    if not DEFAULTS_FILE.exists():
        print(f"ERROR: Cannot find defaults file:\n  {DEFAULTS_FILE}", file=sys.stderr)
        sys.exit(1)

    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        pass

    print("customize.py exited.")
