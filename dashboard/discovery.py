"""YAML file discovery — scans configured directories for .yaml/.yml files."""

from pathlib import Path

import yaml


def load_dashboard_config(path: Path) -> dict:
    """Load dashboard.yaml and return its config dict.

    Returns a default config if the file doesn't exist or is unreadable,
    so the dashboard degrades gracefully to scanning the project root.
    """
    default = {
        "scan": [{"path": ".", "recursive": False}],
        "rich_editor": "default.yaml",
    }

    if not path.exists():
        return default

    try:
        with open(path, "r") as f:
            cfg = yaml.safe_load(f)
    except (yaml.YAMLError, OSError):
        return default

    if cfg is None or not isinstance(cfg, dict):
        return default

    # Merge with defaults so missing keys are filled in
    if "scan" not in cfg:
        cfg["scan"] = default["scan"]
    if "rich_editor" not in cfg:
        cfg["rich_editor"] = default["rich_editor"]

    return cfg


def discover_yaml_files(
    scan_configs: list[dict],
    project_root: Path,
    dashboard_yaml_name: str = "dashboard.yaml",
) -> list[dict]:
    """Walk configured directories and return metadata for every .yaml/.yml file.

    Args:
        scan_configs: List of {path, recursive} dicts from dashboard.yaml.
        project_root: Absolute path to the project root (resolves relative paths).
        dashboard_yaml_name: Filename of the dashboard config itself (excluded from results).

    Returns:
        List of dicts sorted by name, each with:
          - name: relative path used as the API identifier
          - path: absolute filesystem path (as string)
          - relative: relative path from project_root (same as name)
          - is_rich: True if this file matches the rich_editor config entry
    """
    seen: set[str] = set()  # deduplicate by resolved absolute path
    results: list[dict] = []

    for entry in scan_configs:
        scan_path = entry.get("path", ".")
        recursive = entry.get("recursive", False)
        target_dir = (project_root / scan_path).resolve()

        if not target_dir.exists() or not target_dir.is_dir():
            continue

        if recursive:
            glob_iter = target_dir.rglob("*")
        else:
            glob_iter = target_dir.glob("*")

        for file_path in glob_iter:
            if not file_path.is_file():
                continue
            if file_path.suffix not in (".yaml", ".yml"):
                continue
            if file_path.name == dashboard_yaml_name:
                continue

            abs_path = str(file_path.resolve())
            if abs_path in seen:
                continue
            seen.add(abs_path)

            try:
                rel_path = str(file_path.resolve().relative_to(project_root.resolve()))
            except ValueError:
                # File is outside project root — use absolute path as fallback
                rel_path = abs_path

            results.append(
                {
                    "name": rel_path,
                    "path": abs_path,
                    "relative": rel_path,
                }
            )

    results.sort(key=lambda f: f["name"])
    return results


def annotate_rich_editor(
    files: list[dict], rich_editor_name: str
) -> list[dict]:
    """Mark the file matching rich_editor_name with is_rich=True."""
    for f in files:
        f["is_rich"] = f["name"] == rich_editor_name or f.get("relative", f["name"]) == rich_editor_name
    return files
