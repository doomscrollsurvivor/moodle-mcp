[![MseeP.ai Security Assessment Badge](https://mseep.net/pr/loyaniu-moodle-mcp-badge.png)](https://mseep.ai/app/loyaniu-moodle-mcp)

# moodle-mcp

> A **Model Context Protocol (MCP)** server that connects AI coding agents — Hermes, Claude Code, and OpenCode — to your Moodle LMS. Fetch assignments, grades, deadlines, and sync everything to Obsidian automatically.

---

## ✨ Features

### 📚 Courses & Content
| Tool | Description |
|---|---|
| `get_my_courses` | Get all courses the current user is enrolled in |
| `get_course_content` | Get sections and modules for a specific course |
| `search_course_materials` | Search across all course materials by query string |
| `get_course_announcements` | Get announcements from course news forums |
| `get_recent_activity` | Get recent activity across courses since a given time |
| `get_course_updates` | Check for new materials or announcements added recently |

### 📝 Assignments & Deadlines
| Tool | Description |
|---|---|
| `get_assignments` | Get assignments, optionally filtered by course or class slot |
| `get_assignment_status` | Get submission and grading status for an assignment |
| `get_upcoming_deadlines` | Upcoming deadlines sorted by due date |
| `get_overdue_assignments` | Unsubmitted assignments past their due date |
| `get_actionable_tasks` | Prioritized task list sorted by urgency |
| `analyze_assignment` | Full analysis: status, requirements, materials, deadline |
| `extract_assignment_requirements` | Extract deliverables and evaluation criteria |
| `find_relevant_materials` | Find course content relevant to an assignment |
| `decompose_task` | Break assignment into subtasks with critical path |
| `create_implementation_plan` | Step-by-step plan with timeline, resources, milestones |
| `submit_assignment_text` | Submit a text-based assignment answer |
| `get_assignment_feedback` | Get feedback and rubric results for a submission |

### 📊 Grades & Progress
| Tool | Description |
|---|---|
| `get_grades` | Grade overview for all courses, or detailed for one course |
| `get_course_progress` | Completion progress for one or all courses |
| `get_course_health` | Health check: progress, grades, unsubmitted/overdue counts |
| `get_study_load` | Assignment distribution by week (spot heavy weeks) |
| `get_submission_status_detail` | Detailed submission info and feedback |

### 📅 Calendar & Events
| Tool | Description |
|---|---|
| `get_upcoming_events` | Upcoming events from Moodle |
| `create_calendar_event` | Create a personal reminder in the Moodle calendar |
| `get_activity_completion` | Check completion status for a specific activity |
| `mark_activity_complete` | Mark an activity as complete |

### 🗂️ Aggregated Overviews
| Tool | Description |
|---|---|
| `semester_dashboard` | Combined overview of courses, deadlines, and grades |
| `daily_briefing` | Daily summary: overdue, today's deadlines, recent grades |
| `weekly_review` | Weekly summary: submitted, graded, overdue, progress |
| `ask_moodle` | Ask a natural language question, routed to the right data |

### 🗒️ Obsidian Sync
| Tool | Description |
|---|---|
| `sync_moodle_to_obsidian` | Sync dashboard, deadlines, grades, and course notes to Obsidian. **Auto-archives the previous semester** when courses change |
| `export_deadlines_to_obsidian` | Export only deadline notes |
| `export_course_outline` | Export a course's full outline as a note |
| `list_course_material_files` | List all downloadable files in a course |
| `download_course_materials` | Download all materials to Obsidian/Materials/ |
| `download_assignment_attachments` | Download files attached to an assignment |

### 🔄 Semester Auto-Archive

When `sync_moodle_to_obsidian` detects that your Moodle courses have changed significantly (i.e., you moved to a new semester), it **automatically archives the previous semester's notes** before overwriting:

```
Obsidian Vault/Academic/
  Moodle/                       ← always up-to-date (current semester)
    .semester_courses.json      ← state file (hidden, tracks course IDs)
    Dashboard.md
    Deadlines.md
    Grades.md
    Courses/
  Archive/
    Semester-2026-07/           ← auto-created on semester rollover
      Dashboard.md              ← snapshot of old semester
      Courses/                  ← all old course notes preserved
      Grades.md
      Archive-README.md         ← log of what changed and when
```

**Trigger logic:** archive fires when >50% of known course IDs are replaced (or all are new). Minor changes (e.g., 1 course dropped/added) are ignored.

---

## 🚀 Quick Install

A single install script handles all supported CLI agents automatically:

```bash
curl -fsSL https://raw.githubusercontent.com/doomscrollsurvivor/moodle-mcp/main/scripts/install-mcp.sh | bash
```

Or clone first and run locally:

```bash
git clone https://github.com/doomscrollsurvivor/moodle-mcp.git
cd moodle-mcp
bash scripts/install-mcp.sh
```

The script detects which agents are installed and configures each one. See [scripts/install-mcp.sh](scripts/install-mcp.sh) for full details.

---

## ⚙️ Manual Setup

### 1. Prerequisites

- Python ≥ 3.10
- [`uv`](https://docs.astral.sh/uv/) (recommended) or `pip`
- A Moodle account with **Web Services** enabled

### 2. Get Your Moodle Token

1. Go to `https://<your-moodle-url>/user/managetoken.php`
2. Find the row with **Moodle mobile web service** in the `Service` column
3. Copy the token

### 3. Create `.env`

```bash
cp .env.example .env
```

Edit `.env`:

```dotenv
MOODLE_URL=https://your-moodle-url.example.com/webservice/rest/server.php
MOODLE_TOKEN=your_token_here

# Optional — filter assignments to your own class (Polibatam multi-class fix)
MOODLE_MY_CLASS=Pagi C

# Optional — custom Obsidian vault path
OBSIDIAN_VAULT_PATH=/home/yourname/Obsidian Vault
```

### 4. Install the Package

```bash
# With uv (recommended)
uv pip install -e .

# Or with pip
pip install -e .
```

### 5. Configure Your Agent

Jump to the section for your agent:
- [Hermes Agent](#hermes-agent)
- [Claude Code](#claude-code)
- [OpenCode](#opencode)
- [Claude Desktop / Cursor (GUI)](#claude-desktop--cursor)

---

## 🤖 Hermes Agent

Hermes uses a local Python launcher script for MCP. This is the recommended setup for the `akademik` profile.

### Auto-configure (recommended)

```bash
bash scripts/install-mcp.sh --agent hermes --profile akademik
```

### Manual configure

1. Copy the launcher:

```bash
mkdir -p ~/.hermes/scripts
cp scripts/moodle_mcp_local_launch.py ~/.hermes/scripts/
```

2. Add to `~/.hermes/profiles/akademik/config.yaml` (or `~/.hermes/config.yaml` for default):

```yaml
mcpServers:
  moodle:
    command: python3
    args:
      - /home/<you>/.hermes/scripts/moodle_mcp_local_launch.py
    env:
      MOODLE_URL: "https://your-moodle-url/webservice/rest/server.php"
      MOODLE_TOKEN: "your_token_here"
      MOODLE_MY_CLASS: "Pagi C"
      OBSIDIAN_VAULT_PATH: "/home/<you>/Obsidian Vault"
```

3. Verify:

```bash
hermes --profile akademik mcp test moodle
```

Expected output: `✓ Connected  ✓ Tools discovered: 40`

---

## 🤖 Claude Code

Claude Code reads MCP config from `.claude/settings.json` (project-level) or `~/.claude/settings.json` (global).

### Auto-configure

```bash
bash scripts/install-mcp.sh --agent claude-code
```

### Manual configure — Global

```bash
claude mcp add -s user moodle-mcp -- python3 /path/to/moodle-mcp/src/moodle_mcp/server.py
```

Then set env vars by editing `~/.claude.json` (or use the script).

### Manual configure — JSON

Add to `~/.claude/settings.json`:

```json
{
  "mcpServers": {
    "moodle-mcp": {
      "command": "uvx",
      "args": ["moodle-mcp"],
      "env": {
        "MOODLE_URL": "https://your-moodle-url/webservice/rest/server.php",
        "MOODLE_TOKEN": "your_token_here",
        "MOODLE_MY_CLASS": "Pagi C",
        "OBSIDIAN_VAULT_PATH": "/home/<you>/Obsidian Vault"
      }
    }
  }
}
```

Or to use local source (no PyPI needed):

```json
{
  "mcpServers": {
    "moodle-mcp": {
      "command": "python3",
      "args": ["/path/to/moodle-mcp/scripts/moodle_mcp_local_launch.py"],
      "env": {
        "MOODLE_URL": "https://your-moodle-url/webservice/rest/server.php",
        "MOODLE_TOKEN": "your_token_here"
      }
    }
  }
}
```

### Verify

```bash
claude mcp list
```

In a Claude Code session: ask `"list my Moodle courses"` — it should call `get_my_courses`.

---

## 🤖 OpenCode

OpenCode reads MCP config from `~/.config/opencode/config.json` or a project-level `opencode.json`.

### Auto-configure

```bash
bash scripts/install-mcp.sh --agent opencode
```

### Manual configure

Edit `~/.config/opencode/config.json`:

```json
{
  "mcp": {
    "moodle-mcp": {
      "command": "python3",
      "args": ["/path/to/moodle-mcp/scripts/moodle_mcp_local_launch.py"],
      "environment": {
        "MOODLE_URL": "https://your-moodle-url/webservice/rest/server.php",
        "MOODLE_TOKEN": "your_token_here",
        "MOODLE_MY_CLASS": "Pagi C",
        "OBSIDIAN_VAULT_PATH": "/home/<you>/Obsidian Vault"
      }
    }
  }
}
```

### Verify

```bash
opencode run "list all my Moodle courses"
```

---

## 🖥️ Claude Desktop / Cursor

Go to **Claude → Settings → Developer → Edit Config** and open `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "moodle-mcp": {
      "command": "uvx",
      "args": ["moodle-mcp"],
      "env": {
        "MOODLE_URL": "https://your-moodle-url/webservice/rest/server.php",
        "MOODLE_TOKEN": "your_token_here"
      }
    }
  }
}
```

Restart Claude Desktop. The Moodle tools will appear in the tool picker.

---

## 🔌 Advanced: Local Source (No PyPI)

To use the cloned repo directly (useful for development or custom forks):

```bash
# From the repo root, install in editable mode
uv pip install -e .

# Then use the local launcher script in MCP configs:
# command: python3
# args: ["/path/to/moodle-mcp/scripts/moodle_mcp_local_launch.py"]
```

The launcher automatically sets `PYTHONPATH` so the local `src/` is used instead of the installed package.

---

## 🛡️ Security Notes

- **Never commit your `.env` file.** It contains your Moodle token which grants full API access.
- Tokens are loaded server-side — they are never sent to the AI model directly.
- The `.env` file is in `.gitignore` by default.
- For CI/CD, inject `MOODLE_URL` and `MOODLE_TOKEN` as environment secrets.

---

## 📖 API Reference

Full Moodle Web Service API: [Moodle Dev Docs](https://docs.moodle.org/dev/Web_service_API_functions)

---

## 🤝 Contributing

1. Fork the repo
2. Create a feature branch
3. Write tests (TDD preferred — run `PYTHONPATH=src python -m unittest discover -s tests -v`)
4. Open a PR

---

## 📄 License

MIT
