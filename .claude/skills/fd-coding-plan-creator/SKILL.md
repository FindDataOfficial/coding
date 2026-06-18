---
name: fd-coding-plan-creator
description: >
  Generate page and service plans from class diagrams and SQLAlchemy schemas.
  Plans describe what pages (UI) and services (backend) to build, which diagram
  classes and schema entities each one uses, and how they connect. Use this when
  the user wants to "plan the pages", "design the UI", "map out services", or
  figure out what screens and APIs are needed before writing code. This skill sits
  between fd-coding-schema-creator and fd-coding-code-creator in the pipeline.
---

# Plan Creator

Generate a page/service plan from class diagrams and SQLAlchemy schemas.
The plan describes what to build — pages (UI), services (backend logic),
and their connections — before any implementation code is written.

This is the "what screens and APIs do we need?" step. It bridges the gap
between data design (schema) and code (fd-coding-code-creator).

## Where things live

- **Input**: `.claude/skills/fd-coding-common-resources/diagram/` — class diagrams + `.claude/skills/fd-coding-common-resources/schema/` — SQLAlchemy models
- **Context**: `.claude/skills/fd-coding-common-resources/goal/initial-goal/` and `.claude/skills/fd-coding-common-resources/goal/clear-goal/` — what the system should do
- **Output**: `plan/` — YAML plan files
- **Directory structure**: Mirror the input. `.claude/skills/fd-coding-common-resources/diagram/paas/mcp-diagram.yaml` → `plan/paas/mcp-plan.yaml`

## Before you start

1. Read the diagram YAML to understand all classes and relationships
2. Read the schema file to understand the data layer
3. Read the goal files (initial + clear) to understand what the system needs to do
4. Check `plan/` for any existing plans for this project

## What a plan describes

A plan has two sections: **pages** (UI/frontend) and **services** (backend/logic).

### Pages

Each page is a screen or view the user interacts with. For each page:

- **name**: What the page is called (e.g., "Server List", "Server Detail")
- **route**: The URL path (e.g., `/servers`, `/servers/:id`)
- **description**: What the user can do on this page
- **components**: UI components on the page (table, form, button, chart, log viewer)
- **uses_schema**: Which schema entities this page reads/writes
- **uses_services**: Which diagram service classes this page calls
- **actions**: What actions the user can take (create, start, stop, delete, view logs)

### Services

Each service is a backend module that provides business logic. For each service:

