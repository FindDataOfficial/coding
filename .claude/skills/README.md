# FD-Coding Skills

Six Claude Code skills that form a complete design-to-implementation pipeline.
Each skill reads the output of the previous one, produces its own artifact,
and offers to chain to the next step.

## Pipeline

```
fd-coding-goal-clear → fd-coding-diagram-creator → fd-coding-schema-creator → fd-coding-plan-creator → fd-coding-code-creator → fd-coding-project-builder
    (brainstorm)       (class diagram)        (DB models)        (pages/services)     (implementation)       (TDD + tests)
```

| # | Skill | What it does | Input | Output |
|---|-------|-------------|-------|--------|
| 1 | `fd-coding-goal-clear` | Brainstorm and refine goals | `goal/initial-goal/` | `goal/clear-goal/` |
| 2 | `fd-coding-diagram-creator` | Design class diagrams | `goal/clear-goal/` + `goal/initial-goal/` | `diagram/` |
| 3 | `fd-coding-schema-creator` | Generate SQLAlchemy models | `diagram/` + `goal/clear-goal/` | `schema/` |
| 4 | `fd-coding-plan-creator` | Plan pages and services | `diagram/` + `schema/` + `goal/` | `plan/` |
| 5 | `fd-coding-code-creator` | Generate service implementations | `diagram/` + `schema/` + `plan/` | `src/` |
| 6 | `fd-coding-project-builder` | Write tests, implement, fix bugs | `goal/` + `diagram/` + `schema/` | `src/` + `test/` |

## Directory Structure

All skills mirror the source directory structure so outputs are always easy to find:

```
goal/initial-goal/PAAS/mcp.md       ← raw goal
goal/clear-goal/PAAS/mcp.md         ← refined goal (skill 1)
diagram/paas/mcp-diagram.yaml       ← class diagram (skill 2)
schema/paas/mcp.py                  ← SQLAlchemy models (skill 3)
plan/paas/mcp-plan.yaml             ← page/service plan (skill 4)
src/paas/*.py                       ← implementation (skill 5)
test/test_paas/*.py                 ← tests (skill 6)
```

## How Each Skill Works

### 1. fd-coding-goal-clear

A thinking partner for goals. Reads a raw goal from `goal/initial-goal/`,
discusses it with you (scope, steps, constraints, alternatives), and saves
the refined version to `goal/clear-goal/`. Does NOT execute — only brainstorms.

**Triggers**: "think through this goal", "refine my plan", "brainstorm this idea"

### 2. fd-coding-diagram-creator

Reads the refined goal and designs a class diagram in YAML. Extracts nouns
as classes and verbs as methods. Presents the design for approval before
generating.

**Triggers**: "create a class diagram", "design the classes", "UML for this"

### 3. fd-coding-schema-creator

Reads the class diagram and generates Python SQLAlchemy models. Automatically
distinguishes data entities (→ models) from service classes (→ skipped with
comments). Reads the clear-goal for design decisions (e.g., "YAML not SQLite").

**Triggers**: "generate schema", "create database models", "SQLAlchemy for this"

### 4. fd-coding-plan-creator

Bridges data design and code. Reads the diagram + schema and generates a
YAML plan describing every page (UI) and service (backend) to build. Each
page lists its route, components, actions, and which schema/services it uses.

**Triggers**: "plan the pages", "design the UI", "what screens do we need"

### 5. fd-coding-code-creator

Reads the diagram + schema + plan and generates Python service implementations.
Uses constructor dependency injection, proper error handling, and type hints.
Only generates service classes (data entities are already in `schema/`).

**Triggers**: "implement this", "generate the code", "write the services"

### 6. fd-coding-project-builder

TDD-based project builder. Reads the full design pipeline (goal + diagram +
schema) and writes tests first, then implementation. Runs tests, catches
failures, auto-fixes bugs, and repeats until everything passes. Verifies
every success criterion from the goal has a test.

**Triggers**: "build the project", "make it work with tests", "TDD this"

## Chaining

After each skill saves its output, it asks whether to continue to the next
skill. You can run the entire pipeline in one flow:

```
/fd-coding-goal-clear → "yes" → /fd-coding-diagram-creator → "yes" → /fd-coding-schema-creator → "yes" → /fd-coding-plan-creator → "yes" → /fd-coding-code-creator → "yes" → /fd-coding-project-builder
```

Or stop at any point and continue later — the next skill reads from the
filesystem, not from memory.

## Example: MCP PAAS

The full pipeline was exercised on an MCP server hosting platform:

- **Goal**: Build a platform to deploy, host, and manage MCP servers
- **Refined**: Split from 8 monolithic steps into 3 sub-goals (MVP → Dashboard → Docker)
- **Diagram**: 7 classes (1 data entity `MCPServer` + 6 services)
- **Schema**: Single `MCPServer` SQLAlchemy model
- **Plan**: 3 pages (Server List, Deploy, Detail) + 6 services (registry, lifecycle, etc.)
- **Code**: 7 Python files with constructor injection and error handling
- **Tests**: pytest suite covering all success criteria
