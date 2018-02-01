# -*- coding: utf-8 -*-

"""
Tests! Yay!
"""

# standard library
import os.path
import sys

# related
import pytest


if __name__ == '__main__':

    tests_base_path = os.path.join(os.path.dirname(__file__))


    pytest_params = [
        '-s'  # do not capture stdout/stderr
    ]

    tests = [
        'admin_client_test.py',
        'packet_test.py',
        'protocol_test.py',
        'session_test.py',
    ]
    tests = [os.path.join(tests_base_path, t) for t in tests]

    pytest.main(pytest_params + sys.argv[1:] + tests)