- **name**: Which diagram class this implements (e.g., "LifecycleManager")
- **type**: The service pattern (manager, router, allocator, deployer, config)
- **description**: What this service does
- **depends_on**: Other services it needs (from diagram relationships)
- **uses_schema**: Schema entities it operates on
- **endpoints**: API endpoints it exposes (if it's a router)
- **key_methods**: The main public methods (from the diagram)

## How to derive pages and services

### From the diagram

- **Classes with "Router" in the name** → generate pages that map to their endpoints
- **Classes with "Manager" or "Service" in the name** → services section
- **Classes with "Allocator" or "Deployer" or "Config" in the name** → services section, utility type
- **Data entity classes** → referenced in `uses_schema`, not planned separately

### From the goal

- **Success criteria** → each one implies pages or services
- **"Dashboard shows..."** → a page
- **"Deploy with one click"** → a page action + service method
- **"Monitor health"** → a page component + service method

### From the schema

- **Each model** → at minimum a list page + detail page (if the goal mentions a UI)
- **Model fields** → form fields and table columns on pages

## Output format

```yaml
# ============================================
# Page & Service Plan for <system-name>
# Generated from <diagram-path> + <schema-path>
# ============================================

system: <system-name>
description: <one-line summary>

pages:
  - name: Server List
    route: /servers
    description: View all registered MCP servers and their status
    components:
      - type: table
        columns: [name, status, port, health]
      - type: button
        label: Deploy New Server
        action: navigate_to_deploy
      - type: badge
        field: status
        mapping:
          running: green
          stopped: gray
          error: red
    uses_schema:
      - MCPServer
    uses_services:
      - ServerRouter.listServers
      - LifecycleManager.getStatus
    actions:
      - name: start
        label: Start
        method: POST /api/servers/:id/start
        confirm: true
      - name: stop
        label: Stop
        method: POST /api/servers/:id/stop
        confirm: true

  - name: Deploy Server
    route: /servers/deploy
    description: Register and deploy a new MCP server
    components:
      - type: form
        fields:
          - name: id
            type: text
            required: true
          - name: name
            type: text
            required: true
          - name: source_path
            type: text
            required: true
          - name: entry_point
            type: text
            default: "server:app"
          - name: health_url
            type: text
            required: true
      - type: button
        label: Deploy
        action: submit
    uses_schema:
      - MCPServer
    uses_services:
      - ServerRouter.deployServer
      - LifecycleManager.startServer
      - NginxConfigManager.generateConfig
    actions:
      - name: deploy
        label: Deploy
        method: POST /api/servers
        redirect: /servers

  - name: Server Detail
    route: /servers/:id
    description: View server details, logs, and health
    components:
      - type: card
        fields: [name, status, port, source_path, entry_point]
      - type: log_viewer
        source: GET /api/servers/:id/logs
      - type: health_indicator
        source: GET /api/servers/:id/health
        poll_interval: 30
    uses_schema:
      - MCPServer
    uses_services:
      - ServerRouter.getServer
      - LifecycleManager.collectLogs
      - LifecycleManager.checkHealth
    actions:
      - name: start
      - name: stop
      - name: restart

services:
  - name: ServerRegistry
    type: manager
    description: YAML-backed CRUD for MCP server records
    depends_on: []
    uses_schema:
      - MCPServer
    key_methods:
      - load
      - save
      - getServer
      - addServer
      - removeServer
      - listServers

  - name: PortAllocator
    type: allocator
    description: Allocate and release ports in range 8100-8199
    depends_on: []
    uses_schema: []
    key_methods:
      - allocate
      - release
      - isAllocated
      - availableCount

  - name: LifecycleManager
    type: manager
    description: Process lifecycle, health polling, log collection
    depends_on:
      - ServerRegistry
      - PortAllocator
    uses_schema: []
    key_methods:
      - startServer
      - stopServer
      - restartServer
      - getStatus
      - checkHealth
      - collectLogs

  - name: NginxConfigManager
    type: config
    description: Generate and reload nginx upstream configs
    depends_on:
      - ServerRegistry
    uses_schema: []
    key_methods:
      - generateConfig
      - reload
      - removeConfig
      - validateConfig

  - name: ServerRouter
    type: router
    description: FastAPI routes for the PAAS dashboard API
    depends_on:
      - ServerRegistry
      - LifecycleManager
      - NginxConfigManager
    uses_schema:
      - MCPServer
    endpoints:
      - GET /api/servers
      - GET /api/servers/:id
      - POST /api/servers
      - POST /api/servers/:id/start
      - POST /api/servers/:id/stop
      - GET /api/servers/:id/logs
      - GET /api/servers/:id/health
    key_methods:
      - listServers
      - getServer
      - deployServer
      - startServer
      - stopServer
      - getLogs

  - name: DockerDeployer
    type: deployer
    description: Optional Docker-based deployment
    depends_on:
      - LifecycleManager
    uses_schema: []
    key_methods:
      - checkDocker
      - generateDockerfile
      - build
      - run
      - stop
```

## Plan conventions

- **Page names**: Human-readable, title case (e.g., "Server List", "Deploy Server")
- **Route paths**: kebab-case, RESTful (`/servers`, `/servers/:id`, `/servers/deploy`)
- **Service names**: Match the diagram class name exactly
- **Component types**: table, form, card, button, badge, chart, log_viewer, health_indicator, modal
- **Action names**: verb in imperative form (start, stop, deploy, delete, refresh)
- **uses_schema**: List the diagram class names of data entities this page/service uses
- **uses_services**: List as `ClassName.methodName` for page actions, `ClassName` for dependencies

## Workflow

### Phase 1: Analyze

1. Read the diagram — list all classes, their types (entity vs service), and relationships
2. Read the schema — list all models and their fields
3. Read the goals — extract success criteria and user-facing requirements
4. Determine which service classes need endpoints (routers) and which are internal

### Phase 2: Plan pages

For each user-facing requirement from the goal:

1. What does the user need to see? → a page
2. What can they do? → actions on that page
3. What data does the page need? → uses_schema
4. What backend calls does it make? → uses_services

### Phase 3: Plan services

For each service class from the diagram:

1. What type is it? (manager, router, allocator, config, deployer)
2. What does it depend on? → from diagram relationships
3. What data does it touch? → uses_schema
4. What are its public methods? → from diagram methods
5. If it's a router, what endpoints? → derived from its methods

### Phase 4: Confirm with the user

Present the plan summary:

- How many pages, what they do
- How many services, what types
- Which services talk to which
- Any gaps (success criteria not covered by any page)

### Phase 5: Generate

Write the plan YAML to `plan/<mirror-path>/<name>-plan.yaml`.

**Quality checks before saving:**
- Every page references at least one schema entity or service
- Every service name matches a class in the diagram
- Every `uses_services` reference exists in the services list
- Route paths are unique across pages
- Every success criterion from the goal maps to at least one page or service

### Phase 6: Validate

1. **Completeness**: Every router-type service has endpoints listed
2. **Consistency**: Page actions reference methods that exist on the services
3. **Coverage**: Every diagram class is accounted for (as a service, or referenced via uses_schema)
4. **YAML syntax**: The file parses without errors (`python -c "import yaml; yaml.safe_load(open('...'))"`)

### Phase 7: Offer to continue the pipeline

After saving the plan, **ask the user**: "Plan saved. Want to generate the implementation code now? I can run `/fd-coding-code-creator` with the diagram, schema, and plan."

If the user says yes, invoke the Skill tool with `skill: "fd-coding-code-creator"` and pass the diagram file path as args. The code-creator will use the plan to guide implementation.

If the user says no or "later", that's fine.
