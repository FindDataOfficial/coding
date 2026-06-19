# FD-Coding Skills

Six Claude Code skills that form a complete design-to-implementation pipeline.
Each skill reads the output of the previous one, produces its own artifact,
and offers to chain to the next step.

## Installation

```bash
# One-liner (project-scope, recommended)
curl -fsSL https://raw.githubusercontent.com/FindDataOfficial/coding/master/install.sh | bash

# One-liner (global)
curl -fsSL https://raw.githubusercontent.com/FindDataOfficial/coding/master/install.sh | bash -s -- --global

# Or clone first, then install
git clone https://github.com/FindDataOfficial/coding.git /tmp/fd-skills && \
  /tmp/fd-skills/install.sh && rm -rf /tmp/fd-skills
```

## Pipeline

```
fd-coding-goal-clear → fd-coding-diagram-creator → fd-coding-schema-creator → fd-coding-plan-creator → fd-coding-code-creator → fd-coding-project-builder
    (brainstorm)       (class diagram)        (DB models)        (pages/services)     (implementation)       (pytest + Cypress)
```

| # | Skill | What it does | Input | Output |
|---|-------|-------------|-------|--------|
| 1 | `fd-coding-goal-clear` | Brainstorm and refine goals | `goal/initial-goal/` | `goal/clear-goal/` |
| 2 | `fd-coding-diagram-creator` | Design class diagrams | `goal/clear-goal/` + `goal/initial-goal/` | `diagram/` |
| 3 | `fd-coding-schema-creator` | Generate SQLAlchemy models | `diagram/` + `goal/clear-goal/` | `schema/` |
| 4 | `fd-coding-plan-creator` | Plan pages and services | `diagram/` + `schema/` + `goal/` | `plan/` |
| 5 | `fd-coding-code-creator` | Generate service implementations | `diagram/` + `schema/` + `plan/` | `src/` |
| 6 | `fd-coding-project-builder` | TDD with pytest + Cypress E2E | `goal/` + `diagram/` + `schema/` | `src/` + `test/` + `cypress/` |

All input/output paths above are relative to `.claude/skills/fd-coding-common-resources/`.

## Directory Structure

The sub-directory name is **not hardcoded**. `fd-coding-goal-clear` asks for the
project name when it starts, and all downstream skills derive it from the
filesystem. Example with project name `my-app`:

```
.claude/skills/fd-coding-common-resources/
├── goal/
│   ├── initial-goal/               ← raw goals
│   └── clear-goal/                 ← refined goals (skill 1)
│       └── my-app/
│           └── mcp.md
├── diagram/                        ← class diagrams (skill 2)
│   └── my-app/
│       └── mcp-diagram.yaml
├── schema/                         ← SQLAlchemy models (skill 3)
│   └── my-app/
│       └── mcp.py
├── plan/                           ← page/service plans (skill 4)
│   └── my-app/
│       └── mcp-plan.yaml
├── src/                            ← implementation (skill 5)
│   └── my-app/
│       └── *.py
└── test/                           ← unit tests (skill 6 — pytest)
│   └── my-app/
│       └── *.py
└── cypress/e2e/                    ← E2E tests (skill 6 — Cypress)
    └── my-app/
        └── *.cy.js
```

## How Each Skill Works

### 1. fd-coding-goal-clear

A thinking partner for goals. First asks for the **project name** using
`AskUserQuestion` (this becomes the sub-directory for all outputs). Then
reads a raw goal from `goal/initial-goal/`, discusses it with you (scope,
steps, constraints, alternatives), and saves the refined version to
`goal/clear-goal/<project>/`.

Uses `AskUserQuestion` for all decisions — scope, splitting, approach
choices. Never lists options as plain text.

**Triggers**: "think through this goal", "refine my plan", "brainstorm this idea"

### 2. fd-coding-diagram-creator

Reads the refined goal and designs a class diagram in YAML. Extracts nouns
as classes and verbs as methods. Uses `AskUserQuestion` for design choices
(composition vs association, class boundaries, inheritance vs composition).
Reads `scripts/template.yaml` for output format.

**Triggers**: "create a class diagram", "design the classes", "UML for this"

### 3. fd-coding-schema-creator

Reads the class diagram and generates Python SQLAlchemy models. Automatically
distinguishes data entities (→ models) from service classes (→ skipped with
comments). Uses `AskUserQuestion` to confirm classification decisions.
Reads the clear-goal for design decisions (e.g., "YAML not SQLite").

**Triggers**: "generate schema", "create database models", "SQLAlchemy for this"

### 4. fd-coding-plan-creator

Bridges data design and code. Reads the diagram + schema and generates a
YAML plan describing every page (UI) and service (backend) to build. Each
page lists its route, components, actions, and which schema/services it uses.
Reads `scripts/template.yaml` for output format.

**Triggers**: "plan the pages", "design the UI", "what screens do we need"

### 5. fd-coding-code-creator

Reads the diagram + schema + plan and generates Python service implementations.
Uses constructor dependency injection, proper error handling, and type hints.
Only generates service classes (data entities are already in `schema/`).

**Triggers**: "implement this", "generate the code", "write the services"

### 6. fd-coding-project-builder

TDD-based project builder. Writes **pytest** unit tests first (service classes,
data entities, API routes), then **Cypress** E2E tests (page flows, user
interactions). Runs both suites, catches failures, auto-fixes bugs, and repeats
until everything passes. Outputs to project root `src/`, `test/`, and
`cypress/e2e/`.

**Triggers**: "build the project", "make it work with tests", "TDD this"

## Key Design Decisions

- **No hardcoded directory names**: `fd-coding-goal-clear` asks for the project
  name, all downstream skills derive it from the filesystem
- **Terminal choices everywhere**: Every skill uses `AskUserQuestion` for
  decisions, confirmations, and pipeline chaining — never plain text lists
- **Shared context**: Every skill reads this README as step 1, so the LLM
  always knows where it is in the pipeline
- **Template files**: Output format templates live in each skill's
  `scripts/template.yaml`, not embedded in SKILL.md
- **Chaining**: After saving, each skill asks "continue to next?" via
  `AskUserQuestion`. Yes chains forward, no stops gracefully.

## Chaining

After each skill saves its output, it uses `AskUserQuestion` to ask whether
to continue. You can run the entire pipeline in one flow:

```
/fd-coding-goal-clear → "yes" → /fd-coding-diagram-creator → "yes" → /fd-coding-schema-creator → "yes" → /fd-coding-plan-creator → "yes" → /fd-coding-code-creator → "yes" → /fd-coding-project-builder
```

Or stop at any point and continue later — the next skill reads from the
filesystem, not from memory.
