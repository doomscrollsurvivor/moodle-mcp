#!/usr/bin/env bash
# =============================================================================
# moodle-mcp — Universal MCP Install Script
# Configures moodle-mcp for Hermes Agent, Claude Code, and/or OpenCode.
#
# Usage:
#   bash scripts/install-mcp.sh                    # auto-detect all agents
#   bash scripts/install-mcp.sh --agent hermes     # Hermes only
#   bash scripts/install-mcp.sh --agent claude-code
#   bash scripts/install-mcp.sh --agent opencode
#   bash scripts/install-mcp.sh --profile akademik # Hermes profile (default: akademik)
#   bash scripts/install-mcp.sh --dry-run          # preview without writing
# =============================================================================

set -euo pipefail

# ── Colors ────────────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; CYAN='\033[0;36m'; BOLD='\033[1m'; RESET='\033[0m'

info()    { echo -e "${BLUE}ℹ${RESET}  $*"; }
success() { echo -e "${GREEN}✓${RESET}  $*"; }
warn()    { echo -e "${YELLOW}⚠${RESET}  $*"; }
error()   { echo -e "${RED}✗${RESET}  $*" >&2; }
step()    { echo -e "\n${BOLD}${CYAN}▶ $*${RESET}"; }
dry()     { echo -e "${YELLOW}[DRY-RUN]${RESET} $*"; }

# ── Defaults ──────────────────────────────────────────────────────────────────
AGENT=""          # empty = auto-detect all
HERMES_PROFILE="akademik"
DRY_RUN=false
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"

# ── Parse args ────────────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
  case "$1" in
    --agent)    AGENT="$2"; shift 2 ;;
    --profile)  HERMES_PROFILE="$2"; shift 2 ;;
    --dry-run)  DRY_RUN=true; shift ;;
    -h|--help)
      sed -n '2,12p' "$0" | sed 's/^# \?//'
      exit 0 ;;
    *) error "Unknown flag: $1"; exit 1 ;;
  esac
done

# ── Helpers ───────────────────────────────────────────────────────────────────
write_file() {
  local path="$1"; local content="$2"
  if $DRY_RUN; then
    dry "Would write: $path"
    echo "---BEGIN---"
    echo "$content"
    echo "---END---"
  else
    mkdir -p "$(dirname "$path")"
    echo "$content" > "$path"
    success "Written: $path"
  fi
}

run_cmd() {
  if $DRY_RUN; then
    dry "Would run: $*"
  else
    "$@"
  fi
}

# Prompt user for a value, with a default
prompt() {
  local label="$1"; local default="$2"; local var_name="$3"
  read -rp "  ${label} [${default}]: " value
  value="${value:-$default}"
  eval "$var_name='$value'"
}

# Merge a key into a simple YAML block (key: value style, no nesting for env vars)
json_set() {
  # json_set FILE KEY VALUE — naive single-key JSON set without external deps
  local file="$1"; local key="$2"; local value="$3"
  python3 - "$file" "$key" "$value" <<'PY'
import sys, json
file, key, value = sys.argv[1], sys.argv[2], sys.argv[3]
try:
    data = json.loads(open(file).read())
except Exception:
    data = {}
# Support dotted key paths: a.b.c
keys = key.split('.')
d = data
for k in keys[:-1]:
    d = d.setdefault(k, {})
d[keys[-1]] = value
open(file, 'w').write(json.dumps(data, indent=2, ensure_ascii=False) + '\n')
PY
}

