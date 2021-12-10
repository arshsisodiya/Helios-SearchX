import logging
import re
import threading
import time
import math

from bot import dispatcher
from telegram.ext import CallbackQueryHandler

LOGGER = logging.getLogger(__name__)


URL_REGEX = r"(?:(?:https?|ftp):\/\/)?[\w/\-?=%.]+\.[\w/\-?=%.]+"

COUNT = 0
PAGE_NO = 1
SIZE_UNITS = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
def get_readable_file_size(size_in_bytes) -> str:
    if size_in_bytes is None:
        return '0B'
    index = 0
    while size_in_bytes >= 1024:
        size_in_bytes /= 1024
        index += 1
    try:
        return f'{round(size_in_bytes, 2)}{SIZE_UNITS[index]}'
    except IndexError:
        return 'File too large'

