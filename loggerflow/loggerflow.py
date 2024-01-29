#  \     \
#  _\_____\
# | |   __  \___       /     __     __    __   ___   ___   ----         __
# | |  |__/     |     /    /   /  / __  / __  /__   /  /  /___  /     /   /   /  /  /
# | |      ____/     /___ /___/  /___/ /___/ /___  /     /     /___  /___/   /__/__/
# |_|_____/
# DeNRuDi - 2023 (c) Copyright
# BSD 3-Clause License

from loggerflow.lifecycle.lifecycle_cli import LifecycleMixin, Lifecycle
from loggerflow.utils.stack_cleaner import StackCleaner

from loggerflow.utils.filters import Filter
from loggerflow.backends import Backend

from traceback import format_exception, format_exc
from typing import Union, Literal, Optional
from asyncio import AbstractEventLoop

import threading
import sys


class LoggerFlow(Filter, LifecycleMixin):
    def __init__(self, backend: Backend, project_name: str | None = None, disable: bool = False,
                 thread_logging: bool = True, traceback: Literal['full', 'clean', 'minimal'] = 'full'):
        """
        :param project_name: Name of your project
        :param backend: Backend for sending traceback logging
        :param disable: Disable LoggerFlow: if need to disable LoggerFlow completely and don`t sending traceback logging
        :param thread_logging: Enable thread logging - if need to sending traceback logs from threads
        :param traceback: Send full, clean (without built-in libraries tracebacks) or short (1 line) traceback

        Library for sending traceback logs.

        Currently supported 3 backends::

            from loggerflow.backends.telegram import TelegramBackend
            from loggerflow.backends.discord import DiscordBackend
            from loggerflow.backends.file import FileBackend
        Backends can be combined into a list - then the stacktrace will be sent to several backends at once.

        LoggerFlow supports 3 levels of send traceback logging::

            traceback='full'
        Sending full traceback on your backend/backends;

            traceback='clean'
        Sending your program's stacktrace (clearing lines that were are called from libraries);

            traceback='minimal'
        Sending a 1 line with name file, number line and last line of your traceback;
        """

        self.thread_logging = thread_logging
        self.project_name = project_name
        self._traceback = traceback
        self.backends = backend
        self.disable = disable
        self.loop: Optional[AbstractEventLoop] = None

        self.original_stdout = sys.stdout
        self._cleaner = StackCleaner()

        if isinstance(self.backends, list):
            for bk in self.backends:
                if isinstance(bk, Lifecycle):
                    self._create_handshake_for_lifecycle_server(bk)

        else:
            if isinstance(self.backends, Lifecycle):
                self._create_handshake_for_lifecycle_server(backend)

    def write(self, text):
        if not any(note in text for note in self.traceback_filters):
            self.original_stdout.write(text)
        if not self.disable:
            if self.loop:
                self.loop.run_until_complete(self.send_async_traceback(text))
            else:
                self.send_traceback(text)

    def exclude_output_tb_filter(self, filter_: Union[str, list]):
        """
        Exclude a filter if you need to avoid double stacktrace output (for example, if used non-standard logging)
        """
        if isinstance(filter_, str):
            self.traceback_filters.append(filter_)
        elif isinstance(filter_, list):
            self.traceback_filters.extend(filter_)

    def exclude(self, filter_: Union[str, list]):
        """
        Exclude filter from sending to backend
        """
        if isinstance(filter_, str):
            self.filters.append(filter_)
        elif isinstance(filter_, list):
            self.filters.extend(filter_)

    def __handle_traceback(self, traceback: str):
        if not traceback:
            traceback = format_exc()

        if 'Traceback (most recent call last):' in traceback:
            try:
                if self._traceback == 'clean':
                    traceback = self._cleaner.clean_traceback(traceback)
                elif self._traceback == 'minimal':
                    traceback = self._cleaner.clean_traceback(traceback, minimal=True)
            except Exception as e:
                print(f'Error in LoggerFlow at cleaning: {e}. Please create issue on GitHub and show traceback.')
        return traceback

    async def send_async_traceback(self, traceback: Optional[str] = None):
        traceback = self.__handle_traceback(traceback)
        await self.send_async_data(text=traceback)

    def send_traceback(self, traceback: Optional[str] = None):
        """
        :param traceback:
        :return:
        """
        traceback = self.__handle_traceback(traceback)
        self.send_data(text=traceback)

    async def send_async_data(self, text: str):

        if isinstance(self.backends, list):
            for backend in self.backends:
                await backend.async_write_flow(text, self.project_name)
        else:
            await self.backends.async_write_flow(text, self.project_name)

    def send_data(self, text: str):
        if isinstance(self.backends, list):
            for backend in self.backends:
                backend.write_flow(text, self.project_name)
        else:
            self.backends.write_flow(text, self.project_name)

    def flush(self):
        self.original_stdout.flush()

    def isatty(self):
        return self.original_stdout.isatty()

    @staticmethod
    def _except_hook(exctype, value, tb):
        print("".join(format_exception(exctype, value, tb)))

    def _thread_excepthook(self, args):
        exctype, value, tb = args.exc_type, args.exc_value, args.exc_traceback
        self._except_hook(exctype, value, tb)

    def run(self, loop: AbstractEventLoop = None):
        if loop:
            self.loop = loop

        if not self.disable:
            sys.excepthook = self._except_hook
            if self.thread_logging:
                threading.excepthook = self._thread_excepthook
            sys.stdout = self
