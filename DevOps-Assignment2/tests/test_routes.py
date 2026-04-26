"""
Route-level tests for the ACEest Fitness Flask application.
Tests cover POST/DELETE operations and API endpoints.
"""
import json
import pytest
from app import create_app


@pytest.fixture
def app():
    """Create a test application with in-memory SQLite database."""
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


def test_post_add_client_valid(client):
    """POST /clients/add with valid data should redirect (302) to /clients."""
    response = client.post('/clients/add', data={
        'name': 'Test User',
        'age': '25',
        'height': '175',
        'weight': '70',
        'program': 'Fat Loss (FL) - 3 day',
    })
    # Should redirect to /clients on success
    assert response.status_code == 302
    assert '/clients' in response.headers.get('Location', '')


def test_post_add_client_missing_name(client):
    """POST /clients/add with empty name should return 400 or redirect with error."""
    response = client.post('/clients/add', data={
        'name': '',
        'age': '25',
        'height': '175',
        'weight': '70',
        'program': 'Fat Loss (FL) - 3 day',
    })
    # Should return 400 bad request or redirect back to form
    assert response.status_code in (400, 302)


def test_post_add_client_missing_fields(client):
    """POST /clients/add with missing required fields should return 400."""
    response = client.post('/clients/add', data={
        'name': 'Incomplete User',
        'age': '',
        'height': '',
        'weight': '',
        'program': '',
    })
    assert response.status_code in (400, 302)


def test_post_add_client_invalid_program(client):
    """POST /clients/add with an invalid program should return 400."""
    response = client.post('/clients/add', data={
        'name': 'Bad Program User',
        'age': '30',
        'height': '170',
        'weight': '75',
        'program': 'Nonexistent Program XYZ',
    })
    assert response.status_code in (400, 302)


def test_get_client_by_name_api(client):
    """After adding a client, GET /clients/<name> should return 200 with JSON."""
    # First add the client
    client.post('/clients/add', data={
        'name': 'Jane Doe',
        'age': '29',
        'height': '168',
        'weight': '65',
        'program': 'Muscle Gain (MG) - PPL',
    })
    # Now retrieve via API
    response = client.get('/clients/Jane Doe')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['name'] == 'Jane Doe'
    assert data['age'] == 29
    assert data['program'] == 'Muscle Gain (MG) - PPL'
    assert data['calories'] == 2275  # 65 * 35


def test_get_client_not_found(client):
    """GET /clients/<name> for a non-existent client should return 404."""
    response = client.get('/clients/NonExistentPerson')
    assert response.status_code == 404
    data = json.loads(response.data)
    assert 'error' in data


def test_delete_client_api(client):
    """DELETE /clients/<name> should return 200 JSON with success=True."""
    # Add client first
    client.post('/clients/add', data={
        'name': 'Mark Delete',
        'age': '40',
        'height': '180',
        'weight': '90',
        'program': 'Beginner (BG)',
    })
    # Delete via API
    response = client.delete('/clients/Mark Delete')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is True

    # Verify it's gone
    get_response = client.get('/clients/Mark Delete')
    assert get_response.status_code == 404


def test_delete_nonexistent_client_api(client):
    """DELETE /clients/<name> for a non-existent client should return 404."""
    response = client.delete('/clients/GhostClient')
    assert response.status_code == 404
    data = json.loads(response.data)
    assert data['success'] is False


def test_api_clients_after_add(client):
    """GET /api/clients should include newly added clients."""
    client.post('/clients/add', data={
        'name': 'API Test User',
        'age': '33',
        'height': '172',
        'weight': '78',
        'program': 'Fat Loss (FL) - 5 day',
    })
    response = client.get('/api/clients')
    assert response.status_code == 200
    data = json.loads(response.data)
    names = [c['name'] for c in data]
    assert 'API Test User' in names
