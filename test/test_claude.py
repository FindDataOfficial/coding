"""Tests for claude.py — the agent loop that generates, runs, and fixes Python scripts."""

from unittest import mock
import subprocess
import sys
from pathlib import Path

import pytest

# Ensure the project root is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import claude


# ── extract_script tests ──


def test_extract_script_from_code_block():
    """extract_script should pull Python from a ```python``` fence."""
    output = """Sure! Here's the script:

```python
import csv
print("hello")
```
"""
    result = claude.extract_script(output)
    assert result == 'import csv\nprint("hello")'


def test_extract_script_no_fence_returns_raw():
    """If there is no code fence, the raw output is returned as-is."""
    raw = "just some text, no code block"
    assert claude.extract_script(raw) == raw


def test_extract_script_multiple_blocks_returns_first():
    """Only the first Python code block is extracted."""
    output = """```python
first_block = True
```
```python
second_block = False
```"""
    result = claude.extract_script(output)
    assert result == "first_block = True"


def test_extract_script_non_python_fence_ignored():
    """A ```json or ```bash fence should not match — returns raw."""
    output = """```json
{"key": "value"}
```"""
    result = claude.extract_script(output)
    assert result == output  # no python block → raw


def test_extract_script_multiline():
    """Multi-line scripts inside a fence are preserved intact."""
    output = """```python
def hello():
    print("hello")
    return 42

if __name__ == "__main__":
    hello()
```"""
    result = claude.extract_script(output)
    assert "def hello():" in result
    assert 'print("hello")' in result
    assert "hello()" in result


# ── run_script tests ──


def test_run_script_passes():
    """A valid script that exits 0 returns (True, "")."""
    passed, error = claude.run_script("print('ok')")
    assert passed is True
    assert error == ""


def test_run_script_fails():
    """A script that raises an exception returns (False, stderr)."""
    passed, error = claude.run_script("raise ValueError('boom')")
    assert passed is False
    assert "ValueError" in error
    assert "boom" in error


def test_run_script_syntax_error():
    """A script with a syntax error returns (False, stderr)."""
    passed, error = claude.run_script("def broken(")
    assert passed is False
    assert "SyntaxError" in error


def test_run_script_prints_output():
    """Script stdout is captured and not returned as error."""
    passed, error = claude.run_script("print('hello world')")
    assert passed is True
    assert error == ""


def test_run_script_tmp_file_cleaned_up():
    """The temporary file is deleted after run_script completes."""
    import tempfile
    import os

    # We intercept unlink to verify cleanup, but also let it run
    real_unlink = os.unlink
    unlinked_files = []

    def tracking_unlink(path):
        unlinked_files.append(path)
        real_unlink(path)

    with mock.patch("os.unlink", side_effect=tracking_unlink):
        passed, _ = claude.run_script("x = 1")
        assert passed is True
        assert len(unlinked_files) == 1
        assert unlinked_files[0].endswith(".py")


# ── call_claude_code tests ──


@mock.patch("subprocess.run")
def test_call_claude_code_returns_stdout(mock_run):
    """call_claude_code returns stripped stdout from the claude CLI."""
    mock_run.return_value = mock.Mock(stdout="  response text  \n", stderr="")
    result = claude.call_claude_code("write a script")
    assert result == "response text"
    mock_run.assert_called_once()
    args = mock_run.call_args[0][0]
    assert args[0] == "claude"
    assert args[1] == "-p"


@mock.patch("subprocess.run")
def test_call_claude_code_strips_only_whitespace(mock_run):
    """Leading/trailing whitespace is stripped but internal preserved."""
    mock_run.return_value = mock.Mock(stdout="  line1\n\nline2  ", stderr="")
    result = claude.call_claude_code("prompt")
    assert result == "line1\n\nline2"


@mock.patch("subprocess.run")
def test_call_claude_code_timeout(mock_run):
    """call_claude_code passes a 120s timeout to subprocess.run."""
    mock_run.return_value = mock.Mock(stdout="ok", stderr="")
    claude.call_claude_code("test")
    assert mock_run.call_args[1]["timeout"] == 120


@mock.patch("subprocess.run")
def test_call_claude_code_captures_text(mock_run):
    """call_claude_code uses capture_output=True and text=True."""
    mock_run.return_value = mock.Mock(stdout="ok", stderr="")
    claude.call_claude_code("test")
    assert mock_run.call_args[1]["capture_output"] is True
    assert mock_run.call_args[1]["text"] is True


# ── agent loop tests ──


@mock.patch("claude.run_script")
@mock.patch("claude.call_claude_code")
def test_agent_passes_on_first_try(mock_call, mock_run):
    """When the generated script passes immediately, agent returns it."""
    script = "print('hello from agent')"
    mock_call.return_value = f"```python\n{script}\n```"
    mock_run.return_value = (True, "")

    result = claude.agent("print hello")

    assert result == script
    assert mock_call.call_count == 1
    assert mock_run.call_count == 1