# ── Gather .env values ────────────────────────────────────────────────────────
gather_env() {
  step "Gathering Moodle credentials"
  echo ""

  # Try loading from existing .env in repo
  if [[ -f "$REPO_DIR/.env" ]]; then
    info "Found existing .env — loading defaults from it"
    set -a; source "$REPO_DIR/.env"; set +a
  fi

  MOODLE_URL="${MOODLE_URL:-}"
  MOODLE_TOKEN="${MOODLE_TOKEN:-}"
  MOODLE_MY_CLASS="${MOODLE_MY_CLASS:-}"
  OBSIDIAN_VAULT_PATH="${OBSIDIAN_VAULT_PATH:-$HOME/Obsidian Vault}"

  if [[ -z "$MOODLE_URL" ]]; then
    prompt "Moodle REST URL (e.g. https://learning.example.ac.id/webservice/rest/server.php)" \
      "https://learning.polibatam.ac.id/webservice/rest/server.php" MOODLE_URL
  else
    info "Using MOODLE_URL from .env: ${MOODLE_URL}"
  fi

  if [[ -z "$MOODLE_TOKEN" ]]; then
    read -rsp "  Moodle token (get from /user/managetoken.php): " MOODLE_TOKEN
    echo ""
    if [[ -z "$MOODLE_TOKEN" ]]; then
      error "MOODLE_TOKEN cannot be empty."
      exit 1
    fi
  else
    info "Using MOODLE_TOKEN from .env (redacted)"
  fi

  if [[ -z "$MOODLE_MY_CLASS" ]]; then
    prompt "Your class slot for assignment filtering (e.g. 'Pagi C', or leave blank)" "" MOODLE_MY_CLASS
  else
    info "Using MOODLE_MY_CLASS: ${MOODLE_MY_CLASS}"
  fi

  prompt "Obsidian Vault path" "$OBSIDIAN_VAULT_PATH" OBSIDIAN_VAULT_PATH
}

# ── Launcher script path ──────────────────────────────────────────────────────
get_launcher() {
  echo "$SCRIPT_DIR/moodle_mcp_local_launch.py"
}

ensure_launcher_exists() {
  local launcher
  launcher="$(get_launcher)"
  if [[ ! -f "$launcher" ]]; then
    error "Launcher not found: $launcher"
    error "Run this script from the moodle-mcp repo root."
    exit 1
  fi
}

# ─────────────────────────────────────────────────────────────────────────────
# AGENT: HERMES
# ─────────────────────────────────────────────────────────────────────────────
install_hermes() {
  step "Configuring Hermes Agent (profile: ${HERMES_PROFILE})"
  ensure_launcher_exists

  local launcher
  launcher="$(get_launcher)"

  # Determine config path
  local profile_dir
  if [[ "$HERMES_PROFILE" == "default" ]]; then
    profile_dir="$HOME/.hermes"
  else
    profile_dir="$HOME/.hermes/profiles/$HERMES_PROFILE"
  fi
  local config_file="$profile_dir/config.yaml"

  info "Config file: $config_file"

  if ! command -v hermes &>/dev/null; then
    warn "hermes command not found — skipping Hermes install"
    warn "Install Hermes first: https://hermes-agent.nousresearch.com/docs"
    return 1
  fi

  # Check if hermes profile create is needed
  if [[ ! -d "$profile_dir" ]] && [[ "$HERMES_PROFILE" != "default" ]]; then
    info "Profile '${HERMES_PROFILE}' does not exist — creating it"
    if ! $DRY_RUN; then
      hermes profile create "$HERMES_PROFILE" 2>/dev/null || true
    else
      dry "Would run: hermes profile create $HERMES_PROFILE"
    fi
  fi

  if $DRY_RUN; then
    dry "Would inject moodle MCP block into: $config_file"
    return 0
  fi

  mkdir -p "$profile_dir"

  # Use hermes config set if available, otherwise inject YAML block
  if hermes --profile "$HERMES_PROFILE" config set mcpServers.moodle.command python3 &>/dev/null 2>&1; then
    # hermes config set supports dotted keys
    local cmds=(
      "mcpServers.moodle.command=python3"
      "mcpServers.moodle.args[0]=$launcher"
      "mcpServers.moodle.env.MOODLE_URL=$MOODLE_URL"
      "mcpServers.moodle.env.MOODLE_TOKEN=$MOODLE_TOKEN"
      "mcpServers.moodle.env.OBSIDIAN_VAULT_PATH=$OBSIDIAN_VAULT_PATH"
    )
    [[ -n "$MOODLE_MY_CLASS" ]] && cmds+=("mcpServers.moodle.env.MOODLE_MY_CLASS=$MOODLE_MY_CLASS")
    for kv in "${cmds[@]}"; do
      hermes --profile "$HERMES_PROFILE" config set "${kv%%=*}" "${kv#*=}" 2>/dev/null
    done
  else
    # Fallback: inject YAML block if mcp section doesn't exist yet
    local mcp_block
    mcp_block=$(cat <<YAML

mcpServers:
  moodle:
    command: python3
    args:
      - $launcher
    env:
      MOODLE_URL: "$MOODLE_URL"
      MOODLE_TOKEN: "$MOODLE_TOKEN"
      OBSIDIAN_VAULT_PATH: "$OBSIDIAN_VAULT_PATH"
YAML
)
    [[ -n "$MOODLE_MY_CLASS" ]] && mcp_block+="
      MOODLE_MY_CLASS: \"$MOODLE_MY_CLASS\""

    if grep -q "mcpServers:" "$config_file" 2>/dev/null; then
      warn "mcpServers already present in $config_file"
      warn "Add manually under mcpServers: (see README)"
    else
      echo "$mcp_block" >> "$config_file"
      success "Injected moodle MCP block into $config_file"
    fi
  fi

  # Run verification
  info "Verifying Hermes MCP connection..."
  if hermes --profile "$HERMES_PROFILE" mcp test moodle 2>/dev/null | grep -q "Connected"; then
    success "Hermes: moodle MCP connected ✓"
  else
    warn "Hermes: could not verify — restart the gateway and try:"
    warn "  systemctl --user restart hermes-gateway-${HERMES_PROFILE}.service"
    warn "  hermes --profile $HERMES_PROFILE mcp test moodle"
  fi
}

