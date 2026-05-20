from collections import defaultdict
from time import time

from flask import Blueprint, jsonify, request

bp = Blueprint("auth", __name__)

_USERS = {"alice": "secret123", "bob": "hunter2"}
_FAILED_ATTEMPTS: dict[str, list[float]] = defaultdict(list)


def _rate_limited(user: str) -> bool:
    now = time()
    _FAILED_ATTEMPTS[user] = [t for t in _FAILED_ATTEMPTS[user] if now - t < 60]
    return len(_FAILED_ATTEMPTS[user]) >= 5


@bp.route("/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    user = data.get("user", "")
    pw = data.get("password", "")

    if _rate_limited(user):
        return jsonify({"error": "too many attempts"}), 429

    if _USERS.get(user) != pw:
        _FAILED_ATTEMPTS[user].append(time())
        return jsonify({"error": "bad credentials"}), 401

    return jsonify({"token": f"session-{user}"}), 200
