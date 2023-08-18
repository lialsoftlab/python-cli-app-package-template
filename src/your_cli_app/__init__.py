import logging
import os
import sys


_BOOTSTRAP_GUARD = False


def bootstrap():
    """Application bootstrapping."""
    global _BOOTSTRAP_GUARD

    if _BOOTSTRAP_GUARD:
        return

    logger = logging.getLogger()
    formatter = logging.Formatter('%(asctime)s:%(name)s:%(levelname)s: %(message)s')
    if not logger.handlers:
        ch = logging.StreamHandler()
        ch.setFormatter(formatter)
        logger.addHandler(ch)
    else:
        logger.handlers[0].setFormatter(formatter)

    # Appending the current directory from which application has started into module search path to boost up it
    # priority when searching for application settings files and modules.
    sys.path.insert(0, os.getcwd())
    from .conf import settings

    logger.setLevel(settings.LOG_LEVEL)

    if settings.LOG_FILE_NAME:
        fh = logging.FileHandler(settings.LOG_FILE_NAME, encoding="utf-8")
        fh.setLevel(settings.LOG_FILE_LEVEL)
        fh.setFormatter(logging.Formatter('%(asctime)s:%(name)s:%(levelname)s: %(message)s'))
        logger.addHandler(fh)

    _BOOTSTRAP_GUARD = True


bootstrap()
