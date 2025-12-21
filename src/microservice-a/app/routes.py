from flask import Blueprint, render_template, jsonify, request, redirect, url_for
from flask_login import login_required, current_user
from app.services.database import get_db_connection
import logging

logger = logging.getLogger(__name__)

main_bp = Blueprint('main', __name__)
auth_bp = Blueprint('auth', __name__)
api_bp = Blueprint('api', __name__)

@main_bp.route('/')
def index():
    return render_template('index.html')

@main_bp.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', user=current_user)

@api_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for Kubernetes"""
    try:
        # Verificar conexión a BD
        conn = get_db_connection()
        conn.execute('SELECT 1')
        return jsonify({
            'status': 'healthy',
            'service': 'microservice-a',
            'timestamp': datetime.utcnow().isoformat()
        }), 200
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 503

@api_bp.route('/users', methods=['GET'])
@login_required
def get_users():
    """API endpoint para obtener usuarios"""
    conn = get_db_connection()
    users = conn.execute('SELECT * FROM users').fetchall()
    return jsonify([dict(user) for user in users])

@api_bp.route('/data', methods=['POST'])
@login_required
def process_data():
    """Endpoint para procesar datos"""
    data = request.get_json()
    # Lógica de negocio aquí
    result = {"processed": True, "data": data}
    return jsonify(result), 201

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    # Implementar lógica de login
    pass

@auth_bp.route('/logout')
def logout():
    # Implementar logout
    pass
