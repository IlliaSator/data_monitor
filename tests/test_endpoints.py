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
    assert len(metrics_response.json()["performance_metrics"]) == 1


def test_alert_status_and_retraining_events_endpoints_work(client, sample_batch):
    client.post("/ingest", json=sample_batch)
    alerts = client.get("/alerts").json()
    update_response = client.patch(f"/alerts/{alerts[0]['id']}", json={"status": "acknowledged"})
    retrain_response = client.post(
        "/retrain/trigger",
        json={"reason": "Manual trigger from endpoint test"},
    )
    events_response = client.get("/retrain/events")

    assert update_response.status_code == 200
    assert update_response.json()["status"] == "acknowledged"
    assert retrain_response.status_code == 200
    assert retrain_response.json()["retrain_required"] is True
    assert events_response.status_code == 200
    assert len(events_response.json()) >= 1
