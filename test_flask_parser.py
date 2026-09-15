import pytest
from backend.parsers.flask_parser import FlaskParser


def test_flask_parser_can_parse():
    parser = FlaskParser()
    assert parser.can_parse("app.py", "from flask import Flask\napp = Flask(__name__)") is True
    assert parser.can_parse("script.py", "print('hello world')") is False


def test_flask_endpoint_extraction():
    code = """
from flask import Flask, Blueprint, jsonify, request
app = Flask(__name__)
bp = Blueprint('users', __name__, url_prefix='/users')

@app.route('/status', methods=['GET'])
def status():
    \"\"\"System status check.\"\"\"
    return jsonify({"status": "ok"})

@bp.route('/<int:user_id>', methods=['GET'])
def get_user(user_id):
    \"\"\"Fetch user profile.\"\"\"
    return jsonify({"id": user_id})

@bp.route('/', methods=['POST'])
def create_user():
    \"\"\"Create user profile.\"\"\"
    return jsonify({"id": 1}), 201

app.register_blueprint(bp)
"""
    parser = FlaskParser()
    endpoints = parser.parse("flask_app.py", code)

    assert len(endpoints) == 3

    status_ep = next(ep for ep in endpoints if ep.path == "/status")
    assert status_ep.method == "GET"
    assert status_ep.docstring == "System status check."

    get_user_ep = next(ep for ep in endpoints if ep.path == "/users/{user_id}")
    assert get_user_ep.method == "GET"
    param = get_user_ep.parameters[0]
    assert param.name == "user_id"
    assert param.type == "integer"
    assert param.location == "path"

    create_ep = next(ep for ep in endpoints if ep.path == "/users")
    assert create_ep.method == "POST"
    assert create_ep.request_body is not None
