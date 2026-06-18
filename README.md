# Coding Skills

A YAML-driven config harness with a web dashboard for editing, plus a
design-to-implementation pipeline powered by Claude Code skills.

## Overview

This project does two things:

1. **Config Dashboard** — A FastAPI + vanilla JS SPA that serves as a web
   editor for YAML configuration files. `default.yaml` is the primary
   config (model/database registries), and `dashboard.yaml` controls which
   directories get scanned for editable YAML files.

2. **Design Pipeline** — Four Claude Code skills that form a
   design-to-implementation workflow:

   ```
   goal/initial-goal/   →  /goal-clear       →  goal/clear-goal/
   goal/clear-goal/     →  /diagram-creator   →  diagram/
   diagram/             →  /schema-creator    →  schema/
   diagram/ + schema/   →  /code-creator      →  src/
   ```

   Each skill reads its upstream input, the clear-goal context, and
   mirrors the directory structure so outputs are always easy to find.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run the dashboard (starts on http://127.0.0.1:8000)
python -m dashboard.main serve
# or: config-dashboard

# Run tests
pytest
```

## Project Structure

```
coding-skills/
├── default.yaml              # Primary config (model + DB registries)
├── dashboard.yaml            # Dashboard directory scan config
├── CLAUDE.md                 # Project instructions for Claude Code
│
├── dashboard/                # FastAPI config editor
│   ├── main.py               #   FastAPI app + API routes
│   ├── discovery.py          #   YAML file auto-discovery
│   ├── config.py             #   YAML load/save utilities
│   └── static/index.html     #   SPA (vanilla JS + Tailwind CDN)
│
├── .claude/skills/           # Claude Code skills
│   ├── goal-clear/           #   Brainstorm and refine goals
│   ├── diagram-creator/      #   Generate class diagrams from goals
│   ├── schema-creator/       #   Generate SQLAlchemy models from diagrams
│   └── code-creator/         #   Generate service implementations
│
├── goal/
│   ├── initial-goal/         #   Raw goal definitions (to be refined)
│   │   ├── PAAS/             #     MCP server hosting platform
│   │   ├── DAAS/             #     Data as a Service
│   │   └── code/             #     Code generation goals
│   └── clear-goal/           #   Refined goals (output of /goal-clear)
│       └── PAAS/             #     Refined PAAS goal
│
├── diagram/paas/             # Class diagrams (output of /diagram-creator)
├── schema/paas/              # SQLAlchemy models (output of /schema-creator)
├── src/paas/                 # Service implementations (output of /code-creator)
│
├── template/                 # YAML templates (config, diagram schema)
├── save/                     # Agent and workflow registry templates
├── scripts/                  # CLI utilities (get_defaults.py)
└── test/                     # pytest test suite
```

## Skills

| Skill | Trigger | Input | Output |
|-------|---------|-------|--------|
| `/goal-clear` | Brainstorm a goal | `goal/initial-goal/` | `goal/clear-goal/` |
| `/diagram-creator` | Design class structure | `goal/clear-goal/` | `diagram/` |
| `/schema-creator` | Generate database models | `diagram/` | `schema/` |
| `/code-creator` | Generate implementation | `diagram/` + `schema/` | `src/` |

All skills read the clear-goal context and mirror the source directory
structure (case-insensitive). For example, `goal/initial-goal/PAAS/mcp.md`
produces outputs at `goal/clear-goal/PAAS/mcp.md`,
`diagram/paas/mcp-diagram.yaml`, `schema/paas/mcp.py`, and `src/paas/*.py`.

## Config Schema

`default.yaml` has two main sections:

- **models**: Provider definitions (API keys, base URLs) and model registry
  entries (id, provider, name, max_tokens, temperature). Supports tier
  selectors (`default_model_high/middle/low`).
- **databases**: Database registry with driver, URL, connection pool, SSL,
  and auto-migration settings.

The dashboard provides a schema-aware editor for `default.yaml` and a
generic YAML editor for all other discovered files.

## Tests

```bash
pytest                          # Run all tests
pytest test/test_config.py      # Config load/save/round-trip
pytest test/test_api.py         # API route integration tests
pytest test/test_discovery.py   # File discovery unit tests
```

Tests use temp YAML fixtures and never touch real config files.

## Example Pipeline: MCP PAAS

The full pipeline was exercised on the MCP server hosting platform goal:

- **Goal**: Build a platform to deploy, host, and manage MCP servers
- **Refined**: Split from 1 monolithic goal into 3 sub-goals (MVP →
  Dashboard → Docker)
- **Diagram**: 7 classes (1 data entity `MCPServer` + 6 services)
- **Schema**: Single SQLAlchemy model (`mcp_server` table)
- **Code**: 6 service files (registry, lifecycle, port allocator, nginx
  config, router, docker deployer)

## License

MIT
