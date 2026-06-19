"""Configuration and file path management for AWS SSO profiles."""

import hashlib
import json
import os
from configparser import ConfigParser
from pathlib import Path
from typing import Dict, List, Optional, Tuple


AWS_CONFIG = Path.home() / ".aws" / "config"
SSO_CACHE_DIR = Path.home() / ".aws" / "sso" / "cache"
STATE_DIR = Path.home() / ".config" / "awsctx"
STATE_FILE = STATE_DIR / "state.json"

DEFAULT_REGION = "us-east-1"


def ensure_state_dir():
    STATE_DIR.mkdir(parents=True, exist_ok=True)


def load_aws_config() -> ConfigParser:
    config = ConfigParser()
    if AWS_CONFIG.exists():
        config.read(AWS_CONFIG)
    return config


def load_profiles() -> Dict[str, dict]:
    """Load all profiles from ~/.aws/config. Returns {name: {key: value}}."""
    config = load_aws_config()
    profiles = {}
    for section in config.sections():
        if section == "default":
            profiles["default"] = dict(config.items(section))
        elif section.startswith("profile "):
            name = section[len("profile "):]
            profiles[name] = dict(config.items(section))
    return profiles


def list_profile_names() -> List[str]:
    return sorted(load_profiles().keys())


def get_profile_region(profile: str) -> str:
    profiles = load_profiles()
    data = profiles.get(profile, {})
    return data.get("region", DEFAULT_REGION)


def get_profile_sso_info(profile: str) -> Optional[Dict[str, str]]:
    """Get SSO-related fields for a profile."""
    profiles = load_profiles()
    data = profiles.get(profile, {})
    sso_start_url = data.get("sso_start_url")
    sso_session = data.get("sso_session")
    if sso_start_url or sso_session:
        return {
            "sso_start_url": sso_start_url or "",
            "sso_region": data.get("sso_region", ""),
            "sso_account_id": data.get("sso_account_id", ""),
            "sso_role_name": data.get("sso_role_name", ""),
            "sso_session": sso_session or "",
        }
    return None


def _get_sso_cache_file(profile: str) -> Optional[Path]:
    """Find the SSO cache file for a profile."""
    if not SSO_CACHE_DIR.exists():
        return None

    profiles = load_profiles()
    data = profiles.get(profile, {})

    sso_session = data.get("sso_session")
    if sso_session:
        cache_key = sso_session
    else:
        cache_key = data.get("sso_start_url")

    if not cache_key:
        return None

    sha = hashlib.sha1(cache_key.encode("utf-8")).hexdigest()
    cache_file = SSO_CACHE_DIR / f"{sha}.json"
    if cache_file.exists():
        return cache_file
    return None


def get_sso_session_expiration(profile: str) -> Optional[str]:
    """Get the expiresAt value from SSO cache for a profile."""
    cache_file = _get_sso_cache_file(profile)
    if not cache_file:
        return None
    try:
        with open(cache_file) as f:
            data = json.load(f)
        return data.get("expiresAt")
    except (json.JSONDecodeError, OSError):
        return None


def get_current_profile() -> Optional[str]:
    return os.environ.get("AWS_PROFILE")


def load_state() -> dict:
    ensure_state_dir()
    if STATE_FILE.exists():
        with open(STATE_FILE) as f:
            return json.load(f)
    return {}


def save_state(state: dict):
    ensure_state_dir()
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)


def get_previous_profile() -> Optional[str]:
    state = load_state()
    return state.get("previous_profile")


def set_previous_profile(profile: str):
    state = load_state()
    state["previous_profile"] = profile
    save_state(state)


def get_profile_default_region(profile: str) -> Optional[str]:
    state = load_state()
    regions = state.get("profile_regions", {})
    return regions.get(profile)


def set_profile_default_region(profile: str, region: str):
    state = load_state()
    if "profile_regions" not in state:
        state["profile_regions"] = {}
    state["profile_regions"][profile] = region
    save_state(state)


def resolve_region(profile: str, override: Optional[str] = None) -> str:
    if override:
        return override
    custom = get_profile_default_region(profile)
    if custom:
        return custom
    return get_profile_region(profile)


def get_profile_info(profile: str) -> Tuple[str, str, Optional[str]]:
    """Returns (account_id, region, sso_expires_at)."""
    profiles = load_profiles()
    data = profiles.get(profile, {})
    account = data.get("sso_account_id", "n/a")
    region = get_profile_region(profile)
    expiration = get_sso_session_expiration(profile)
    return account, region, expiration
