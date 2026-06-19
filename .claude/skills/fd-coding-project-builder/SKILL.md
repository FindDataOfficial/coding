---
name: fd-coding-project-builder
description: >
  Build complete, tested projects from design artifacts using test-driven
  development. Reads goals, diagrams, and schemas, then writes tests first
  and implementation second — automatically fixing bugs until all tests
  pass. Use this when the user wants to "build the project", "implement
  everything", "make it work with tests", or when the pipeline
  (goal→diagram→schema) is complete and it's time to write tested code.
---

# Project Builder

Build a complete, tested project from the full design pipeline output.
You read the goal (what to build), the diagram (class structure), and the
schema (data layer), then use TDD to produce working code.

The key difference from fd-coding-code-creator: you write **tests first**, run them
(they fail), write implementation, run them again (they pass), and
automatically fix any bugs that tests catch.

## Where things live

- **Input**: `goal/` (initial + clear), `.claude/skills/fd-coding-common-resources/diagram/`, `.claude/skills/fd-coding-common-resources/schema/` — the full design pipeline output
- **Output**: Project root — tested implementation and tests go directly into the project
- **Unit tests**: `test/` — pytest for service classes, data entities, API routes
- **E2E tests**: `cypress/e2e/` — Cypress for UI flows, page interactions, user journeys
- **Directory structure**: Flat at project root. `diagram/paas/mcp-diagram.yaml` → `src/paas/*.py`, `test/paas/*.py`, `cypress/e2e/paas/*.cy.js`

## Before you start

