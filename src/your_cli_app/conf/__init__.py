"""
Package for the application configuration settings collection and storage.

Package collect's values for the app settings with in the specified priorities order:
    1. Environment variables.
    2. Variable values from a .env-files.
    3. Local app settings module (see `LOCAL_SETTINGS_ENV_VAR`).
    4. Global/default app settings module (your_cli_app.conf.global_settings)

Collected settings are available as singleton-object of conf.Settings class. Global variable conf.settings contains
this object already created for your convenience.
"""
import importlib
import logging
import os

from dotenv import dotenv_values

from ..singleton import Singleton
from ..conf import global_settings


logger = logging.getLogger(__name__)


# Environment variable name which contains name of the local settings module (if needed).
LOCAL_SETTINGS_ENV_VAR = "YOUR_CLI_APP_SETTINGS"


class Settings(metaclass=Singleton):
    """
    Application settings class

    Collects settings values from different sources into a collection of read-only properties.
    """

    @staticmethod
    def _make_value_property_lambda(value):
        return property(fget=lambda _self: value)

    def _load_global_settings(self):
        """Load all available settings and its default values from conf.global_settings module."""
        for setting in dir(global_settings):
            if setting.isupper():
                setattr(self, f"_{setting}", getattr(global_settings, setting))

    def _load_local_settings(self):
        """Load settings from the local settings module which name specified in the specified environment variable."""
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
                logger.warning(
                    f"In the {where} was specified invalid log level {setting}: {value}! Reverting to logging.WARNING."
                )
                return logging.WARNING
        else:
            return value

    def _try_set_new_value(self, setting_type, setting, value, where):
        try:
            setattr(self, f"_{setting}", setting_type(value))
        except ValueError:
            logger.error(f"Invalid value '{value}' was specified for the '{setting}' in the {where}!")
            raise

    def _load_dot_env_settings(self):
        """Load settings from the .env-file"""
        for setting, value in dotenv_values().items():
            if setting.isupper():
                setting_type = str
                # Apply known setting type if setting was already loaded from global or local settings module.
                if f"_{setting}" in dir(self):
                    setting_type = type(getattr(self, f"_{setting}"))

                value = Settings._transform_if_log_level(setting, value, ".env-file")
                self._try_set_new_value(setting_type, setting, value, ".env-file")

    def _try_load_form_app_env_var(self, setting: str):
        """Load settings values from environment variables, if they exist."""
        if setting in os.environ:
            # Apply known setting type if setting was already loaded from global or local settings module.
            setting_type = type(getattr(self, f"_{setting}"))

            value = os.environ[setting]
            value = Settings._transform_if_log_level(setting, value, "env-var")
            self._try_set_new_value(setting_type, setting, value, "env-var")

    def __init__(self):
        self._load_global_settings()
        self._load_local_settings()
        self._load_dot_env_settings()

        for attr in dir(self):
            # Enumerate all attributes of the object and select private attributes containing settings.
            if len(attr) > 1 and attr[0] == '_' and (setting := attr[1:]).isupper():
                self._try_load_form_app_env_var(setting)

                # Transform private attribute with setting value into class-level getter.
                value = getattr(self, f"_{setting}")
                delattr(self, f"_{setting}")
                setattr(Settings, setting, Settings._make_value_property_lambda(value))


settings = Settings()
