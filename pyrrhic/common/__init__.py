import logging
import os

from datetime import datetime

_logger = logging.getLogger(__name__)
_prefs_dir = os.path.join(os.path.expanduser('~'), '.pyrrhic')
_prefs_file = os.path.join(_prefs_dir, 'prefs')
_log_file = os.path.join(_prefs_dir, '{}.log'.format(
    datetime.now().strftime('%Y%M%d_%H%M%S')
))

if not os.path.exists(_prefs_dir):
    os.makedirs(_prefs_dir)
