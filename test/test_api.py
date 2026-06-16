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
    assert "default.yaml" in resp.text


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
