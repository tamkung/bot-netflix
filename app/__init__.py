import os
import gevent
import wtforms_json
import logging
import pytz
import uwsgi
from datetime import datetime
from config import CONFIG as ENV_CONFIG
from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from gevent import monkey
from flask_apscheduler import APScheduler


monkey.patch_all(ssl=False, thread=False)

SQL_DB = SQLAlchemy()
SCHEDULER = APScheduler()
SERVICE_NAME = "backend"

BASEDIR = os.path.abspath(os.path.dirname(__file__))
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(process)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S %Z00",
)
LOGGER = logging.getLogger("python-logstash-logger")
LOGGER.setLevel(logging.INFO)

CURRENT_NOW = datetime.now(pytz.utc)


def convertStringToBoolean(string_bool):
    # Convert string to Boolean(first char in string is equal T)
    if str(string_bool)[:1].upper() == "T":
        return True
    else:
        return False


def createApp():
    app = Flask(__name__)
    app.config.from_object(ENV_CONFIG)
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SQLALCHEMY_POOL_SIZE"] = 20
    app.config["SQLALCHEMY_POOL_TIMEOUT"] = 10
    app.config["SQLALCHEMY_POOL_RECYCLE"] = 30
    app.config["WTF_CSRF_ENABLED"] = convertStringToBoolean(ENV_CONFIG.WTF_CSRF_ENABLED)
    # not using sqlalchemy event system, hence disabling it
    ENV_CONFIG.init_app(app)

    # Set up extensions
    SQL_DB.app = app
    SQL_DB.init_app(app)
    wtforms_json.init()
    CORS(app)

    with app.app_context():
        SCHEDULER.init_app(app)

    # create directory tmp
    try:
        # Create target Directory
        os.mkdir("tmp")
    except FileExistsError:
        pass

    from app.test import TEST_BLUEPRINT
    from app.mail import MAIL_BLUEPRINT

    app.register_blueprint(TEST_BLUEPRINT)
    app.register_blueprint(MAIL_BLUEPRINT)

    if ENV_CONFIG.DEBUG == "True":
        ENV_CONFIG.DEBUG = True
    else:
        ENV_CONFIG.DEBUG = False

    print(CURRENT_NOW)

    # start schedule
    from app.mail.controller import receiveMailAllFolder
    if uwsgi.worker_id()==1:
        SCHEDULER.add_job(func=receiveMailAllFolder, trigger="interval", id="email_receiver", name="email_receiver", seconds=5, replace_existing=True, max_instances=10)
        SCHEDULER.start()

    return app
