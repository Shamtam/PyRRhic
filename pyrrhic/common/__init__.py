import logging
import os

from datetime import datetime

_prefs_dir = os.path.join(os.path.expanduser('~'), '.pyrrhic')
_prefs_file = os.path.join(_prefs_dir, 'prefs')

_logs_dir = os.path.join(_prefs_dir, 'logs')
_log_file = os.path.join(_logs_dir, '{}.log'.format(
    datetime.now().strftime('%Y%m%d_%H%M%S')
))

if not os.path.exists(_prefs_dir):
    os.makedirs(_prefs_dir)

if not os.path.exists(_logs_dir):
    os.makedirs(_logs_dir)
