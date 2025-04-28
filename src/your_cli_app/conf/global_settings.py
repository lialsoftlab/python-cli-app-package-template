"""Global and default settings module."""
import logging
import tempfile

# General level for all log messages.
LOG_LEVEL = logging.WARNING

# Log file name and level for log messages going to it.
LOG_FILE_NAME = ''
LOG_FILE_LEVEL = logging.WARNING

# PID-file path and name.
PID_FILE_PATH = tempfile.gettempdir()
PID_FILE_NAME = "your_cli_app.pid"
