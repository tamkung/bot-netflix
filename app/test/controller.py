
from flask import jsonify, request

from config import CONFIG as ENV_CONFIG


def test():
    user_id = request.headers.get("X-Consumer-Custom-Id", None)
    username = request.headers.get("X-Consumer-Username", None)
    print(user_id)
    if user_id is None:
        user_id=""
    print("test")
    return jsonify({
        "status": "success",
        "message": "hello ticket",
        "user_id": user_id,
        "username": username
    }), 200