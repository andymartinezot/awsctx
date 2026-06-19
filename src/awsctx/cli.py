"""CLI entry point for awsctx."""

import os
import random
import sys
from pathlib import Path
from typing import Optional

from .config import (
    get_current_profile,
    get_previous_profile,
    get_profile_info,
    get_profile_sso_info,
    list_profile_names,
    resolve_region,
    set_previous_profile,
    set_profile_default_region,
)
from .picker import format_expiration, fuzzy_match, pick_profile
from .shell import get_shell_hook


BOLD = "\033[1m"
RESET = "\033[0m"
GREEN = "\033[32m"
CYAN = "\033[36m"
DIM = "\033[2m"

EMOJIS = [
    "🚀", "⚡", "🎯", "🔥", "✨", "🌟", "💫", "🎉",
    "🦄", "🐉", "🦅", "🐙", "🦊", "🐺", "🦁", "🐯",
    "🌈", "☁️", "🌊", "🏔️", "🌋", "🏝️", "🪐", "🌙",
    "🎸", "🎮", "🏄", "🛸", "🤖", "👾", "🧙", "🥷",
    "💎", "🔮", "⚔️", "🛡️", "🏹", "🪄", "🧊", "🔑",
]


def random_emoji() -> str:
    return random.choice(EMOJIS)


def format_switch_output(profile: str, region: str) -> str:
    account, _, expiration = get_profile_info(profile)
    exp_str = format_expiration(expiration)
    emoji = random_emoji()
    sso_info = get_profile_sso_info(profile)
    role = sso_info.get("sso_role_name", "n/a") if sso_info else "n/a"
    return (
        f"{emoji} Switched to: {BOLD}{profile}{RESET}\n"
        f"   Account:  {account}\n"
        f"   Role:     {role}\n"
        f"   Region:   {region}\n"
        f"   Session:  {exp_str}"
    )


def print_status():
    current = get_current_profile()
    profiles = list_profile_names()

    if not profiles:
        print("No profiles found in ~/.aws/config", file=sys.stderr)
        sys.exit(1)

    print(f"\n{BOLD}AWS Profiles:{RESET}\n", file=sys.stderr)
    for profile in profiles:
        marker = f"{GREEN}*{RESET}" if profile == current else " "
        account, _, expiration = get_profile_info(profile)
        region = resolve_region(profile)
        exp_str = format_expiration(expiration)
        print(
            f"  {marker} {BOLD}{profile}{RESET}  "
            f"{DIM}({account} | {region}){RESET}  "
            f"[{exp_str}{DIM}]{RESET}",
            file=sys.stderr,
        )
    print(file=sys.stderr)


def print_current():
    current = get_current_profile()
    if current:
        account, _, expiration = get_profile_info(current)
        region = resolve_region(current)
        exp_str = format_expiration(expiration)
        sso_info = get_profile_sso_info(current)
        role = sso_info.get("sso_role_name", "n/a") if sso_info else "n/a"
        print(
            f"{BOLD}{current}{RESET}\n"
            f"   Account:  {account}\n"
            f"   Role:     {role}\n"
            f"   Region:   {region}\n"
            f"   Session:  {exp_str}",
            file=sys.stderr,
        )
    else:
        print("No active profile (AWS_PROFILE is not set)", file=sys.stderr)


def print_usage():
    print(f"""{BOLD}awsctx{RESET} - Interactive AWS profile switcher

{BOLD}Usage:{RESET}
  awsctx                       Interactive profile picker
  awsctx <name>                Switch to profile (fuzzy match)
  awsctx <name> -r <region>    Switch with region override
  awsctx -                     Switch to previous profile
  awsctx --set-region <region> Set default region for current profile
  awsctx --setup               Auto-add shell hook to your shell config
  awsctx --list                List all profiles with status
  awsctx --current             Show current profile
  awsctx --init <shell>        Print shell hook (zsh, bash, fish)
  awsctx --help                Show this help

{BOLD}Region priority:{RESET}
  1. -r / --region flag (per-switch override)
  2. Per-profile default (set with --set-region)
  3. ~/.aws/config region for the profile
  4. Fallback: us-east-1

{BOLD}Source:{RESET}
  Reads profiles from ~/.aws/config ([profile X] sections)
  Checks SSO session status from ~/.aws/sso/cache/
""", file=sys.stderr)


