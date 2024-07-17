"""
Пакет сборки и хранения настроек приложения.

Пакет считывает значения настроек приложения в соответствии со следующим порядком приоритетов:
    1. Переменная окружения среды приложения.
    2. Значения переменных окружения из .env-файлов.
    3. Модуль локальных настроек приложения (имя модуля заданное в GP_LOGS_TRANSMITTER_SETTINGS)
    4. Модуль глобальных настроек приложения (your_cli_app.conf.global_settings)
Агрегированные настройки доступны как объект singleton-класса conf.Settings, для удобства имеется глобальная
переменная conf.settings с экземпляром данного объекта.
"""
import importlib
import logging
import os

from dotenv import dotenv_values

from ..singleton import Singleton
from ..conf import global_settings


logger = logging.getLogger(__name__)


# Имя переменной окружения в которой возможно указать название модуля с локальными настройками.
LOCAL_SETTINGS_ENV_VAR = "YOUR_CLI_APP_SETTINGS"


class Settings(metaclass=Singleton):
    """Класс агрегирующий значения настроек из разных источников в свойства с режимом только для чтения."""

    @staticmethod
    def _make_value_property_lambda(value):
        return property(fget=lambda _self: value)

    def _load_global_settings(self):
        """Загрузить все возможные настройки и их значения из модуля conf.global_settings."""
        for setting in dir(global_settings):
            if setting.isupper():
                setattr(self, f"_{setting}", getattr(global_settings, setting))

    def _load_local_settings(self):
        """Загрузить настройки и их значения из модуля локальных настроек указанного в переменной окружения."""
        if settings_module := os.environ.get(LOCAL_SETTINGS_ENV_VAR):
            local_settings = importlib.import_module(settings_module)
            for setting in dir(local_settings):
                if setting.isupper():
                    setattr(self, f"_{setting}", getattr(local_settings, setting))

    @staticmethod
    def _transform_if_log_level(setting, value, where):
        if setting in ("LOG_LEVEL", "LOG_FILE_LEVEL") and isinstance(value, str):
            log_level = getattr(logging, value.upper(), None)
            if isinstance(log_level, int):
                return log_level
            else:
                logger.warning(f"В {where} указано неверное имя уровня журналирования {setting}: {value}!")
        else:
            return value

    def _try_set_new_value(self, setting_type, setting, value, where):
        try:
            setattr(self, f"_{setting}", setting_type(value))
        except ValueError:
            logger.error(f"Неподходящее значение '{value}' для параметра настройки '{setting}' в {where}!")
            raise

    def _load_dot_env_settings(self):
        """Загрузить настройки из .env файла."""
        for setting, value in dotenv_values().items():
            if setting.isupper():
                setting_type = str
                # Если настройка была ранее загружена из модуля глобальных или локальных настроек, то применяем её тип.
                if f"_{setting}" in dir(self):
                    setting_type = type(getattr(self, f"_{setting}"))

                value = Settings._transform_if_log_level(setting, value, ".env-файле")
                self._try_set_new_value(setting_type, setting, value, ".env-файле")

    def _try_load_form_app_env_var(self, setting: str):
        """Загрузить значения настроек из переменных окружения, если таковые определены."""
        if setting in os.environ:
            # Получаем и применяем ранее установленный в глобальных или локальных настройка тип значения.
            setting_type = type(getattr(self, f"_{setting}"))

            value = os.environ[setting]
            value = Settings._transform_if_log_level(setting, value, "переменной окружения среды")
            self._try_set_new_value(setting_type, setting, value, "переменной окружения среды")

    def __init__(self):
        self._load_global_settings()
        self._load_local_settings()
        self._load_dot_env_settings()

        # Перебираем все атрибуты данного объекта и отбираем приватные атрибуты с настройками.
        for attr in dir(self):
            if len(attr) > 1 and attr[0] == '_' and (setting := attr[1:]).isupper():
                self._try_load_form_app_env_var(setting)

                # Трансформируем приватные аттрибуты с настройками в get-свойства класса.
                value = getattr(self, f"_{setting}")
                delattr(self, f"_{setting}")
                setattr(Settings, setting, Settings._make_value_property_lambda(value))


settings = Settings()