# ─────────────────────────────────────────────────────────────────────────────
# AGENT: CLAUDE CODE
# ─────────────────────────────────────────────────────────────────────────────
install_claude_code() {
  step "Configuring Claude Code"
  ensure_launcher_exists

  if ! command -v claude &>/dev/null; then
    warn "claude command not found — skipping Claude Code install"
    warn "Install with: npm install -g @anthropic-ai/claude-code"
    return 1
  fi

  local launcher
  launcher="$(get_launcher)"
  local settings_dir="$HOME/.claude"
  local settings_file="$settings_dir/settings.json"

  mkdir -p "$settings_dir"
  [[ ! -f "$settings_file" ]] && echo '{}' > "$settings_file"

  if $DRY_RUN; then
    dry "Would add moodle-mcp to: $settings_file"
    dry "Using launcher: $launcher"
    return 0
  fi

  # Build the mcpServers block using python3 (no jq dependency)
  python3 - "$settings_file" "$launcher" "$MOODLE_URL" "$MOODLE_TOKEN" \
    "$MOODLE_MY_CLASS" "$OBSIDIAN_VAULT_PATH" <<'PY'
import sys, json
file, launcher, url, token, cls, vault = sys.argv[1:]
try:
    data = json.loads(open(file).read())
except Exception:
    data = {}
servers = data.setdefault("mcpServers", {})
env = {
    "MOODLE_URL": url,
    "MOODLE_TOKEN": token,
    "OBSIDIAN_VAULT_PATH": vault,
}
if cls:
    env["MOODLE_MY_CLASS"] = cls
servers["moodle-mcp"] = {
    "command": "python3",
    "args": [launcher],
    "env": env,
}
open(file, "w").write(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
print("OK")
PY

  success "Claude Code: moodle-mcp added to $settings_file"
  info "Verify with:  claude mcp list"
  info "In a session: ask 'list my Moodle courses'"
}

# ─────────────────────────────────────────────────────────────────────────────
# AGENT: OPENCODE
# ─────────────────────────────────────────────────────────────────────────────
install_opencode() {
  step "Configuring OpenCode"
  ensure_launcher_exists

  if ! command -v opencode &>/dev/null; then
    warn "opencode command not found — skipping OpenCode install"
    warn "Install with: npm i -g opencode-ai@latest"
    return 1
  fi

  local launcher
  launcher="$(get_launcher)"
  local config_dir="$HOME/.config/opencode"
  local config_file="$config_dir/config.json"

  mkdir -p "$config_dir"
  [[ ! -f "$config_file" ]] && echo '{}' > "$config_file"

  if $DRY_RUN; then
    dry "Would add moodle-mcp to: $config_file"
    dry "Using launcher: $launcher"
    return 0
  fi

  python3 - "$config_file" "$launcher" "$MOODLE_URL" "$MOODLE_TOKEN" \
    "$MOODLE_MY_CLASS" "$OBSIDIAN_VAULT_PATH" <<'PY'
import sys, json
file, launcher, url, token, cls, vault = sys.argv[1:]
try:
    data = json.loads(open(file).read())
except Exception:
    data = {}
mcps = data.setdefault("mcp", {})
env = {
    "MOODLE_URL": url,
    "MOODLE_TOKEN": token,
    "OBSIDIAN_VAULT_PATH": vault,
}
if cls:
    env["MOODLE_MY_CLASS"] = cls
mcps["moodle-mcp"] = {
    "command": "python3",
    "args": [launcher],
    "environment": env,
}
open(file, "w").write(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
print("OK")
PY

  success "OpenCode: moodle-mcp added to $config_file"
  info "Verify with:  opencode run 'list all my Moodle courses'"
}

# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────
main() {
  echo ""
  echo -e "${BOLD}╔══════════════════════════════════════╗${RESET}"
  echo -e "${BOLD}║     moodle-mcp  •  MCP Installer     ║${RESET}"
  echo -e "${BOLD}╚══════════════════════════════════════╝${RESET}"
  echo ""

  if $DRY_RUN; then
    warn "DRY-RUN mode — no files will be written"
    echo ""
  fi

  # Detect available agents if none specified
  if [[ -z "$AGENT" ]]; then
    info "Auto-detecting installed agents..."
    DETECTED=()
    command -v hermes    &>/dev/null && DETECTED+=("hermes")
    command -v claude    &>/dev/null && DETECTED+=("claude-code")
    command -v opencode  &>/dev/null && DETECTED+=("opencode")

    if [[ ${#DETECTED[@]} -eq 0 ]]; then
      error "No supported agents found (hermes, claude, opencode)."
      error "Install at least one and re-run."
      exit 1
    fi

    echo -e "  Detected: ${BOLD}${DETECTED[*]}${RESET}"
  else
    DETECTED=("$AGENT")
  fi

  # Gather credentials once
  gather_env

  # Install for each agent
  local any_fail=false
  for agent in "${DETECTED[@]}"; do
    case "$agent" in
      hermes)       install_hermes ;;
      claude-code|claude) install_claude_code ;;
      opencode)     install_opencode ;;
      *)
        error "Unknown agent: $agent (valid: hermes, claude-code, opencode)"
        any_fail=true ;;
    esac
  done

  echo ""
  echo -e "${BOLD}${GREEN}═══════════════════════════════════════${RESET}"
  echo -e "${BOLD}${GREEN}  Installation complete!${RESET}"
  echo -e "${BOLD}${GREEN}═══════════════════════════════════════${RESET}"
  echo ""
  echo -e "  ${BOLD}Quick test commands:${RESET}"

  command -v hermes   &>/dev/null && \
    echo "  hermes --profile $HERMES_PROFILE mcp test moodle"
  command -v claude   &>/dev/null && \
    echo "  claude mcp list"
  command -v opencode &>/dev/null && \
    echo "  opencode run 'list my Moodle courses'"
  echo ""

  $any_fail && exit 1 || exit 0
}

main
