def test_health_endpoint_returns_service_metadata(client):
    response = client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["database_connectivity"] == "up"


def test_alerts_and_metrics_history_endpoints_return_data(client, sample_batch):
    ingest_response = client.post("/ingest", json=sample_batch)
    alerts_response = client.get("/alerts?unresolved_only=true")
    metrics_response = client.get("/metrics/history")

    assert ingest_response.status_code == 200
    assert alerts_response.status_code == 200
    assert metrics_response.status_code == 200
    assert len(alerts_response.json()) >= 1
    assert len(metrics_response.json()["global_metrics"]) == 1
    assert len(metrics_response.json()["feature_metrics"]) >= 1
