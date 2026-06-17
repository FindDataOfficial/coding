"""Tests for dashboard/discovery.py."""

import tempfile
from pathlib import Path

import pytest
import yaml

from dashboard.discovery import (
    annotate_rich_editor,
    discover_yaml_files,
    load_dashboard_config,
)


# ── load_dashboard_config tests ──


def test_load_dashboard_config_valid(tmp_path):
    """Valid dashboard.yaml should parse correctly."""
    cfg_path = tmp_path / "dashboard.yaml"
    cfg = {
        "scan": [{"path": "foo", "recursive": True}],
        "rich_editor": "myfile.yaml",
    }
    with open(cfg_path, "w") as f:
        yaml.dump(cfg, f)

    result = load_dashboard_config(cfg_path)
    assert result["scan"] == [{"path": "foo", "recursive": True}]
    assert result["rich_editor"] == "myfile.yaml"


def test_load_dashboard_config_missing(tmp_path):
    """Missing dashboard.yaml should return default config."""
    result = load_dashboard_config(tmp_path / "nonexistent.yaml")
    assert result["scan"] == [{"path": ".", "recursive": False}]
    assert result["rich_editor"] == "default.yaml"


def test_load_dashboard_config_empty_file(tmp_path):
    """Empty dashboard.yaml should return default config."""
    cfg_path = tmp_path / "dashboard.yaml"
    cfg_path.write_text("")

    result = load_dashboard_config(cfg_path)
    assert result["scan"] == [{"path": ".", "recursive": False}]
    assert result["rich_editor"] == "default.yaml"


def test_load_dashboard_config_missing_keys_filled(tmp_path):
    """Missing scan or rich_editor keys should be filled with defaults."""
    cfg_path = tmp_path / "dashboard.yaml"
    with open(cfg_path, "w") as f:
        yaml.dump({"scan": [{"path": "x", "recursive": False}]}, f)

    result = load_dashboard_config(cfg_path)
    assert result["scan"] == [{"path": "x", "recursive": False}]
    assert result["rich_editor"] == "default.yaml"  # filled in


def test_load_dashboard_config_invalid_yaml(tmp_path):
    """Invalid YAML should return default config."""
    cfg_path = tmp_path / "dashboard.yaml"
    cfg_path.write_text("::: not valid yaml :::")

    result = load_dashboard_config(cfg_path)
    assert result["scan"] == [{"path": ".", "recursive": False}]


# ── discover_yaml_files tests ──


