#!/usr/bin/env python
import os
import subprocess

from app import SQL_DB, createApp
from flask_migrate import Migrate
from flask_script import Manager, Shell

APP = createApp()
MANAGER = Manager(APP)
MIGRATE = Migrate(APP, SQL_DB)


def makeShellContext():
    return dict(app=APP, sql_db=SQL_DB)


MANAGER.add_command('shell', Shell(make_context=makeShellContext))

@MANAGER.command
def test():
    """Run the unit tests."""
    import unittest

    tests = unittest.TestLoader().discover('tests')
    unittest.TextTestRunner(verbosity=2).run(tests)


@MANAGER.command
def run():
    """Runs the set-up needed for local development."""
    APP.run(host='0.0.0.0', port=5000, debug=True, use_reloader=True)


@MANAGER.command
def setupProd():
    """Runs the set-up needed for production."""
    setupGeneral()


def setupGeneral():
    """Runs the set-up needed for both local development and production.
       Also sets up first admin user."""


@MANAGER.command
def format():
    """Runs the yapf and isort formatters over the project."""
    isort = 'isort -rc *.py app/'
    yapf = 'yapf -r -i *.py app/'

    print('Running {}'.format(isort))
    subprocess.call(isort, shell=True)

    print('Running {}'.format(yapf))
    subprocess.call(yapf, shell=True)


if __name__ == '__main__':
    MANAGER.run()
