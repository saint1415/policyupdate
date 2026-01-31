"""
Authentication Routes
Login, logout, and user management endpoints
"""

from functools import wraps
from pathlib import Path

try:
    from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
    from flask_login import login_user, logout_user, login_required, current_user
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False

from .auth import AuthManager, admin_required, manager_required

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


def init_auth_routes(app, auth_manager: AuthManager):
    """Initialize authentication routes"""

    @auth_bp.route('/login', methods=['GET', 'POST'])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for('index'))

        if request.method == 'POST':
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '')

            if not username or not password:
                flash('Please enter username and password.', 'error')
                return render_template('auth/login.html')

            user = auth_manager.authenticate(username, password)

            if user:
                login_user(user, remember=request.form.get('remember', False))
                flash(f'Welcome back, {user.username}!', 'success')

                next_page = request.args.get('next')
                if next_page:
                    return redirect(next_page)
                return redirect(url_for('index'))

            flash('Invalid username or password.', 'error')

        return render_template('auth/login.html')

    @auth_bp.route('/logout')
    @login_required
    def logout():
        logout_user()
        flash('You have been logged out.', 'info')
        return redirect(url_for('auth.login'))

    @auth_bp.route('/profile', methods=['GET', 'POST'])
    @login_required
    def profile():
        if request.method == 'POST':
            action = request.form.get('action')

            if action == 'change_password':
                old_password = request.form.get('old_password', '')
                new_password = request.form.get('new_password', '')
                confirm_password = request.form.get('confirm_password', '')

                if not old_password or not new_password:
                    flash('Please fill in all password fields.', 'error')
                elif new_password != confirm_password:
                    flash('New passwords do not match.', 'error')
                elif len(new_password) < 8:
                    flash('Password must be at least 8 characters.', 'error')
                else:
                    try:
                        if auth_manager.change_password(current_user.id, old_password, new_password):
                            flash('Password changed successfully.', 'success')
                        else:
                            flash('Current password is incorrect.', 'error')
                    except ValueError as e:
                        flash(str(e), 'error')

        return render_template('auth/profile.html', user=current_user)

    # =========================================================================
    # USER MANAGEMENT (Admin only)
    # =========================================================================

    @auth_bp.route('/users')
    @login_required
    @admin_required
    def list_users():
        users = auth_manager.list_users()
        return render_template('auth/users.html', users=users)

    @auth_bp.route('/users/new', methods=['GET', 'POST'])
    @login_required
    @admin_required
    def create_user():
        if request.method == 'POST':
            username = request.form.get('username', '').strip()
            email = request.form.get('email', '').strip()
            password = request.form.get('password', '')
            role = request.form.get('role', 'viewer')

            if not username or not email or not password:
                flash('Please fill in all required fields.', 'error')
            else:
                try:
                    user = auth_manager.create_user(username, email, password, role)
                    flash(f'User {username} created successfully.', 'success')
                    return redirect(url_for('auth.list_users'))
                except ValueError as e:
                    flash(str(e), 'error')

        return render_template('auth/user_form.html', user=None, roles=['admin', 'manager', 'analyst', 'viewer'])

    @auth_bp.route('/users/<user_id>/edit', methods=['GET', 'POST'])
    @login_required
    @admin_required
    def edit_user(user_id):
        user = auth_manager.get_user(user_id)
        if not user:
            flash('User not found.', 'error')
            return redirect(url_for('auth.list_users'))

        if request.method == 'POST':
            email = request.form.get('email', '').strip()
            role = request.form.get('role', user.role)
            is_active = request.form.get('is_active') == 'on'

            try:
                auth_manager.update_user(user_id, email=email, role=role, is_active=is_active)
                flash('User updated successfully.', 'success')
                return redirect(url_for('auth.list_users'))
            except ValueError as e:
                flash(str(e), 'error')

        return render_template('auth/user_form.html', user=user, roles=['admin', 'manager', 'analyst', 'viewer'])

    @auth_bp.route('/users/<user_id>/reset-password', methods=['POST'])
    @login_required
    @admin_required
    def reset_user_password(user_id):
        user = auth_manager.get_user(user_id)
        if not user:
            flash('User not found.', 'error')
            return redirect(url_for('auth.list_users'))

        new_password = request.form.get('new_password', '')

        if len(new_password) < 8:
            flash('Password must be at least 8 characters.', 'error')
        else:
            try:
                auth_manager.reset_password(user_id, new_password)
                flash(f'Password reset for {user.username}.', 'success')
            except ValueError as e:
                flash(str(e), 'error')

        return redirect(url_for('auth.edit_user', user_id=user_id))

    @auth_bp.route('/users/<user_id>/delete', methods=['POST'])
    @login_required
    @admin_required
    def delete_user(user_id):
        if user_id == current_user.id:
            flash('You cannot delete your own account.', 'error')
            return redirect(url_for('auth.list_users'))

        user = auth_manager.get_user(user_id)
        if user:
            auth_manager.delete_user(user_id)
            flash(f'User {user.username} deleted.', 'success')
        else:
            flash('User not found.', 'error')

        return redirect(url_for('auth.list_users'))

    # =========================================================================
    # API ENDPOINTS
    # =========================================================================

    @auth_bp.route('/api/users')
    @login_required
    @admin_required
    def api_list_users():
        users = auth_manager.list_users()
        return jsonify([{
            'id': u.id,
            'username': u.username,
            'email': u.email,
            'role': u.role,
            'is_active': u.is_active,
            'last_login': u.last_login.isoformat() if u.last_login else None
        } for u in users])

    @auth_bp.route('/api/users', methods=['POST'])
    @login_required
    @admin_required
    def api_create_user():
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        try:
            user = auth_manager.create_user(
                data.get('username', ''),
                data.get('email', ''),
                data.get('password', ''),
                data.get('role', 'viewer')
            )
            return jsonify({
                'id': user.id,
                'username': user.username,
                'message': 'User created successfully'
            }), 201
        except ValueError as e:
            return jsonify({'error': str(e)}), 400

    @auth_bp.route('/api/users/<user_id>', methods=['DELETE'])
    @login_required
    @admin_required
    def api_delete_user(user_id):
        if user_id == current_user.id:
            return jsonify({'error': 'Cannot delete your own account'}), 400

        if auth_manager.delete_user(user_id):
            return jsonify({'message': 'User deleted'})
        return jsonify({'error': 'User not found'}), 404

    # Register blueprint
    app.register_blueprint(auth_bp)

    return auth_bp
