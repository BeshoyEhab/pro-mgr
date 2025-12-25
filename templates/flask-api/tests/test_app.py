"""Test Flask app."""

import pytest
from {{name_underscore}}.app import app


@pytest.fixture
def client():
    """Create test client."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_index(client):
    """Test index endpoint."""
    response = client.get('/')
    assert response.status_code == 200
    data = response.get_json()
    assert 'message' in data


def test_health(client):
    """Test health endpoint."""
    response = client.get('/health')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'healthy'
