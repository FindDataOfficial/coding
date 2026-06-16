---
name: goal-tracker
description: Track and complete goals stored in goal/initial-goal/. Use this skill whenever the user mentions goals, wants to check progress, finish a goal, or asks "what's next." Also use it when the user talks about completing tasks, wrapping up work, or needs help working through a multi-step plan. If the user says they've finished something major, check whether it maps to a goal and offer to mark it complete.
---

# Goal Tracker

You help the user progress through goals defined in `goal/initial-goal/` and document completions in `goal/final-goal/`.

## Workflow

```
Check goals → Load active goal → Help complete → Document completion
```

### Step 1: Check for existing goals

Look in `goal/initial-goal/` for goal definition files (`.md` files). Each file represents one goal.

- If goals exist, present them to the user and ask which one they want to work on.
- If no goals exist, move to **Creating a new goal**.

### Step 2: Load and understand the goal

Read the selected goal file. Extract:

- **Title**: What this goal is about
- **Steps/Tasks**: The concrete work items needed
- **Success criteria**: What "done" looks like

Present a clear summary to the user and identify what's already been done vs what remains.

### Step 3: Help complete the goal

Work through the remaining steps with the user:

- Break each step into actionable sub-tasks
- Track progress as steps are completed
- When a step is done, acknowledge it and move to the next
- If the user gets blocked, note the blocker and suggest alternatives

Be proactive — don't just wait for the user to drive. If you see a way to advance the goal, suggest it.

### Step 4: Document completion

When the user confirms the goal is fully done, create a YAML file in `goal/final-goal/`:

```yaml
goal: <goal-title>
source: goal/initial-goal/<filename>.md
completed_at: <ISO 8601 timestamp>
summary: |
  <2-3 sentence summary of what was accomplished>
steps_completed:
  - <step 1>
  - <step 2>
outcome: |
  <description of the final result, any deliverables created>
files_changed:
  - <path relative to project root>
notes: <optional, any lessons learned or follow-ups>
```

Name the file after the goal slug (lowercase, hyphens): `goal/final-goal/<slug>.yaml`.

---

## Creating a new goal

If no goal exists in `goal/initial-goal/`, interview the user to create one:

1. **What do you want to accomplish?** — Get a clear title and one-sentence description
2. **What are the steps?** — Break it into 3-7 concrete, ordered steps
3. **What does "done" look like?** — Define success criteria
4. **Any constraints or deadlines?** — Capture scope limits

Then write the goal to `goal/initial-goal/<slug>.md`:

```markdown
# [Goal Title]

## Description
[One paragraph describing what this goal aims to achieve]

## Steps
1. [Step name] — [What needs to happen]
2. [Step name] — [What needs to happen]
...

## Success Criteria
- [Criterion 1]
- [Criterion 2]

## Constraints
- [Any limits on scope, time, resources]
```

After creating it, move to Step 2 of the main workflow.

---

## Principles

- **One goal at a time** — Focus the user on a single goal. If multiple goals exist, prioritize the one the user wants, or the first unfinished one.
- **Keep it concrete** — Vague goals are hard to complete. If a goal is fuzzy, help the user refine it before starting work.
- **Document as you go** — Don't wait until the very end to capture what happened. Take mental notes of files changed and decisions made.
- **Completion is a ceremony** — Creating the final-goal YAML is a deliberate act. It marks the transition from "working on it" to "done." Don't rush it or skip it.
