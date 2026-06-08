from datetime import datetime

from app.routes.api_routes import bloom_filter_routes


def test_stats_endpoint(client, mock_bloom):

    bloom_filter_routes.loaded_bloom = mock_bloom
    bloom_filter_routes.last_updated = datetime.utcnow()

    response = client.get("/bloom/api/v1/stats")

    assert response.status_code == 200

    data = response.json()

    assert data["size"] == 100
    assert data["capacity"] == 120
    assert data["error_rate"] == 0.001


def test_check_word_found(client, mock_bloom):

    bloom_filter_routes.loaded_bloom = mock_bloom

    response = client.post(
        "/bloom/api/v1/check-word",
        json={"word": "hello"},
    )

    assert response.status_code == 200
    assert response.json()["status"] is True


def test_check_word_not_found(client, mock_bloom):

    mock_bloom.contains.return_value = False
    bloom_filter_routes.loaded_bloom = mock_bloom

    response = client.post(
        "/bloom/api/v1/check-word",
        json={"word": "missing"},
    )

    assert response.status_code == 200
    assert response.json()["status"] is False


def test_check_empty_word(client, mock_bloom):

    bloom_filter_routes.loaded_bloom = mock_bloom

    response = client.post(
        "/bloom/api/v1/check-word",
        json={"word": ""},
    )

    assert response.status_code == 200
    assert response.json()["status"] is False