
import uuid


def create_deployment(client):
    project_response = client.post(
        "/api/v1/projects",
        json={
            "name": "status-test-project",
            "repository_url": "https://github.com/example/status-test",
        },
    )
    assert project_response.status_code == 201
    project_id = project_response.json()["id"]

    application_response = client.post(
        f"/api/v1/projects/{project_id}/applications",
        json={
            "name": "status-test-api",
            "image": "nginx",
            "port": 80,
            "replicas": 1,
        },
    )
    assert application_response.status_code == 201
    application_id = application_response.json()["id"]

    deployment_response = client.post(
        f"/api/v1/applications/{application_id}/deployments",
        json={
            "environment": "dev",
            "image_tag": "v1.0.0",
        },
    )
    assert deployment_response.status_code == 201

    return deployment_response.json()["id"]


def update_status(client, deployment_id, status):
    return client.patch(
        f"/api/v1/deployments/{deployment_id}/status",
        json={"status": status},
    )


def test_pending_to_running(client):
    deployment_id = create_deployment(client)

    response = update_status(client, deployment_id, "running")

    assert response.status_code == 200
    assert response.json()["status"] == "running"


def test_running_to_succeeded(client):
    deployment_id = create_deployment(client)

    update_status(client, deployment_id, "running")
    response = update_status(client, deployment_id, "succeeded")

    assert response.status_code == 200
    assert response.json()["status"] == "succeeded"


def test_running_to_failed(client):
    deployment_id = create_deployment(client)

    update_status(client, deployment_id, "running")
    response = update_status(client, deployment_id, "failed")

    assert response.status_code == 200
    assert response.json()["status"] == "failed"


def test_pending_to_succeeded_returns_409(client):
    deployment_id = create_deployment(client)

    response = update_status(client, deployment_id, "succeeded")

    assert response.status_code == 409


def test_pending_to_failed_returns_409(client):
    deployment_id = create_deployment(client)

    response = update_status(client, deployment_id, "failed")

    assert response.status_code == 409


def test_succeeded_to_running_returns_409(client):
    deployment_id = create_deployment(client)

    update_status(client, deployment_id, "running")
    update_status(client, deployment_id, "succeeded")

    response = update_status(client, deployment_id, "running")

    assert response.status_code == 409


def test_failed_to_running_returns_409(client):
    deployment_id = create_deployment(client)

    update_status(client, deployment_id, "running")
    update_status(client, deployment_id, "failed")

    response = update_status(client, deployment_id, "running")

    assert response.status_code == 409


def test_same_status_transition_returns_409(client):
    deployment_id = create_deployment(client)

    response = update_status(client, deployment_id, "pending")

    assert response.status_code == 409


def test_invalid_status_returns_422(client):
    deployment_id = create_deployment(client)

    response = update_status(client, deployment_id, "completed")

    assert response.status_code == 422


def test_nonexistent_deployment_returns_404(client):
    response = update_status(client, uuid.uuid4(), "running")

    assert response.status_code == 404


def test_status_persisted_in_database(client):
    deployment_id = create_deployment(client)

    response = update_status(client, deployment_id, "running")
    assert response.status_code == 200

    get_response = client.get(
        f"/api/v1/deployments/{deployment_id}"
    )

    assert get_response.status_code == 200
    assert get_response.json()["status"] == "running"


def test_invalid_transition_preserves_status(client):
    deployment_id = create_deployment(client)

    response = update_status(client, deployment_id, "succeeded")
    assert response.status_code == 409

    get_response = client.get(
        f"/api/v1/deployments/{deployment_id}"
    )

    assert get_response.status_code == 200
    assert get_response.json()["status"] == "pending"
