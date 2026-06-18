import subprocess
import tempfile
import os

MAX_ITERATIONS = 5

def call_claude_code(prompt: str) -> str:
    """Call Claude Code CLI and capture output."""
    result = subprocess.run(
        ["claude", "-p", prompt, "--output-format", "text"],
        capture_output=True,
        text=True,
        timeout=120
    )
    return result.stdout.strip()

def extract_script(claude_output: str) -> str:
    """Extract Python code block from Claude's response."""
    import re
    pattern = r"```python\n(.*?)```"
    match = re.search(pattern, claude_output, re.DOTALL)
    return match.group(1).strip() if match else claude_output

def run_script(script: str) -> tuple[bool, str]:
    """Run the script and return (passed, error_message)."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", delete=False
    ) as f:
        f.write(script)
        tmp_path = f.name

    try:
        result = subprocess.run(
            ["python", tmp_path],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            return True, ""
        else:
            return False, result.stderr
    finally:
        os.unlink(tmp_path)

def agent(task: str) -> str:
    """
    Agent loop: generate → run → fix → repeat until pass.
    Returns the final passing script.
    """
    prompt = f"Write a Python script to: {task}. Return only the code block."
    
    for i in range(MAX_ITERATIONS):
        print(f"\n--- Iteration {i + 1} ---")
        
        # 1. Call Claude Code
        claude_output = call_claude_code(prompt)
        script = extract_script(claude_output)
        print(f"Generated script:\n{script}\n")
        
        # 2. Run and check
        passed, error = run_script(script)
        
        if passed:
            print("✅ Script passed!")
            return script
        
        # 3. Feed error back into next prompt
        print(f"❌ Failed: {error}")
        prompt = (
            f"The previous script failed with this error:\n{error}\n\n"
            f"Previous script:\n```python\n{script}\n```\n\n"
            f"Fix it and return only the corrected code block."
        )
    
    raise RuntimeError(f"Agent failed after {MAX_ITERATIONS} iterations")


if __name__ == "__main__":
    final_script = agent("read a CSV file and print the row count")
    print("\n=== Final Passing Script ===")
    print(final_script)