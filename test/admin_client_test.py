# -*- coding: utf-8 -*-

# standard library

# related
import pytest

# project
from admin_client import AdminClient, CallbackAppend, CallbackPrepend


@pytest.mark.parametrize('callbacks', [
    {
        1: [1, 2, 3],
        2: [4, 5, 6]
    },
])
def test_admin_client_callbacks_in_construction(callbacks):
    """Making sure callbacks are in the right order"""
    ac = AdminClient('host', 1111, callbacks=None)
    assert len(ac.callbacks) == 0, 'Unexpected callbacks'
    ac.register_callbacks(callbacks)
    for packet_type, cb_list in callbacks.items():
        assert list(ac.callbacks[packet_type]) == cb_list, 'Callbacks do not match'


@pytest.mark.parametrize('callbacks_expected', [
    [
        # #####
        [
            (1, 'cb1', CallbackAppend),
            (1, 'cb2', CallbackAppend),
            (2, 'cb3', CallbackAppend),
            (2, 'cb4', CallbackAppend),
            (1, 'cb5', CallbackAppend),

        ],
        {
            1: ['cb1', 'cb2', 'cb5'],
            2: ['cb3', 'cb4'],
        }
    ],
    [
        # #####
        [
            (1, 'cb1', CallbackPrepend),
            (1, 'cb2', CallbackPrepend),
            (2, 'cb3', CallbackPrepend),
            (2, 'cb4', CallbackPrepend),
            (1, 'cb5', 0),

        ],
        {
            1: ['cb5', 'cb2', 'cb1'],
            2: ['cb4', 'cb3'],
        }
    ],
    [
        # #####
        [
            (1, 'cb1', 99),
            (1, 'cb2', CallbackPrepend),
            (2, 'cb3', CallbackPrepend),
            (2, 'cb4', 0),
            (1, 'cb5', -1),

        ],
        {
            1: ['cb2', 'cb5', 'cb1'],
            2: ['cb4', 'cb3'],
        }
    ],
])
def test_admin_client_register_callback(callbacks_expected):
    """Testing the position of the callbacks when using register_callback()"""
    ac = AdminClient('host', 1111, callbacks=None)
    callbacks, expected = callbacks_expected
    for packet_type, callback, position in callbacks:
        ac.register_callback(packet_type, callback, position)
    for packet_type, callbacks in expected.items():
        assert ac.callbacks[packet_type] == expected[packet_type], 'Callbacks do not match'
