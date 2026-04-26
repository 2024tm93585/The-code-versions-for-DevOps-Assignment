"""
Integration tests for the ACEest Fitness Flask application.
Tests cover the main routes using the Flask test client.
"""
import json
import pytest
from app import create_app


@pytest.fixture
def app():
    """Create a test application instance with in-memory SQLite."""
    test_app = create_app({
        'TESTING': True,
        'DATABASE': ':memory:',
        'SECRET_KEY': 'test-secret-key',
        'WTF_CSRF_ENABLED': False,
    })
    yield test_app


@pytest.fixture
def client(app):
    """Return a test client for the app."""
    return app.test_client()


def test_health_check(client):
    """GET /health should return 200 with healthy status."""
    response = client.get('/health')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'healthy'
    assert data['service'] == 'ACEest Fitness API'


def test_index_page(client):
    """GET / should return 200 and render the dashboard."""
    response = client.get('/')
    assert response.status_code == 200
    assert b'ACEest' in response.data


def test_clients_page(client):
    """GET /clients should return 200 and render the clients list."""
    response = client.get('/clients')
    assert response.status_code == 200
    assert b'Clients' in response.data


def test_programs_page(client):
    """GET /programs should return 200 and render the programs list."""
    response = client.get('/programs')
    assert response.status_code == 200
    assert b'Programs' in response.data


def test_add_client_page(client):
    """GET /clients/add should return 200 and render the add client form."""
    response = client.get('/clients/add')
    assert response.status_code == 200
    assert b'Add' in response.data


def test_api_clients_empty(client):
    """GET /api/clients on a fresh DB should return 200 and an empty list."""
    response = client.get('/api/clients')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert isinstance(data, list)


def test_api_programs(client):
    """GET /api/programs should return 200 and a dict with expected program keys."""
    response = client.get('/api/programs')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert isinstance(data, dict)
    assert 'Fat Loss (FL) - 3 day' in data
    assert 'Fat Loss (FL) - 5 day' in data
    assert 'Muscle Gain (MG) - PPL' in data
    assert 'Beginner (BG)' in data
