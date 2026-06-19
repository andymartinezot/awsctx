"""Interactive profile picker with built-in TUI (no external deps)."""

import subprocess
import sys
from datetime import datetime, timezone
from typing import List, Optional

from .config import get_current_profile, get_sso_session_expiration


RESET = "\033[0m"
BOLD = "\033[1m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"
CYAN = "\033[36m"
DIM = "\033[2m"


def format_expiration(expires_at: Optional[str]) -> str:
    if expires_at is None:
        return f"{DIM}no session{RESET}"
    try:
        exp_time = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        remaining = (exp_time - now).total_seconds()
    except (ValueError, TypeError):
        return f"{DIM}unknown{RESET}"

    if remaining <= 0:
        return f"{RED}expired{RESET}"
    hours = int(remaining) // 3600
    minutes = (int(remaining) % 3600) // 60
    if hours > 2:
        return f"{GREEN}{hours}h {minutes}m remaining{RESET}"
    elif hours >= 1:
        return f"{YELLOW}{hours}h {minutes}m remaining{RESET}"
    else:
        return f"{RED}{minutes}m remaining{RESET}"


def fuzzy_match(query: str, profiles: List[str]) -> Optional[str]:
    query_lower = query.lower()
    for profile in profiles:
        if query_lower in profile.lower():
            return profile
    return None


def pick_profile_fzf(profiles: List[str]) -> Optional[str]:
    """Try to use fzf if available, return None if not."""
    import shutil

    if not shutil.which("fzf"):
        return None

    current = get_current_profile()
    lines = []
    for p in profiles:
        marker = "* " if p == current else "  "
        exp = get_sso_session_expiration(p)
        exp_str = format_expiration(exp)
        for code in ("\033[2m", "\033[32m", "\033[33m", "\033[31m", "\033[0m"):
            exp_str = exp_str.replace(code, "")
        lines.append(f"{marker}{p}\t{exp_str}")

    input_text = "\n".join(lines)
    try:
        proc = subprocess.Popen(
            ["fzf", "--ansi", "--prompt=AWS Profile> ", "--height=~50%", "--reverse"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=sys.stderr,
            text=True,
        )
        selected, _ = proc.communicate(input=input_text)
        if proc.returncode != 0:
            return None
        name = selected.strip().lstrip("* ").split("\t")[0].strip()
        return name
    except (subprocess.SubprocessError, OSError):
        return None


def pick_profile_builtin(profiles: List[str]) -> Optional[str]:
    """Built-in interactive picker (no deps required)."""
    current = get_current_profile()

    print(f"\n{BOLD}AWS Profiles:{RESET}\n", file=sys.stderr)
    for i, profile in enumerate(profiles, 1):
        marker = f"{GREEN}*{RESET}" if profile == current else " "
        exp = get_sso_session_expiration(profile)
        exp_str = format_expiration(exp)
        print(f"  {marker} {BOLD}{i}){RESET} {profile}  {DIM}[{exp_str}{DIM}]{RESET}", file=sys.stderr)

    print(file=sys.stderr)
    try:
        tty = open("/dev/tty", "r")
        sys.stderr.write(f"{CYAN}Select profile (number or name): {RESET}")
        sys.stderr.flush()
        choice = tty.readline().strip()
        tty.close()
    except (KeyboardInterrupt, EOFError, OSError):
        return None

    if not choice:
        return None

    if choice.isdigit():
        idx = int(choice) - 1
        if 0 <= idx < len(profiles):
            return profiles[idx]
        return None

    return fuzzy_match(choice, profiles)


def pick_profile(profiles: List[str]) -> Optional[str]:
    """Pick a profile using fzf (preferred) or built-in picker."""
    result = pick_profile_fzf(profiles)
    if result is not None:
        return result
    return pick_profile_builtin(profiles)