@mock.patch("claude.run_script")
@mock.patch("claude.call_claude_code")
def test_agent_retries_on_failure(mock_call, mock_run):
    """When a script fails, agent feeds the error back and retries."""
    script_v1 = "print('v1')\nraise ValueError('oops')"
    script_v2 = "print('v2 fixed')"

    # First call returns a failing script
    mock_call.side_effect = [
        f"```python\n{script_v1}\n```",
        f"```python\n{script_v2}\n```",
    ]
    # First run fails, second passes
    mock_run.side_effect = [
        (False, "ValueError: oops"),
        (True, ""),
    ]

    result = claude.agent("do something")

    assert result == script_v2
    assert mock_call.call_count == 2
    assert mock_run.call_count == 2

    # Second prompt should contain the error feedback
    second_prompt = mock_call.call_args_list[1][0][0]
    assert "ValueError: oops" in second_prompt
    assert script_v1 in second_prompt
    assert "Fix it" in second_prompt


@mock.patch("claude.run_script")
@mock.patch("claude.call_claude_code")
def test_agent_exhausts_iterations(mock_call, mock_run):
    """After MAX_ITERATIONS failures, agent raises RuntimeError."""
    mock_call.return_value = "```python\nprint('still broken')\n```"
    mock_run.return_value = (False, "SomeError: nope")

    with pytest.raises(RuntimeError, match="failed after"):
        claude.agent("impossible task")

    assert mock_call.call_count == claude.MAX_ITERATIONS
    assert mock_run.call_count == claude.MAX_ITERATIONS


@mock.patch("claude.run_script")
@mock.patch("claude.call_claude_code")
def test_agent_passes_on_last_iteration(mock_call, mock_run):
    """Agent succeeds on the very last allowed iteration."""
    fail_script = "raise Exception('fail')"
    pass_script = "print('finally works')"

    call_outputs = []
    for i in range(claude.MAX_ITERATIONS - 1):
        call_outputs.append(f"```python\n{fail_script}\n```")
    call_outputs.append(f"```python\n{pass_script}\n```")
    mock_call.side_effect = call_outputs

    run_results = [(False, "Exception: fail")] * (claude.MAX_ITERATIONS - 1) + [(True, "")]
    mock_run.side_effect = run_results

    result = claude.agent("do it")

    assert result == pass_script
    assert mock_call.call_count == claude.MAX_ITERATIONS
    assert mock_run.call_count == claude.MAX_ITERATIONS


@mock.patch("claude.run_script")
@mock.patch("claude.call_claude_code")
def test_agent_prompt_includes_task(mock_call, mock_run):
    """The initial prompt to claude should contain the task description."""
    mock_call.return_value = "```python\nprint('ok')\n```"
    mock_run.return_value = (True, "")

    claude.agent("read a CSV and count rows")

    first_prompt = mock_call.call_args[0][0]
    assert "read a CSV and count rows" in first_prompt
    assert "Python script" in first_prompt
    assert "code block" in first_prompt


@mock.patch("claude.run_script")
@mock.patch("claude.call_claude_code")
def test_agent_handles_no_code_fence_in_response(mock_call, mock_run):
    """If claude returns text without a code fence, extract_script returns it raw."""
    raw_script = "print('no fence')"
    mock_call.return_value = raw_script  # no ```python``` wrapper
    mock_run.return_value = (True, "")

    result = claude.agent("simple task")

    assert result == raw_script


@mock.patch("claude.run_script")
@mock.patch("claude.call_claude_code")
def test_agent_error_prompt_includes_previous_script(mock_call, mock_run):
    """After failure, the retry prompt includes the previous failing script."""
    prev_script = "import foo"
    mock_call.side_effect = [
        f"```python\n{prev_script}\n```",
        "```python\nprint('fixed')\n```",
    ]
    mock_run.side_effect = [
        (False, "ModuleNotFoundError: No module named 'foo'"),
        (True, ""),
    ]

    claude.agent("import foo")

    second_prompt = mock_call.call_args_list[1][0][0]
    assert "Previous script:" in second_prompt
    assert prev_script in second_prompt
    assert "ModuleNotFoundError" in second_prompt
    assert "Fix it" in second_prompt


# ── subprocess error handling ──


@mock.patch("claude.run_script")
@mock.patch("claude.call_claude_code")
def test_agent_subprocess_timeout_is_caught(mock_call, mock_run):
    """If call_claude_code raises TimeoutExpired, agent should propagate it."""
    mock_call.side_effect = subprocess.TimeoutExpired(cmd="claude", timeout=120)

    with pytest.raises(subprocess.TimeoutExpired):
        claude.agent("some task")
