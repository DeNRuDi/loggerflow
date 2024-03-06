#  \     \
#  _\_____\
# | |   __  \___       /     __     __    __   ___   ___   ----         __
# | |  |__/     |     /    /   /  / __  / __  /__   /  /  /___  /     /   /   /  /  /
# | |      ____/     /___ /___/  /___/ /___/ /___  /     /     /___  /___/   /__/__/
# |_|_____/
# DeNRuDi - 2024 (c) Copyright
# BSD 3-Clause License

from loggerflow.lifecycle import WebhookLifecycle, WebSocketLifecycle
from loggerflow.lifecycle.lifecycle_cli import Lifecycle

from loggerflow.utils.stack_cleaner import StackCleaner

from loggerflow.utils.filters import Filter
from loggerflow.backends import Backend

from traceback import format_exception, format_exc
from typing import Union, Literal, Optional

import threading
import asyncio
import sys


LIFECYCLE_BACKENDS = (WebhookLifecycle, WebSocketLifecycle)
LifecycleBackend = Union[WebhookLifecycle, WebSocketLifecycle]


class LoggerFlow(Filter):

    def __init__(self, project_name: str, backend: Backend,  disable: bool = False,
                 thread_logging: bool = True, traceback: Literal['full', 'clean', 'minimal'] = 'full'):
        """
        :param project_name: Name of your project
        :param backend: Backend for sending traceback logging
        :param disable: Disable LoggerFlow: if need to disable LoggerFlow completely and don`t sending traceback logging
        :param thread_logging: Enable thread logging - if need to sending traceback logs from threads
        :param traceback: Send full, clean (without built-in libraries tracebacks) or short (1 line) traceback

        Library for sending traceback logs.

        Currently supported 5 backends::

            from loggerflow.backends import TelegramBackend
            from loggerflow.backends import DiscordBackend
            from loggerflow.backends import FileBackend
            from loggerflow.lifecycle import WebhookLifecycle, WebSocketLifecycle

        Backends can be combined into a list - then the stacktrace will be sent to several backends at once.

        LoggerFlow supports 3 levels of send traceback logging::

            traceback='full'
        Sending full traceback on your backend/backends;

            traceback='clean'
        Sending your program's stacktrace (clearing lines that were are called from libraries);

            traceback='minimal'
        Sending a 1 line with name file, number line and last line of your traceback;

        Lifecycle

        Working with lifecycle helps you track the state of your application, app heartbeat, as well as
        convenient display errors on the web page with a cleaned stacktrace if desired.
        """

        self.thread_logging = thread_logging
        self.project_name = project_name
        self._traceback = traceback
        self.backends = backend
        self.disable = disable

        self.original_stdout = sys.stdout
        self._cleaner = StackCleaner()

        if isinstance(self.backends, list):
            for bk in self.backends:
                if isinstance(bk, LIFECYCLE_BACKENDS):
                    self._init_lifecycle(bk)
        else:
            if isinstance(self.backends, LIFECYCLE_BACKENDS):
                self._init_lifecycle(self.backends)

    def _init_lifecycle(self, backend: LifecycleBackend):
        if not self.disable:
            backend_info = self._get_backend_info(backend)
            backend.create_lifecycle(backend_info)

    def _get_backend_info(self, lf_backend: LifecycleBackend) -> dict:
        if isinstance(self.backends, list):
            connected_backends = ', '.join(
                [bk.__class__.__name__ for bk in self.backends if not isinstance(bk, Lifecycle)]
            )
            all_authors = []
            for bk in self.backends:
                if hasattr(bk, 'authors') and not isinstance(bk, Lifecycle):
                    if bk.authors:
                        all_authors.extend(bk.authors)
            all_authors = ', '.join(all_authors)

        else:
            connected_backends = self.backends.__class__.__name__ if not isinstance(self.backends, Lifecycle) else ''
            if not isinstance(self.backends, Lifecycle) and hasattr(self.backends, 'authors'):
                all_authors = ', '.join(self.backends.authors)
            else:
                all_authors = ''

        backend_info = {
            'project_name': self.project_name,
            'connected_backends': connected_backends,
            'traceback': self._traceback,
            'implementation': lf_backend.implementation,
            'heartbeat': lf_backend.heartbeat if hasattr(lf_backend, 'heartbeat') else None,
            'last_readings': lf_backend.get_client_readings(),
            'authors': all_authors
        }
        return backend_info

    def write(self, text: str):
        if not any(note in text for note in self.traceback_filters):
            self.original_stdout.write(text)

        if not self.disable:
            self.send_traceback(text)

    def add_backend(self, backend: Backend):
        if isinstance(self.backends, list) and backend not in self.backends:
            if isinstance(backend, LIFECYCLE_BACKENDS):
                self._init_lifecycle(backend)
            self.backends.append(backend)

        elif self.backends != backend:
            if isinstance(backend, LIFECYCLE_BACKENDS):
                self._init_lifecycle(backend)
            self.backends = [self.backends, backend]

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

    def __handle_traceback(self, traceback: Optional[str] = None, clean: bool = True):
        if not traceback:
            traceback = format_exc()
        traceback = traceback[:-1]

        if not clean:
            return traceback

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
        if not any(note in traceback for note in self.filters):
            new_traceback = self.__handle_traceback(traceback)
            if new_traceback:
                await self.send_async_data(text=new_traceback)

            lifecycle_traceback = self.__handle_traceback(traceback, clean=False)
            if lifecycle_traceback:
                self._check_and_send_data_to_lifecycle(lifecycle_traceback)

    def send_traceback(self, traceback: Optional[str] = None):
        """Send any data to your traceback"""
        if not any(note in traceback for note in self.filters):
            new_traceback = self.__handle_traceback(traceback)
            if new_traceback:
                self.send_data(text=new_traceback)

            lifecycle_traceback = self.__handle_traceback(traceback, clean=False)
            if lifecycle_traceback:
                self._check_and_send_data_to_lifecycle(lifecycle_traceback)

    async def send_async_data(self, text: str):
        """Async send data to your traceback"""
        if isinstance(self.backends, list):
            for backend in self.backends:
                if not isinstance(backend, LIFECYCLE_BACKENDS):
                    await backend.async_write_flow(text, self.project_name)
        else:
            if not isinstance(self.backends, LIFECYCLE_BACKENDS):
                await self.backends.async_write_flow(text, self.project_name)

    def _check_and_send_data_to_lifecycle(self, text: str):
        if isinstance(self.backends, list):
            for bk in self.backends:
                if isinstance(bk, LIFECYCLE_BACKENDS):
                    self._send_data_to_lifecycle(bk, text)
        else:
            if isinstance(self.backends, LIFECYCLE_BACKENDS):
                self._send_data_to_lifecycle(self.backends, text)

    def _send_data_to_lifecycle(self, lf_backend: LifecycleBackend, text: str):
        if lf_backend.loop:
            if lf_backend.wait_send:
                send_event = threading.Event()
                asyncio.run_coroutine_threadsafe(
                    lf_backend.async_write_flow(text, self.project_name, send_event=send_event),
                    lf_backend.loop
                )
                send_event.wait(timeout=lf_backend.send_timeout)
            else:
                asyncio.run_coroutine_threadsafe(
                    lf_backend.async_write_flow(text, self.project_name),
                    lf_backend.loop
                )

    def send_data(self, text: str):
        if isinstance(self.backends, list):
            for backend in self.backends:
                if not isinstance(backend, LIFECYCLE_BACKENDS):
                    backend.write_flow(text, self.project_name)
        else:
            if not isinstance(self.backends, LIFECYCLE_BACKENDS):
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

    def run(self):
        if not self.disable:
            sys.excepthook = self._except_hook
            if self.thread_logging:
                threading.excepthook = self._thread_excepthook
            sys.stdout = self
