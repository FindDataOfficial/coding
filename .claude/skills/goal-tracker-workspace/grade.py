#!/usr/bin/env python3
"""Grade goal-tracker eval runs. Checks assertions against actual outputs."""
import sys, json, os, re

def check(eval_dir):
    """Returns list of {text, passed, evidence} dicts."""
    results = []

    # Determine which eval this is
    eval_name = os.path.basename(eval_dir)

    if "discover-existing-goals" in eval_name:
        report = None
        for sub in ["with_skill", "without_skill"]:
            outputs_dir = os.path.join(eval_dir, sub, "outputs")
            for f in os.listdir(outputs_dir):
                if f.endswith(".md"):
                    with open(os.path.join(outputs_dir, f)) as fh:
                        report = fh.read()
                    break

        if report:
            results.append({
                "text": "Found exactly 1 goal",
                "passed": "Goals Found: 1" in report or "**1 goal**" in report.lower(),
                "evidence": "Report mentions 1 goal"
            })
            results.append({
                "text": "Identified goal title 'Scraw'",
                "passed": "Scraw" in report,
                "evidence": "Report contains 'Scraw'"
            })
            results.append({
                "text": "Listed all 6 steps",
                "passed": all(s in report for s in ["Analyze the scraping task", "Select the right tool", "Load sub-skills", "Execute the scrape", "Structure the output", "Return results"]),
                "evidence": "All 6 step names present in report"
            })
            results.append({
                "text": "Mentioned success criteria",
                "passed": "success criteria" in report.lower() or "Success Criteria" in report,
                "evidence": "Report includes success criteria section"
            })
            results.append({
                "text": "Noted no steps started (pending state)",
                "passed": "pending" in report.lower() or "no work" in report.lower() or "none" in report.lower() or "initial state" in report.lower(),
                "evidence": "Report indicates no work has been done"
            })

    elif "create-new-goal" in eval_name:
        # Check test-project for goal file creation
        tp = os.path.join(eval_dir, "test-project")
        goal_dir = os.path.join(tp, "goal", "initial-goal")

        goal_files = []
        if os.path.isdir(goal_dir):
            goal_files = [f for f in os.listdir(goal_dir) if f.endswith(".md")]

        goal_created = len(goal_files) > 0
        results.append({
            "text": "Created goal file in goal/initial-goal/",
            "passed": goal_created,
            "evidence": f"Found {len(goal_files)} .md files: {goal_files}"
        })

        if goal_created:
            with open(os.path.join(goal_dir, goal_files[0])) as fh:
                content = fh.read()

            results.append({
                "text": "Goal file contains CI/CD in title",
                "passed": "CI/CD" in content or "ci/cd" in content.lower(),
                "evidence": f"Goal file title area contains CI/CD"
            })
            results.append({
                "text": "Goal file lists all 5 steps",
                "passed": all(str(i) in content for i in range(1, 6)),
                "evidence": "Steps numbered 1-5 found in content"
            })
            results.append({
                "text": "Goal file mentions GitHub Actions",
                "passed": "GitHub Actions" in content,
                "evidence": "GitHub Actions mentioned in goal"
            })
            results.append({
                "text": "Goal file includes success criteria",
                "passed": "Success Criteria" in content or "success" in content.lower(),
                "evidence": "Success criteria section present"
            })
            results.append({
                "text": "Goal file includes constraints",
                "passed": "free tier" in content.lower() or "Constraints" in content or "constraint" in content.lower(),
                "evidence": "Constraints mentioned in goal"
            })

    elif "complete-goal" in eval_name:
        tp = os.path.join(eval_dir, "test-project")
        final_dir = os.path.join(tp, "goal", "final-goal")

        yaml_files = []
        if os.path.isdir(final_dir):
            yaml_files = [f for f in os.listdir(final_dir) if f.endswith(".yaml") or f.endswith(".yml")]

        yaml_created = len(yaml_files) > 0
        results.append({
            "text": "Created YAML file in goal/final-goal/",
            "passed": yaml_created,
            "evidence": f"Found {len(yaml_files)} YAML files: {yaml_files}"
        })

        if yaml_created:
            with open(os.path.join(final_dir, yaml_files[0])) as fh:
                content = fh.read()

            results.append({
                "text": "YAML has 'goal' field",
                "passed": bool(re.search(r'^goal:', content, re.MULTILINE)),
                "evidence": "'goal:' field found"
            })
            results.append({
                "text": "YAML has 'completed_at' field",
                "passed": bool(re.search(r'^completed_at:', content, re.MULTILINE)),
                "evidence": "'completed_at:' field found"
            })
            results.append({
                "text": "YAML has all 5 steps_completed",
                "passed": "steps_completed:" in content and len([l for l in content.split('\n') if l.strip().startswith('- ') and 'CSS' in l or 'toggle' in l or 'theme' in l or 'localStorage' in l or 'Test' in l]) >= 4,
                "evidence": "steps_completed list with dark mode steps found"
            })
            results.append({
                "text": "YAML lists all 3 changed files",
                "passed": "style.css" in content and "index.html" in content and "theme.js" in content,
                "evidence": "All 3 files mentioned in files_changed"
            })
            results.append({
                "text": "YAML has 'summary' field",
                "passed": bool(re.search(r'^summary:', content, re.MULTILINE)),
                "evidence": "'summary:' field found"
            })
            results.append({
                "text": "YAML has 'outcome' field",
                "passed": bool(re.search(r'^outcome:', content, re.MULTILINE)),
                "evidence": "'outcome:' field found"
            })

    return results


def main():
    if len(sys.argv) < 2:
        print("Usage: grade.py <eval-directory>")
        sys.exit(1)

    eval_dir = sys.argv[1]

    for sub in ["with_skill", "without_skill"]:
        sub_dir = os.path.join(eval_dir, sub)
        if not os.path.isdir(sub_dir):
            continue

        results = check(eval_dir)

        grading = {"expectations": results, "summary": {"passed": sum(1 for r in results if r["passed"]), "total": len(results)}}

        out_path = os.path.join(sub_dir, "grading.json")
        with open(out_path, "w") as fh:
            json.dump(grading, fh, indent=2)
        print(f"Graded {sub_dir} -> {grading['summary']['passed']}/{grading['summary']['total']} passed")

if __name__ == "__main__":
    main()