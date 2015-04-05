#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
from flask.ext.script import Manager, Shell, Server

from p13n import app

HERE = os.path.abspath(os.path.dirname(__file__))
TEST_PATH = os.path.join(HERE, 'tests')

manager = Manager(app)


def _make_context():
    """Return context dict for a shell session."""
    return {'app': app}


@manager.command
def test():
    """Run the tests."""
    import pytest
    exit_code = pytest.main([TEST_PATH, '--verbose'])
    return exit_code

manager.add_command('server', Server(host=app.config.get('LISTEN_HOST'), port=app.config.get('LISTEN_PORT')))
manager.add_command('shell', Shell(make_context=_make_context))

if __name__ == '__main__':
    manager.run()
