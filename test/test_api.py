"""Tests for dashboard API endpoints."""


def test_get_config(client):
    """GET /api/config should return the full config as JSON."""
    resp = client.get("/api/config")
    assert resp.status_code == 200
    data = resp.json()
    assert "models" in data
    assert "databases" in data
    assert data["models"]["default"] == "claude-sonnet"
    assert data["databases"]["default"] == "sqlite-dev"


def test_get_config_models_registry(client):
    """The config should contain model registries."""
    resp = client.get("/api/config")
    data = resp.json()
    models = data["models"]["registry"]
    assert len(models) == 2
    assert models[0]["id"] == "claude-sonnet"


def test_get_config_databases_registry(client):
    """The config should contain database registries."""
    resp = client.get("/api/config")
    data = resp.json()
    dbs = data["databases"]["registry"]
    assert len(dbs) == 2


def test_post_config_save(client, temp_yaml_path):
    """POST /api/config should save data to the YAML file."""
    resp = client.get("/api/config")
    data = resp.json()

    # Modify
    data["models"]["registry"].append({
        "id": "new-model",
        "provider": "anthropic",
        "name": "new-model-1",
        "max_tokens": 2048,
        "temperature": 0.5,
    })
    data["models"]["default"] = "new-model"

    # Save
    post_resp = client.post("/api/config", json=data)
    assert post_resp.status_code == 200
    assert post_resp.json() == {"ok": True}

    # Verify by reloading
    get_resp = client.get("/api/config")
    new_data = get_resp.json()
    assert new_data["models"]["default"] == "new-model"
    assert len(new_data["models"]["registry"]) == 3


def test_post_config_delete_model(client):
    """Saving a config with a model removed should persist."""
    resp = client.get("/api/config")
    data = resp.json()

    # Remove one model
    data["models"]["registry"] = [m for m in data["models"]["registry"] if m["id"] != "gpt-4o"]
    data["models"]["default"] = "claude-sonnet"

    post_resp = client.post("/api/config", json=data)
    assert post_resp.status_code == 200

    get_resp = client.get("/api/config")
    new_data = get_resp.json()
    assert len(new_data["models"]["registry"]) == 1
    assert new_data["models"]["registry"][0]["id"] == "claude-sonnet"


def test_post_config_add_database(client):
    """Saving a config with a new database should persist."""
    resp = client.get("/api/config")
    data = resp.json()

    data["databases"]["registry"].append({
        "id": "mongo-dev",
        "driver": "mongodb",
        "url": "mongodb://localhost:27017/skills",
        "pool": {"min_size": 2, "max_size": 20, "timeout_seconds": 30},
    })
    data["databases"]["default"] = "mongo-dev"

    post_resp = client.post("/api/config", json=data)
    assert post_resp.status_code == 200

    get_resp = client.get("/api/config")
    new_data = get_resp.json()
    assert len(new_data["databases"]["registry"]) == 3
    assert new_data["databases"]["default"] == "mongo-dev"


def test_static_index_html_served(client):
    """The root path should serve the dashboard HTML page."""
    resp = client.get("/")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]
    assert "Config Dashboard" in resp.text
    assert "sidebar-item-active" in resp.text  # new sidebar layout indicator


def test_post_config_empty_registry(client):
    """Saving an empty registry should work."""
    resp = client.get("/api/config")
    data = resp.json()

    data["models"]["registry"] = []
    data["models"]["default"] = ""

    post_resp = client.post("/api/config", json=data)
    assert post_resp.status_code == 200

    get_resp = client.get("/api/config")
    assert get_resp.json()["models"]["registry"] == []
    assert get_resp.json()["models"]["default"] == ""


# ── Multi-file API tests (use multi_file_env fixture) ──


def test_list_files(multi_file_env):
    """GET /api/files should return all discovered YAML files."""
    client = multi_file_env["client"]
    resp = client.get("/api/files")
    assert resp.status_code == 200
    files = resp.json()
    assert isinstance(files, list)
    assert len(files) >= 4  # default.yaml, extra/settings.yaml, save/agents.yaml, save/workflows.yaml, nested/deep/config.yaml

    names = [f["name"] for f in files]
    assert "default.yaml" in names
    assert "extra/settings.yaml" in names
    assert "save/agents.yaml" in names
    assert "save/workflows.yaml" in names
    # nested/deep/config.yaml should be found (recursive scan)
    assert "nested/deep/config.yaml" in names


def test_get_file(multi_file_env):
    """GET /api/files/{name} should return file content as JSON."""
    client = multi_file_env["client"]
    resp = client.get("/api/files/save/agents.yaml")
    assert resp.status_code == 200
    data = resp.json()
    assert "agents" in data
    assert data["agents"]["default"] == "helper"


def test_get_file_404(multi_file_env):
    """GET /api/files/{name} for unknown file should return 404."""
    client = multi_file_env["client"]
    resp = client.get("/api/files/nonexistent.yaml")
    assert resp.status_code == 404


def test_post_file_save(multi_file_env):
    """POST /api/files/{name} should save and round-trip correctly."""
    client = multi_file_env["client"]

    # Load
    resp = client.get("/api/files/extra/settings.yaml")
    data = resp.json()
    data["theme"] = "light"
    data["new_key"] = "new_value"

    # Save
    post_resp = client.post("/api/files/extra/settings.yaml", json=data)
    assert post_resp.status_code == 200
    assert post_resp.json() == {"ok": True}

    # Verify
    get_resp = client.get("/api/files/extra/settings.yaml")
    new_data = get_resp.json()
    assert new_data["theme"] == "light"
    assert new_data["new_key"] == "new_value"


def test_post_file_404(multi_file_env):
    """POST /api/files/{name} for unknown file should return 404."""
    client = multi_file_env["client"]
    resp = client.post("/api/files/nonexistent.yaml", json={"key": "val"})
    assert resp.status_code == 404


def test_rich_editor_flag(multi_file_env):
    """File matching rich_editor should have is_rich=True, others False."""
    client = multi_file_env["client"]
    resp = client.get("/api/files")
    files = resp.json()

    for f in files:
        if f["name"] == "default.yaml":
            assert f["is_rich"] is True, f"Expected {f['name']} to be rich"
        else:
            assert f["is_rich"] is False, f"Expected {f['name']} NOT to be rich"


def test_backward_compat_get_config(multi_file_env):
    """GET /api/config should still work in multi-file mode."""
    client = multi_file_env["client"]
    resp = client.get("/api/config")
    assert resp.status_code == 200
    data = resp.json()
    assert "models" in data
    assert data["models"]["default"] == "test-model"


def test_backward_compat_post_config(multi_file_env):
    """POST /api/config should still work in multi-file mode."""
    client = multi_file_env["client"]
    resp = client.get("/api/config")
    data = resp.json()
    data["models"]["default"] = "modified"

    post_resp = client.post("/api/config", json=data)
    assert post_resp.status_code == 200

    get_resp = client.get("/api/config")
    assert get_resp.json()["models"]["default"] == "modified"