1. **Read `.claude/skills/fd-coding-common-resources/README.md`** — Understand the full FD-Coding pipeline, where shared resources live, and what comes before/after this skill.
2. Read the goal file (both initial-goal and clear-goal if both exist) to understand what to build and the success criteria
2. Read the diagram YAML to understand all classes, methods, and relationships
3. Read the schema file to understand the data layer
4. Check if `src/` already has code from fd-coding-code-creator (you'll extend it with tests)
5. Check if `test/` already has tests for this project

## TDD Workflow

The core loop: **Write test → Run test (fail) → Write code → Run test (pass) → Fix bugs → Repeat**

### Phase 1: Plan the test suite

From the goal, diagram, and schema, identify what needs testing:

1. **Read the success criteria from the goal** — Every success criterion becomes at least one test
2. **Read the diagram's methods** — Every public method on a service class gets a test
3. **Read the schema** — Every data entity gets CRUD tests
4. **Read the constraints** — Edge cases and error conditions become tests

**Use `AskUserQuestion`** to present the test plan and get approval:

- How many test files, what each covers
- Which success criteria each test maps to
- What edge cases are covered

### Phase 2: Write unit tests first (RED — pytest)

Write pytest files before writing any implementation. Tests should:

- Use pytest conventions (matching the project's existing test style)
- Use fixtures for shared setup (temp files, mock services)
- Test one thing per test function
- Have descriptive names that explain what's being tested
- Cover happy path + error cases + edge cases

If `src/` already has code from fd-coding-code-creator, write tests that verify
the existing code works. If `src/` is empty, write the tests first and
the implementation will follow.

### Phase 2b: Write E2E tests (RED — Cypress)

After unit tests, write Cypress E2E tests for UI flows derived from the plan:

- Every page from the plan gets at least one E2E test
- Test user actions: navigate, fill forms, click buttons, verify results
- Test page interactions: sidebar navigation, modal dialogs, form validation
- Use `cy.visit()`, `cy.get()`, `cy.contains()`, `cy.should()` patterns
- Place tests at `cypress/e2e/<path>/<page>.cy.js`

```javascript
// cypress/e2e/paas/server-list.cy.js
describe('Server List Page', () => {
  beforeEach(() => {
    cy.visit('/servers');
  });

  it('displays all registered servers', () => {
    cy.get('[data-cy=server-row]').should('have.length.at.least', 1);
  });

  it('can navigate to deploy page', () => {
    cy.contains('Deploy New Server').click();
    cy.url().should('include', '/servers/deploy');
  });

  it('can start a stopped server', () => {
    cy.contains('tr', 'test-server')
      .contains('Start').click();
    cy.contains('tr', 'test-server')
      .find('[data-cy=status-badge]').should('contain', 'running');
  });
});
```

### Phase 3: Run unit tests and implement (GREEN)

Run pytest. Tests should fail (RED phase). Then:

1. If `src/` already exists, fix bugs until tests pass
2. If `src/` is empty, implement the minimum code to make each test pass
3. Run `pytest test/ -x --tb=short` after each change — fail fast, fix fast

### Phase 4: Run E2E tests and fix UI (GREEN)

Start the app and run Cypress:

```bash
npx cypress run --spec "cypress/e2e/<path>/"
```

Fix any E2E failures — these are usually:
- Missing `data-cy` attributes on elements
- Wrong route paths (check the plan's `route` field)
- API not returning expected data (check service implementation)

### Phase 5: Auto-repair bugs (REFACTOR + FIX)

This is the critical loop. After all tests pass:

1. **Run unit tests** — `pytest test/ -x --tb=short`
2. **Run E2E tests** — `npx cypress run`
3. **If any test fails**, analyze the error:
   - Import error → fix the import path
   - Assertion error → fix the logic
   - AttributeError → check the diagram for the correct method name
   - Type error → fix the type annotation
   - Cypress timeout → check the element selector or API response
4. **Fix the bug**, re-run both suites, repeat until ALL tests pass
5. **Never leave a failing test** — either fix the code or fix the test
   (if the test expectation was wrong)

### Phase 6: Verify against success criteria

Cross-check the goal's success criteria against the passing tests:

- Every success criterion has a pytest unit test that verifies it
- Every page from the plan has a Cypress E2E test
- Every constraint is tested (or at least considered)
- Both test suites pass clean — no warnings, no skipped tests, no flaky retries

## Test patterns

### Testing service classes

```python
import pytest
from src.paas.registry import ServerRegistry

class TestServerRegistry:
    def test_add_and_get_server(self, temp_yaml_file):
        registry = ServerRegistry(temp_yaml_file)
        server = MCPServer(id="test-1", name="Test", ...)
        registry.add_server(server)
        assert registry.get_server("test-1") == server

    def test_remove_nonexistent_server_raises(self, temp_yaml_file):
        registry = ServerRegistry(temp_yaml_file)
        with pytest.raises(KeyError):
            registry.remove_server("nonexistent")

    def test_save_and_load_roundtrip(self, temp_yaml_file):
        registry = ServerRegistry(temp_yaml_file)
        server = MCPServer(id="test-1", name="Test", ...)
        registry.add_server(server)
        registry.save()

        registry2 = ServerRegistry(temp_yaml_file)
        registry2.load()
        assert registry2.get_server("test-1").name == "Test"
```

### Testing with fixtures

```python
@pytest.fixture
def temp_yaml_file(tmp_path):
    return tmp_path / "servers.yaml"

@pytest.fixture
def populated_registry(temp_yaml_file):
    registry = ServerRegistry(temp_yaml_file)
    registry.add_server(MCPServer(id="s1", name="Server 1", ...))
    registry.add_server(MCPServer(id="s2", name="Server 2", ...))
    return registry
```

### Testing error conditions

Every service method that can fail should have a test for that failure:

- `KeyError` / `ValueError` for invalid inputs
- `RuntimeError` for invalid states (e.g., starting an already-running server)
- `FileNotFoundError` for missing files
- Edge cases: empty list, max capacity, concurrent operations

## Bug fixing guide

When a test fails, follow this order:

1. **Read the error message carefully** — What actually failed?
2. **Check the diagram** — Does the code match the designed API?
3. **Check the schema** — Are you importing from the right path?
4. **Check the goal** — Does the success criterion clarify the expected behavior?
5. **Fix the minimal thing** — Don't rewrite everything, fix the specific bug
6. **Re-run the test** — Confirm it passes before moving on

Common bugs and their fixes:

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| `ImportError` | Wrong module path | Check `src/` directory structure matches imports |
| `AttributeError: 'X' has no attribute 'y'` | Method name mismatch | Check diagram for correct method name (convert camelCase to snake_case) |
| `AssertionError: expected X, got Y` | Logic bug | Trace the method, fix the logic |
| `TypeError: X() missing argument` | Constructor signature mismatch | Check diagram for constructor params (attributes → `__init__` params) |

## Quality checks

Before declaring the project built:

- [ ] `pytest test/ -q` passes with zero failures
- [ ] `npx cypress run` passes with zero failures
- [ ] Every success criterion from the goal has a corresponding unit test
- [ ] Every page from the plan has a corresponding E2E test
- [ ] Every public method from the diagram has a unit test
- [ ] Error cases are tested (not just happy path)
- [ ] Pages use `data-cy` attributes for Cypress selectors
- [ ] No bare `except:` in tests or implementation
- [ ] All imports resolve to existing modules
- [ ] Test files follow the project's existing test conventions (conftest.py fixtures, temp files)
