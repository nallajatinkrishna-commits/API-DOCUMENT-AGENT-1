"""
Sample Flask Application for testing API Documentation Agent.
Demonstrates Blueprints, path converters (<int:id>), methods lists, and auth decorators.
"""

from functools import wraps
from flask import Flask, Blueprint, jsonify, request

app = Flask(__name__)

# Auth Decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)

    return decorated_function


# Blueprints
auth_bp = Blueprint("auth", __name__, url_prefix="/auth")
api_bp = Blueprint("api", __name__, url_prefix="/api/v1")


@app.route("/")
def index():
    """
    Public index status check.
    """
    return jsonify({"status": "Flask API operational", "version": "1.0"})


@auth_bp.route("/login", methods=["POST"])
def login():
    """
    Authenticate user credentials and return JWT session token.
    Expects email and password in JSON payload.
    """
    data = request.get_json() or {}
    email = data.get("email")
    return jsonify({"token": "jwt_token_sample", "email": email})


@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    """
    Revoke current user session token.
    """
    return jsonify({"message": "Successfully logged out"})


@api_bp.route("/items", methods=["GET"])
def get_items():
    """
    Get list of catalog items with optional page and limit query parameters.
    """
    page = request.args.get("page", 1, type=int)
    return jsonify({"items": [{"id": 1, "title": "Widget A"}], "page": page})


@api_bp.route("/items/<int:item_id>", methods=["GET"])
def get_item_by_id(item_id):
    """
    Fetch catalog item details by integer ID.
    """
    return jsonify({"id": item_id, "title": "Widget A", "price": 29.99})


@api_bp.route("/items", methods=["POST"])
@login_required
def create_item():
    """
    Create a new catalog item. Requires authentication.
    """
    data = request.get_json() or {}
    return jsonify({"id": 42, "title": data.get("title", "New Item")}), 201


@api_bp.route("/items/<int:item_id>", methods=["PUT", "PATCH"])
@login_required
def update_item(item_id):
    """
    Update catalog item attributes by ID.
    """
    return jsonify({"id": item_id, "status": "updated"})


@api_bp.route("/items/<int:item_id>", methods=["DELETE"])
@login_required
def delete_item(item_id):
    """
    Delete catalog item by ID.
    """
    return jsonify({"success": True}), 200


app.register_blueprint(auth_bp)
app.register_blueprint(api_bp)

if __name__ == "__main__":
    app.run(port=5000)
