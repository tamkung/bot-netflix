from flask import Blueprint

from app.mail.controller import receiveMailAllFolder

MAIL_BLUEPRINT = Blueprint('email', __name__, url_prefix="/email")

MAIL_BLUEPRINT.add_url_rule("", "receiveMailAllFolder", view_func=receiveMailAllFolder, methods=["GET"])