import os

BASEDIR = os.path.abspath(os.path.dirname(__file__))

if os.path.exists('.env'):
    print('Importing environment from .env file')
    for line in open('.env'):
        var = line.strip().split('=')
        if len(var) == 2:
            os.environ[var[0]] = var[1].replace("\"", "")


def getMultiDBConnURL(data_env, default_env):
    if data_env:
        if "," in data_env:
            list_env_url = data_env.split(",")
            env_url = {}
            for data_env_url in list_env_url:
                env_url_split = data_env_url.split("/")
                env_url[env_url_split[3]] = data_env_url
        else:
            env_url_split = data_env.split("/")
            env_url = {
                env_url_split[3]: data_env
            }
    elif default_env in (None, "") or data_env in (None, ""):
        return None
    else:
        env_url_split = default_env.split("/")
        env_url = {
            env_url_split[3]: default_env
        }
    return env_url


class Config(object):
    APP_NAME = os.environ.get('APP_NAME') or 'Flask-Base'
    FLASK_ENVIRONMENT = os.environ.get('FLASK_ENVIRONMENT')

    if FLASK_ENVIRONMENT != "production":
        DEBUG = os.environ.get('DEBUG') or False
    else:
        DEBUG = False

    if os.environ.get('SECRET_KEY'):
        SECRET_KEY = os.environ.get('SECRET_KEY')
    else:
        SECRET_KEY = 'SECRET_KEY_ENV_VAR_NOT_SET'
        print('SECRET KEY ENV VAR NOT SET! SHOULD NOT SEE IN PRODUCTION')

    if os.environ.get('DATABASE_URL'):
        SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL_DEFAULT')
        SQLALCHEMY_BINDS = getMultiDBConnURL(
            data_env=os.environ.get('DATABASE_URL'),
            # Openstack config
            default_env=None
        )
    else:
        SQLALCHEMY_DATABASE_URI = 'SQLALCHEMY_DATABASE_URI_ENV_VAR_NOT_SET'
        print('SQLALCHEMY_DATABASE_URI ENV VAR NOT SET! SHOULD NOT SEE IN PRODUCTION')
    SSL_DISABLE = (os.environ.get('SSL_DISABLE') or 'True') == 'True'
    WTF_CSRF_ENABLED = os.environ.get('WTF_CSRF_ENABLED') or False
    DATABASE_URL = os.environ.get("DATABASE_URL")
    IMAP_HOST = os.environ.get('IMAP_HOST')
    IMAP_PORT = os.environ.get('IMAP_PORT')
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    SMTP_HOST = os.environ.get('SMTP_HOST')
    SMTP_PORT = os.environ.get('SMTP_PORT')
    AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
    S3_REGION_NAME = os.environ.get('S3_REGION_NAME')
    S3_BUCKET_NAME = os.environ.get('S3_BUCKET_NAME')
    S3_ENDPOINT_URL = os.environ.get('S3_ENDPOINT_URL')

    SCHEDULER_EXECUTORS = {
        'default': {'type': 'threadpool', 'max_workers': 1}
    }

    SCHEDULER_JOB_DEFAULTS = {
        'coalesce': False,
        'max_instances': 1
    }

    SCHEDULER_API_ENABLED = True

    @staticmethod
    def init_app(app):
        print('THIS APP IS IN ' + str(app.config['FLASK_ENVIRONMENT']).upper() + ' MODE. \
                YOU SHOULD NOT SEE THIS IN PRODUCTION.')


CONFIG = Config
