from flask import Blueprint

from app.test.controller import test

TEST_BLUEPRINT = Blueprint('test', __name__, url_prefix="/test")

TEST_BLUEPRINT.add_url_rule("/test", "test", view_func=test, methods=["GET"])