SHELL_RC_MAP = {
    "zsh": Path.home() / ".zshrc",
    "bash": Path.home() / ".bashrc",
    "fish": Path.home() / ".config" / "fish" / "config.fish",
}

HOOK_MARKER = "awsctx --init"


def detect_shell() -> str:
    shell = os.environ.get("SHELL", "")
    if "zsh" in shell:
        return "zsh"
    elif "fish" in shell:
        return "fish"
    return "bash"


def setup_shell_hook():
    shell = detect_shell()
    rc_file = SHELL_RC_MAP[shell]

    if rc_file.exists():
        content = rc_file.read_text()
        if HOOK_MARKER in content:
            print(f"{GREEN}✓{RESET} Shell hook already present in {rc_file}", file=sys.stderr)
            return

    if shell == "fish":
        hook_line = "awsctx --init fish | source"
    else:
        hook_line = f'eval "$(awsctx --init {shell})"'

    with open(rc_file, "a") as f:
        f.write(f"\n# awsctx - AWS profile switcher\n{hook_line}\n")

    print(f"{GREEN}✓{RESET} Added shell hook to {BOLD}{rc_file}{RESET}", file=sys.stderr)
    print(f"  Run {CYAN}source {rc_file}{RESET} or open a new terminal to activate.", file=sys.stderr)


def select_profile(query: Optional[str] = None) -> Optional[str]:
    profiles = list_profile_names()

    if not profiles:
        print("No profiles found in ~/.aws/config", file=sys.stderr)
        sys.exit(1)

    if query:
        match = fuzzy_match(query, profiles)
        if match is None:
            print(f"No profile matching '{query}'", file=sys.stderr)
            sys.exit(1)
        return match

    return pick_profile(profiles)


def parse_region_flag(args: list) -> tuple:
    """Extract -r/--region flag from args. Returns (region, remaining_args)."""
    region = None
    remaining = []
    i = 0
    while i < len(args):
        if args[i] in ("-r", "--region") and i + 1 < len(args):
            region = args[i + 1]
            i += 2
        else:
            remaining.append(args[i])
            i += 1
    return region, remaining


def switch_to(profile: str, region_override: Optional[str] = None):
    current = get_current_profile()
    if current:
        set_previous_profile(current)
    region = resolve_region(profile, region_override)
    print(profile)
    print(region)
    print(format_switch_output(profile, region))
    sys.exit(0)


def main():
    args = sys.argv[1:]

    if not args:
        selected = select_profile()
        if selected:
            switch_to(selected)
        sys.exit(1)

    region_override, args = parse_region_flag(args)

    if not args:
        selected = select_profile()
        if selected:
            switch_to(selected, region_override)
        sys.exit(1)

    arg = args[0]

    if arg in ("--help", "-h"):
        print_usage()
        sys.exit(2)

    if arg in ("--list", "-l"):
        print_status()
        sys.exit(2)

    if arg in ("--current", "-c"):
        print_current()
        sys.exit(2)

    if arg == "--init":
        if len(args) < 2:
            print("Usage: awsctx --init <shell>", file=sys.stderr)
            print("Supported shells: zsh, bash, fish", file=sys.stderr)
            sys.exit(1)
        shell = args[1]
        print(get_shell_hook(shell))
        sys.exit(2)

    if arg == "--setup":
        setup_shell_hook()
        sys.exit(2)

    if arg == "--set-region":
        if len(args) < 2:
            print("Usage: awsctx --set-region <region>", file=sys.stderr)
            sys.exit(1)
        current = get_current_profile()
        if not current:
            print("No active profile. Switch to a profile first.", file=sys.stderr)
            sys.exit(1)
        set_profile_default_region(current, args[1])
        print(f"Default region for {BOLD}{current}{RESET} set to: {args[1]}", file=sys.stderr)
        sys.exit(2)

    if arg == "-":
        prev = get_previous_profile()
        if not prev:
            print("No previous profile", file=sys.stderr)
            sys.exit(1)
        switch_to(prev, region_override)

    selected = select_profile(query=arg)
    if selected:
        switch_to(selected, region_override)
    sys.exit(1)


if __name__ == "__main__":
    main()
