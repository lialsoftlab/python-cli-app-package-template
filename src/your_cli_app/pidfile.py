import errno
import os
import signal
import logging

from your_cli_app.conf import settings

logger = logging.getLogger(__name__)


class PidFileContext:
    def __init__(self, path=f"{settings.PID_FILE_PATH}/{settings.PID_FILE_NAME}"):
        self.pid_file = path
        self.pid_fd = None

    def __enter__(self):
        try:
            self.pid_fd = os.open(self.pid_file, os.O_CREAT | os.O_WRONLY | os.O_EXCL)
            logger.debug(f"Создан и заблокирован pid-файл `{self.pid_file}`.")
        except OSError as e:
            if e.errno == errno.EEXIST:
                pid = self._check()
                if pid:
                    self.pid_fd = None
                    raise ProcessAlreadyRunningException(f"Запущен другой экземпляр программы, pid = {pid}")
                else:
                    os.remove(self.pid_file)
                    logger.warning(f"Удален протухший pid-файл {self.pid_file}.")
                    self.pid_fd = os.open(self.pid_file, os.O_CREAT | os.O_WRONLY | os.O_EXCL)
                    logger.debug(f"Создан и заблокирован pid-файл `{self.pid_file}`.")
            else:
                raise

        os.write(self.pid_fd, str(os.getpid()).encode("ascii"))
        os.close(self.pid_fd)
        return self

    def __exit__(self, t, e, tb):
        # return false to raise, true to pass
        if t is None:
            # normal condition, no exception
            self._remove()
            return True
        elif t is ProcessAlreadyRunningException:
            # do not remove the other process lockfile
            return False
        else:
            # other exception
            if self.pid_fd:
                # this was our lockfile, removing
                self._remove()
            return False

    def _remove(self):
        logging.debug(f"Удаляем pid-файл `{self.pid_file}`.")
        os.remove(self.pid_file)

    def _check(self):
        """check if a process is still running the process id is expected to be in pidfile, which should exist.
        if it is still running, returns the pid, if not, return False."""
        with open(self.pid_file, 'r') as f:
            try:
                pidstr = f.read()
                pid = int(pidstr)
            except ValueError:
                # not an integer
                logger.warning(f"Из pid-файла считано значение не являющееся целым числом: {pidstr}")
                return False
            try:
                os.kill(pid, signal.SIG_DFL)
            except OSError:
                logging.debug(f"Не получилось передать сигнал SIG_DFL процессу с pid = {pid}.")
                return False
            else:
                return pid


class ProcessAlreadyRunningException(BaseException):
    pass
