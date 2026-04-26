"""
Unit tests for the ACEest Fitness models module.
Tests cover database helpers and business logic functions.
"""
import pytest
from app import create_app
from app.models import (
    get_programs,
    calculate_calories,
    save_client,
    get_client_by_name,
    delete_client,
    get_all_clients,
)


@pytest.fixture
def app():
    """Create a test application with in-memory SQLite database."""
    test_app = create_app({
        'TESTING': True,
        'DATABASE': ':memory:',
        'SECRET_KEY': 'test-secret-key',
    })
    yield test_app


def test_get_programs_returns_dict(app):
    """get_programs() should return a dict with all expected program keys."""
    programs = get_programs()
    assert isinstance(programs, dict)
    assert 'Fat Loss (FL) - 3 day' in programs
    assert 'Fat Loss (FL) - 5 day' in programs
    assert 'Muscle Gain (MG) - PPL' in programs
    assert 'Beginner (BG)' in programs
    # Each program should have factor and desc
    for name, data in programs.items():
        assert 'factor' in data
        assert 'desc' in data
        assert isinstance(data['factor'], int)


def test_calculate_calories_fat_loss(app):
    """calculate_calories(70, 'Fat Loss (FL) - 3 day') should return 1540."""
    result = calculate_calories(70, 'Fat Loss (FL) - 3 day')
    assert result == 1540  # 70 * 22


def test_calculate_calories_muscle_gain(app):
    """calculate_calories(80, 'Muscle Gain (MG) - PPL') should return 2800."""
    result = calculate_calories(80, 'Muscle Gain (MG) - PPL')
    assert result == 2800  # 80 * 35


def test_calculate_calories_unknown_program(app):
    """calculate_calories with an unknown program should return 0."""
    result = calculate_calories(70, 'Unknown Program')
    assert result == 0


def test_save_and_get_client(app):
    """save_client then get_client_by_name should return the saved client."""
    with app.app_context():
        success = save_client(app, 'Alice Smith', 30, 165.0, 60.0, 'Fat Loss (FL) - 3 day')
        assert success is True

        client = get_client_by_name(app, 'Alice Smith')
        assert client is not None
        assert client['name'] == 'Alice Smith'
        assert client['age'] == 30
        assert client['height'] == 165.0
        assert client['weight'] == 60.0
        assert client['program'] == 'Fat Loss (FL) - 3 day'
        assert client['calories'] == 1320  # 60 * 22


def test_delete_client(app):
    """save_client then delete_client should result in None on get."""
    with app.app_context():
        save_client(app, 'Bob Jones', 25, 180.0, 85.0, 'Muscle Gain (MG) - PPL')
        deleted = delete_client(app, 'Bob Jones')
        assert deleted is True

        client = get_client_by_name(app, 'Bob Jones')
        assert client is None


def test_delete_nonexistent_client(app):
    """delete_client on a name that does not exist should return False."""
    with app.app_context():
        result = delete_client(app, 'Ghost User')
        assert result is False


def test_get_all_clients_empty(app):
    """get_all_clients on a fresh DB should return an empty list."""
    with app.app_context():
        clients = get_all_clients(app)
        assert isinstance(clients, list)
        assert len(clients) == 0


def test_get_all_clients_multiple(app):
    """get_all_clients should return all saved clients."""
    with app.app_context():
        save_client(app, 'Carol White', 28, 162.0, 58.0, 'Fat Loss (FL) - 5 day')
        save_client(app, 'Dave Brown', 35, 178.0, 90.0, 'Beginner (BG)')
        clients = get_all_clients(app)
        names = [c['name'] for c in clients]
        assert 'Carol White' in names
        assert 'Dave Brown' in names