def _make_yaml(path: Path, content: dict):
    """Helper: write a dict as a YAML file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        yaml.dump(content, f)


def test_discover_flat_directory(tmp_path):
    """Scan a directory with 3 .yaml files — all should be found."""
    _make_yaml(tmp_path / "a.yaml", {"key": "a"})
    _make_yaml(tmp_path / "b.yaml", {"key": "b"})
    _make_yaml(tmp_path / "c.yaml", {"key": "c"})

    result = discover_yaml_files(
        [{"path": str(tmp_path), "recursive": False}],
        project_root=tmp_path,
    )
    names = [f["name"] for f in result]
    assert len(names) == 3
    assert "a.yaml" in names
    assert "b.yaml" in names
    assert "c.yaml" in names


def test_discover_recursive(tmp_path):
    """With recursive: true, nested files should be found."""
    _make_yaml(tmp_path / "top.yaml", {"k": 1})
    _make_yaml(tmp_path / "sub" / "mid.yaml", {"k": 2})
    _make_yaml(tmp_path / "sub" / "deep" / "bottom.yaml", {"k": 3})

    result = discover_yaml_files(
        [{"path": str(tmp_path), "recursive": True}],
        project_root=tmp_path,
    )
    names = [f["name"] for f in result]
    assert len(names) == 3
    assert "top.yaml" in names
    assert "sub/mid.yaml" in names
    assert "sub/deep/bottom.yaml" in names


def test_discover_non_recursive(tmp_path):
    """With recursive: false, nested files should NOT be found."""
    _make_yaml(tmp_path / "top.yaml", {"k": 1})
    _make_yaml(tmp_path / "sub" / "hidden.yaml", {"k": 2})

    result = discover_yaml_files(
        [{"path": str(tmp_path), "recursive": False}],
        project_root=tmp_path,
    )
    names = [f["name"] for f in result]
    assert "top.yaml" in names
    assert "sub/hidden.yaml" not in names


def test_discover_ignores_non_yaml(tmp_path):
    """.txt and .json files should be excluded."""
    _make_yaml(tmp_path / "real.yaml", {"k": 1})
    (tmp_path / "notes.txt").write_text("hello")
    (tmp_path / "data.json").write_text('{"a": 1}')
    (tmp_path / "readme.md").write_text("# hi")

    result = discover_yaml_files(
        [{"path": str(tmp_path), "recursive": False}],
        project_root=tmp_path,
    )
    names = [f["name"] for f in result]
    assert names == ["real.yaml"]


def test_discover_deduplicates(tmp_path):
    """Two scan entries that overlap should not produce duplicates."""
    _make_yaml(tmp_path / "shared.yaml", {"k": 1})
    _make_yaml(tmp_path / "only_here.yaml", {"k": 2})
    sub = tmp_path / "sub"
    sub.mkdir()
    _make_yaml(sub / "nested.yaml", {"k": 3})

    # Both scan entries point at the same root
    result = discover_yaml_files(
        [
            {"path": str(tmp_path), "recursive": True},
            {"path": str(tmp_path), "recursive": True},
        ],
        project_root=tmp_path,
    )
    names = [f["name"] for f in result]
    # Should have 3 unique files, not 6
    assert len(names) == 3
    assert names.count("shared.yaml") == 1


def test_discover_excludes_dashboard_yaml(tmp_path):
    """dashboard.yaml itself should not appear in results."""
    _make_yaml(tmp_path / "dashboard.yaml", {"scan": []})
    _make_yaml(tmp_path / "real.yaml", {"k": 1})

    result = discover_yaml_files(
        [{"path": str(tmp_path), "recursive": False}],
        project_root=tmp_path,
        dashboard_yaml_name="dashboard.yaml",
    )
    names = [f["name"] for f in result]
    assert "dashboard.yaml" not in names
    assert "real.yaml" in names


def test_discover_empty_directory(tmp_path):
    """An empty directory should return [] with no crash."""
    result = discover_yaml_files(
        [{"path": str(tmp_path), "recursive": False}],
        project_root=tmp_path,
    )
    assert result == []


def test_discover_nonexistent_directory(tmp_path):
    """A scan entry pointing to a nonexistent directory should be skipped."""
    _make_yaml(tmp_path / "real.yaml", {"k": 1})

    result = discover_yaml_files(
        [
            {"path": str(tmp_path), "recursive": False},
            {"path": str(tmp_path / "does_not_exist"), "recursive": True},
        ],
        project_root=tmp_path,
    )
    names = [f["name"] for f in result]
    assert names == ["real.yaml"]


def test_discover_yml_extension(tmp_path):
    """.yml files should be discovered alongside .yaml files."""
    _make_yaml(tmp_path / "a.yaml", {"k": 1})
    _make_yaml(tmp_path / "b.yml", {"k": 2})

    result = discover_yaml_files(
        [{"path": str(tmp_path), "recursive": False}],
        project_root=tmp_path,
    )
    names = [f["name"] for f in result]
    assert len(names) == 2
    assert "b.yml" in names


def test_discover_sorted_by_name(tmp_path):
    """Results should be sorted alphabetically by name."""
    _make_yaml(tmp_path / "z.yaml", {"k": 3})
    _make_yaml(tmp_path / "a.yaml", {"k": 1})
    _make_yaml(tmp_path / "m.yaml", {"k": 2})

    result = discover_yaml_files(
        [{"path": str(tmp_path), "recursive": False}],
        project_root=tmp_path,
    )
    names = [f["name"] for f in result]
    assert names == ["a.yaml", "m.yaml", "z.yaml"]


# ── annotate_rich_editor tests ──


def test_annotate_rich_editor_match():
    """The file matching rich_editor_name should get is_rich=True."""
    files = [
        {"name": "a.yaml"},
        {"name": "b.yaml"},
    ]
    result = annotate_rich_editor(files, "b.yaml")
    assert result[0]["is_rich"] is False
    assert result[1]["is_rich"] is True


def test_annotate_rich_editor_no_match():
    """If no file matches, all should have is_rich=False."""
    files = [
        {"name": "a.yaml"},
        {"name": "b.yaml"},
    ]
    result = annotate_rich_editor(files, "nonexistent.yaml")
    assert result[0]["is_rich"] is False
    assert result[1]["is_rich"] is False
