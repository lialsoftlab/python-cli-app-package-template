"""Модуль глобальных/дефолтных настроек программы."""
import logging
import tempfile

# Общий уровень записи сообщений в журнал.
LOG_LEVEL = logging.WARNING

# Имя файла с журналом сообщений и уровень записи сообщений в файл журнала.
LOG_FILE_NAME = ''
LOG_FILE_LEVEL = logging.WARNING

# Путь к PID-файлу.
PID_FILE_PATH = tempfile.gettempdir()
PID_FILE_NAME = "your_cli_app.pid"