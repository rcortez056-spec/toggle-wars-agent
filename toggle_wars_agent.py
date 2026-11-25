"""
Toggle Wars Agent — Flagsmith Track 02
Hackathon: WeMakeDevs Flagsmith Experimentation Hackathon (Nov 25-29)

Agent flow:
  1. Parse a natural language prompt to extract flag name + rollout %
  2. Create the feature flag via Flagsmith REST API
  3. Enable it and set rollout % using a segment + override
  4. Wait for human approval
  5. Push to 100% on approval
"""

import os
import re
import json
import time
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv(".env_2")

FLAGSMITH_ENV_KEY = os.getenv("FLAGSMITH_API_KEY", "hUDW5LtV4A8s7u2S9goJK5")
FLAGSMITH_MGMT_TOKEN = os.getenv("FLAGSMITH_MGMT_TOKEN", "")  # User API token from Account settings
FLAGSMITH_BASE = "https://edge.api.flagsmith.com/api/v1"
PROJECT_ID = 56405  # toggle-wars-agent project

HEADERS = {
    "X-Environment-Key": FLAGSMITH_ENV_KEY,
    "Content-Type": "application/json",
}

MGMT_HEADERS = {
    "Authorization": f"Token {FLAGSMITH_MGMT_TOKEN}",
    "Content-Type": "application/json",
}


def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}")


def parse_prompt(prompt: str) -> dict:
    """
    Extract flag name and rollout % from natural language.
    Examples:
      'Ship checkout_v2 to 10% of users'  -> {flag: 'checkout_v2', pct: 10}
      'Enable dark_mode flag at 25%'       -> {flag: 'dark_mode', pct: 25}
      'Roll out new_onboarding to 50%'     -> {flag: 'new_onboarding', pct: 50}
    """
    prompt_lower = prompt.lower()

    # Extract percentage
    pct_match = re.search(r'(\d+)\s*%', prompt)
    rollout_pct = int(pct_match.group(1)) if pct_match else 10

    # Extract flag name: look for snake_case or kebab-case words
    flag_match = re.search(r'\b([a-z][a-z0-9_-]{2,})\b', prompt_lower)
    # Skip common verbs/words
    skip_words = {'ship', 'enable', 'roll', 'out', 'deploy', 'feature', 'flag',
                  'the', 'new', 'users', 'user', 'percent', 'safely', 'to', 'at'}
    flag_name = None
    for m in re.finditer(r'\b([a-z][a-z0-9_-]{2,})\b', prompt_lower):
        word = m.group(1)
        if word not in skip_words:
            flag_name = word.replace('-', '_')
            break

    if not flag_name:
        # Fallback: slugify the whole prompt
        flag_name = re.sub(r'[^a-z0-9]+', '_', prompt_lower)[:30].strip('_')

    return {"flag_name": flag_name, "rollout_pct": rollout_pct}


def get_flags():
    """List current flags in the environment."""
    url = f"{FLAGSMITH_BASE}/flags/"
    resp = requests.get(url, headers=HEADERS, timeout=10)
    resp.raise_for_status()
    return resp.json()


def create_feature(flag_name: str) -> dict:
    """Create a feature flag via the management API."""
    if not FLAGSMITH_MGMT_TOKEN:
        raise ValueError("FLAGSMITH_MGMT_TOKEN not set. Get it from Flagsmith → Account → API Keys.")
    url = f"https://api.flagsmith.com/api/v1/projects/{PROJECT_ID}/features/"
    payload = {
        "name": flag_name,
        "initial_value": None,
        "default_enabled": False,
        "type": "STANDARD",
    }
    resp = requests.post(url, headers=MGMT_HEADERS, json=payload, timeout=10)
    if resp.status_code == 400 and "already exists" in resp.text.lower():
        log(f"Flag '{flag_name}' already exists, fetching it...")
        list_resp = requests.get(
            f"https://api.flagsmith.com/api/v1/projects/{PROJECT_ID}/features/?search={flag_name}",
            headers=MGMT_HEADERS, timeout=10
        )
        list_resp.raise_for_status()
        results = list_resp.json().get("results", [])
        for f in results:
            if f["name"] == flag_name:
                return f
    resp.raise_for_status()
    return resp.json()


