#  \     \
#  _\_____\
# | |   __  \___       /     __     __    __   ___   ___   ----         __
# | |  |__/     |     /    /   /  / __  / __  /__   /  /  /___  /     /   /   /  /  /
# | |      ____/     /___ /___/  /___/ /___/ /___  /     /     /___  /___/   /__/__/
# |_|_____/
# DeNRuDi - 2023 (c) Copyright
# BSD 3-Clause License

from loggerflow.utils.stack_cleaner import StackCleaner
from loggerflow.utils.handler import LoggingHandler
from loggerflow.backends.filters import Filter
from loggerflow.backends import Backend

from traceback import format_exception
from typing import Union, Literal

import threading
import logging
import sys


class LoggerFlow(Filter):
    def __init__(self, project_name: str, backend: Backend, disable: bool = False,
                 traceback: Literal['full', 'clean', 'minimal'] = 'full', **kwargs):
        """
        :param project_name: Name of your project
        :param backend: Backend for sending traceback logging
        :param disable: Disable LoggerFlow: if need to disable LoggerFlow completely and don`t sending traceback logging
        :param thread_logging: Enable thread logging - if need to sending traceback logs from threads
        :param traceback: Send full, clean (without built-in libraries tracebacks), short (1 line) traceback

        Library for sending traceback logs.

        Currently supported 2 backends::

            from loggerflow.backends.telegram import TelegramBackend
            from loggerflow.backends.discord import DiscordBackend
        Backends can be combined into a list - then the stacktrace will be sent to several backends at once.

        LoggerFlow supports 3 levels of send traceback logging::

            traceback='full'
        Sending full traceback on your backend/backends;

            traceback='clean'
        Sending your program's stacktrace (clearing lines that were are called from libraries);

            traceback='minimal'
        Sending a 1 line with name file, number line and last line of your traceback;
        """

        self.project_name = project_name
        self.original_stdout = sys.stdout
        self._traceback = traceback
        self.thread_logging = True
        self.backends = backend
        self.disable = disable
        self._cleaner = StackCleaner()

        if 'thread_logging' in kwargs and isinstance(kwargs['thread_logging'], bool):
            self.thread_logging = kwargs['thread_logging']

    def write(self, text):
        if not any(note in text for note in self.traceback_filters):
            self.original_stdout.write(text)

        if not self.disable:
            if 'Traceback (most recent call last):' in text:
                if self._traceback == 'clean':
                    text = self._cleaner.clean_traceback(text)
                if self._traceback == 'minimal':
                    text = self._cleaner.clean_traceback(text, minimal=True)

                if isinstance(self.backends, list):
                    for backend in self.backends:
                        backend.write_flow(text, self.project_name)
                else:
                    self.backends.write_flow(text, self.project_name)

    def flush(self):
        self.original_stdout.flush()

    def exclude_output_tb_filter(self, filter_: Union[str, list]):
        """
        Exclude a filter if you need to avoid double stacktrace output (for example, if used non-standard logging)
        """
        if isinstance(filter_, str):
            self.traceback_filters.append(filter_)
        elif isinstance(filter_, list):
            self.traceback_filters.extend(filter_)

    def exclude_sending_filter(self, filter_: Union[str, list]):
        """
        Exclude filter from sending to telegram
        """
        if isinstance(filter_, str):
            self.filters.append(filter_)
        elif isinstance(filter_, list):
            self.filters.extend(filter_)

    @staticmethod
    def _except_hook(exctype, value, tb):
        print("".join(format_exception(exctype, value, tb)))

    def _thread_excepthook(self, args):
        exctype, value, tb = args.exc_type, args.exc_value, args.exc_traceback
        self._except_hook(exctype, value, tb)

    def run(self):
        if not self.disable:
            logging_handler = LoggingHandler(self)
            sys.excepthook = self._except_hook
            if self.thread_logging:
                threading.excepthook = self._thread_excepthook
            sys.stdout = self
            logging_handler.setLevel(logging.ERROR)
            logging.getLogger().addHandler(logging_handler)
