# Toggle Wars Agent

**WeMakeDevs Flagsmith Experimentation Hackathon — Track 02**

An AI agent that accepts a natural language deployment prompt, creates a Flagsmith feature flag via the REST API, sets a rollout target, waits for human approval, then pushes the flag to 100%.

---

## Agent Flow

1. **Parse** — extracts flag name and rollout % from a plain-English prompt
2. **Create** — creates the feature flag in Flagsmith via the management API
3. **Report** — displays flag status and rollout target
4. **Human approval** — waits for operator to type `approve` or `reject`
5. **Ship** — on approval, confirms the flag is pushed to 100% rollout

---

## Example

```bash
python toggle_wars_agent.py "Ship checkout_v2 safely to 10% of users"
```

**Output:**
```
[14:39:43] Parsed → flag: 'checkout_v2', rollout: 10%
[14:39:43] Checking current flags in environment...
[14:39:43] Existing flags: []
[14:39:43] Creating feature flag 'checkout_v2'...
[14:39:45] ✓ Flag created: id=304883, name=checkout_v2

📋 Flag Status:
   Name:    checkout_v2
   Enabled: False (pending rollout)
   Rollout: 10% (target)
   Project: toggle-wars-agent (ID: 56405)

HUMAN APPROVAL REQUIRED
Flag 'checkout_v2' is ready to ship.
Current rollout target: 10%

Type 'approve' to push to 100%, or 'reject' to cancel: approve

[14:40:15] ✓ Approved! Pushing 'checkout_v2' to 100% rollout...
[14:40:15] ✓ 'checkout_v2' is now live at 100%.
🚀 Flag shipped successfully!
```

---

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure environment

Create a `.env` file in the project directory:

```
FLAGSMITH_API_KEY=your_client_side_environment_key
FLAGSMITH_MGMT_TOKEN=your_user_api_token
```

- **FLAGSMITH_API_KEY** — Client-side environment key from Flagsmith → Environment → SDK Keys
- **FLAGSMITH_MGMT_TOKEN** — User API token from Flagsmith → Account → API Keys

### 3. Run the agent

```bash
python toggle_wars_agent.py "Ship dark_mode to 25% of users"
python toggle_wars_agent.py "Enable new_onboarding flag at 50%"
python toggle_wars_agent.py "Deploy checkout_v2 safely to 10% of users"
```

---

## How It Works

The agent uses two separate Flagsmith API mechanisms:

| Operation | API | Auth |
|---|---|---|
| List current flags | Edge API (`edge.api.flagsmith.com`) | `X-Environment-Key` header |
| Create feature flags | Management API (`api.flagsmith.com`) | `Authorization: Token` header |

The NLP parser uses regex to extract snake_case flag names and percentage values from free-form prompts. It skips common verbs (`ship`, `enable`, `deploy`, etc.) to isolate the flag name.

---

## Built With

- [Flagsmith](https://flagsmith.com) — Feature flag platform
- Python `requests` — API calls
- `python-dotenv` — Environment variable management

---

Built by [Ramon Cortez](https://linkedin.com/in/ramon-cortez-a227a2112) — AI Architect
