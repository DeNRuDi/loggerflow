#  \     \
#  _\_____\
# | |   __  \___       /     __     __    __   ___   ___   ----         __
# | |  |__/     |     /    /   /  / __  / __  /__   /  /  /___  /     /   /   /  /  /
# | |      ____/     /___ /___/  /___/ /___/ /___  /     /     /___  /___/   /__/__/
# |_|_____/

from loggerflow.utils.handler import LoggingHandler
from loggerflow.backends.filters import Filter
from typing import Union

import threading
import traceback
import logging
import sys


class LoggerFlow(Filter):
    def __init__(self, project_name: str, backend, disable: bool = False, thread_logging: bool = True):
        self.project_name = project_name
        self.original_stdout = sys.stdout
        self.thread_logging = thread_logging
        self.backends = backend
        self.disable = disable

    def write(self, text):
        if not any(note in text for note in self.traceback_filters):
            self.original_stdout.write(text)

        if not self.disable:
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
        print("".join(traceback.format_exception(exctype, value, tb)))

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



