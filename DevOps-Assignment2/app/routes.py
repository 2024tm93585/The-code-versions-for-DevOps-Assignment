from flask import Blueprint, render_template, request, redirect, url_for, jsonify, flash, current_app
from .models import (
    get_all_clients,
    get_client_by_name,
    save_client,
    delete_client,
    get_programs,
)

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    clients = get_all_clients(current_app._get_current_object())
    programs = get_programs()
    return render_template(
        'index.html',
        client_count=len(clients),
        program_count=len(programs)
    )


@main_bp.route('/clients')
def clients():
    all_clients = get_all_clients(current_app._get_current_object())
    return render_template('clients.html', clients=all_clients)


@main_bp.route('/clients/add', methods=['GET'])
def add_client_form():
    programs = get_programs()
    return render_template('add_client.html', programs=programs)


@main_bp.route('/clients/add', methods=['POST'])
def add_client():
    name = request.form.get('name', '').strip()
    age = request.form.get('age', '').strip()
    height = request.form.get('height', '').strip()
    weight = request.form.get('weight', '').strip()
    program = request.form.get('program', '').strip()

    if not name:
        flash('Client name is required.', 'danger')
        return redirect(url_for('main.add_client_form')), 400

    if not age or not height or not weight or not program:
        flash('All fields are required.', 'danger')
        return redirect(url_for('main.add_client_form')), 400

    try:
        age_val = int(age)
        height_val = float(height)
        weight_val = float(weight)
    except ValueError:
        flash('Age, height, and weight must be valid numbers.', 'danger')
        return redirect(url_for('main.add_client_form')), 400

    programs = get_programs()
    if program not in programs:
        flash('Invalid program selected.', 'danger')
        return redirect(url_for('main.add_client_form')), 400

    success = save_client(
        current_app._get_current_object(),
        name, age_val, height_val, weight_val, program
    )

    if success:
        flash(f'Client "{name}" added successfully!', 'success')
        return redirect(url_for('main.clients'))
    else:
        flash('Failed to save client. Please try again.', 'danger')
        return redirect(url_for('main.add_client_form')), 500


@main_bp.route('/clients/<name>', methods=['GET'])
def get_client(name):
    client = get_client_by_name(current_app._get_current_object(), name)
    if client is None:
        return jsonify({'error': 'Client not found', 'name': name}), 404
    return jsonify(client), 200


@main_bp.route('/clients/<name>', methods=['DELETE'])
def remove_client(name):
    deleted = delete_client(current_app._get_current_object(), name)
    if deleted:
        return jsonify({'success': True, 'message': f'Client "{name}" deleted successfully'}), 200
    return jsonify({'success': False, 'error': 'Client not found'}), 404


@main_bp.route('/programs')
def programs():
    all_programs = get_programs()
    return render_template('programs.html', programs=all_programs)


@main_bp.route('/health')
def health():
    return jsonify({'status': 'healthy', 'service': 'ACEest Fitness API'}), 200


@main_bp.route('/api/clients')
def api_clients():
    all_clients = get_all_clients(current_app._get_current_object())
    return jsonify(all_clients), 200


@main_bp.route('/api/programs')
def api_programs():
    all_programs = get_programs()
    return jsonify(all_programs), 200
