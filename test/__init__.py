# -*- coding: utf-8 -*-

"""
Tests! Yay!
"""

# standard library
import os.path

# related
import pytest


if __name__ == '__main__':

    tests_base_path = os.path.join(os.path.dirname(__file__))


    pytest_params = [
        '-s'  # do not capture stdout/stderr
    ]

    tests = [
        os.path.join(tests_base_path, 'packet_test.py'),
        os.path.join(tests_base_path, 'protocol_test.py')
    ]

    pytest.main(pytest_params + tests)