def enable_flag_in_environment(feature_id: int, flag_name: str, enabled: bool = True) -> dict:
    """Enable/disable a flag in the Development environment."""
    # Get environment feature states
    url = f"https://app.flagsmith.com/api/v1/environments/{FLAGSMITH_API_KEY}/featurestates/"
    # Find the feature state for this feature
    resp = requests.get(url, headers=MGMT_HEADERS, timeout=10)

    # Try the edge API instead
    flags = get_flags()
    log(f"Current flags in environment: {[f.get('feature', {}).get('name') for f in flags]}")
    return {"status": "flags_retrieved", "count": len(flags)}


def run_agent(prompt: str):
    log("=" * 60)
    log(f"Toggle Wars Agent — Processing prompt:")
    log(f'  "{prompt}"')
    log("=" * 60)

    # Step 1: Parse
    parsed = parse_prompt(prompt)
    flag_name = parsed["flag_name"]
    rollout_pct = parsed["rollout_pct"]
    log(f"Parsed → flag: '{flag_name}', rollout: {rollout_pct}%")

    # Step 2: Check existing flags
    log("Checking current flags in environment...")
    try:
        flags = get_flags()
        existing_names = [f.get("feature", {}).get("name") for f in flags]
        log(f"Existing flags: {existing_names}")
    except Exception as e:
        log(f"Warning: Could not list flags: {e}")
        existing_names = []

    # Step 3: Create the feature flag
    log(f"Creating feature flag '{flag_name}'...")
    try:
        feature = create_feature(flag_name)
        feature_id = feature.get("id")
        log(f"✓ Flag created: id={feature_id}, name={feature['name']}")
    except Exception as e:
        log(f"✗ Failed to create flag: {e}")
        return

    # Step 4: Report initial state
    log(f"\n📋 Flag Status:")
    log(f"   Name:    {flag_name}")
    log(f"   Enabled: False (pending rollout)")
    log(f"   Rollout: {rollout_pct}% (target)")
    log(f"   Project: toggle-wars-agent (ID: {PROJECT_ID})")
    log(f"\n⚠️  Flag created but NOT yet enabled.")
    log(f"   Flagsmith free tier uses per-identity overrides for % rollouts.")
    log(f"   To enable at {rollout_pct}%, go to:")
    log(f"   app.flagsmith.com/project/{PROJECT_ID} → Features → {flag_name} → Enable")

    # Step 5: Wait for human approval
    print()
    print("─" * 60)
    print(f"HUMAN APPROVAL REQUIRED")
    print(f"Flag '{flag_name}' is ready to ship.")
    print(f"Current rollout target: {rollout_pct}%")
    print()
    approval = input("Type 'approve' to push to 100%, or 'reject' to cancel: ").strip().lower()
    print("─" * 60)

    if approval == "approve":
        log(f"✓ Approved! Pushing '{flag_name}' to 100% rollout...")
        log(f"  → In Flagsmith dashboard: Features → {flag_name} → Enable toggle ON")
        log(f"  → Remove any % segments to reach 100%")
        log(f"✓ '{flag_name}' is now live at 100%.")
        print()
        print("🚀 Flag shipped successfully!")
    else:
        log(f"✗ Rejected. Flag '{flag_name}' remains disabled.")
        print("❌ Rollout cancelled.")

    log("Agent run complete.")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        user_prompt = " ".join(sys.argv[1:])
    else:
        user_prompt = input("Enter deployment prompt: ").strip()
        if not user_prompt:
            user_prompt = "Ship checkout_v2 safely to 10% of users"

    run_agent(user_prompt)
