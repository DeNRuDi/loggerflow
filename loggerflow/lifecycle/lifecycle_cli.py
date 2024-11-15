from loggerflow.backends.abstract_backend import AbstractBackend
from loggerflow.lifecycle.utils.formatter import ColorFormatter
from loggerflow.exceptions import LifecycleException

from aiohttp import ClientWebSocketResponse, ClientSession
from typing import Optional, Union
from functools import partial
from asyncio import Task, AbstractEventLoop

import threading
import asyncio
import logging
import aiohttp
import atexit
import psutil
import time

sh = logging.StreamHandler()
sh.setLevel(logging.DEBUG)
sh.setFormatter(ColorFormatter("| LoggerFlow %(levelname)s | %(message)s"))

logger = logging.getLogger("LoggerFlow")
logger.setLevel(logging.DEBUG)
logger.addHandler(sh)


class Lifecycle:

    def __init__(self,
                 backend_url: str,
                 wait_send: bool,
                 send_timeout: int,
                 auto_release: bool = True,
                 loop: AbstractEventLoop = None):

        self.lifecycle_url = backend_url
        self.wait_send = wait_send
        self.send_timeout = send_timeout
        self.loop = loop
        self.auto_release = auto_release
        self.working_lifecycle_task: Optional[Task] = None
        self.mechanism: Optional[Union[ClientWebSocketResponse, ClientSession]] = None
        self.implementation = None

    @staticmethod
    def get_client_readings() -> dict:
        cpu_usage = psutil.cpu_percent(interval=0.1)
        memory_info = psutil.virtual_memory()
        process = psutil.Process()
        used_memory_gb = memory_info.used / (1024 ** 3)
        total_memory_gb = memory_info.total / (1024 ** 3)
        process_memory_gb = process.memory_info().rss / (1024 ** 3)

        return {
            'cpu': str(cpu_usage),
            'used_memory': f'{used_memory_gb:.2f}',
            'total_memory': f'{total_memory_gb:.2f}',
            'process_memory': f'{process_memory_gb:.2f}'
        }

    def __run_implementation_lifecycle(self, backend_info: dict, connect_event: threading.Event):
        if self.loop:
            if self.loop.is_running():
                # event loop needs to be running=True, otherwise task won't run
                asyncio.run_coroutine_threadsafe(self._connect_implementation_lifecycle(backend_info, connect_event), self.loop)
            else:
                logger.error('Your loop is not running, so LoggerFlow won\'t work, raising...')
        else:
            asyncio.run(self._connect_implementation_lifecycle(backend_info, connect_event))

    def _run_auto_release(self):
        self.release()
        logger.info('Lifecycle auto released')

    def create_lifecycle(self, backend_info: dict):
        # A daemon thread is created, in which its own event loop is initiated.
        # If the event loop has already been passed, then the coroutine is started in a thread-like manner.
        # That is, if someone passed a loop, then it operates on it itself.
        connect_event = threading.Event()
        target = partial(self.__run_implementation_lifecycle, backend_info, connect_event)
        threading.Thread(target=target, daemon=True).start()
        connect_event.wait(timeout=self.send_timeout)
        if not connect_event.is_set():
            raise LifecycleException(
                f'Lifecycle Server {self.lifecycle_url} don`t return success code, '
                f'please check that LoggerFlow Server is running.\n'
                f'You can start loggerflow using, for example, the command:\n'
                f'loggerflow run --host 127.0.0.1 --port 8000'
            )
        if self.auto_release:
            atexit.register(self._run_auto_release)

    async def _connect_implementation_lifecycle(self, backend_info: dict, event: threading.Event):
        raise NotImplementedError

    def release(self):
        logger.info('Release working lifecycle...')
        if self.working_lifecycle_task:
            loop = self.working_lifecycle_task.get_loop()
            tasks_to_cancel = []
            for task in asyncio.all_tasks(loop):
                coro = task.get_coro()
                if hasattr(coro, '__qualname__'):
                    if 'WebhookLifecycle' in coro.__qualname__ or 'WebSocketLifecycle' in coro.__qualname__:
                        tasks_to_cancel.append(task)

            for task in tasks_to_cancel:
                # time.sleep(1) is needed here because when simply running the example -
                # there is not enough time to send the result, since this is a daemon thread and the result is not expected
                time.sleep(1)
                task.cancel()

        self.mechanism = None

class WebSocketLifecycle(Lifecycle, AbstractBackend):

    def __init__(self,
                 websocket_url: str,
                 heartbeat: int = 5,
                 send_timeout: int = 5,
                 wait_send: bool = False,
                 auto_release: bool = True,
                 loop: AbstractEventLoop = None):
        super().__init__(
            backend_url=f'{websocket_url}/' if websocket_url[-1] != '/' else websocket_url,
            send_timeout=send_timeout,
            wait_send=wait_send,
            auto_release=auto_release,
            loop=loop
        )
        self.heartbeat = heartbeat
        self.implementation = 'websocket'

    def write_flow(self, text: str, project_name: str, *args, **kwargs):
        ...

    async def async_write_flow(self, text: str, project_name: str, *args, **kwargs):
        if self.mechanism and 'Traceback (most recent call last):' in text:
            data = {
                'project_name': project_name,
                'traceback': text,
                'request_path': 'project_error'
            }
            try:
                await self.mechanism.send_json(data)
            except Exception:
                self.mechanism = None

        if self.wait_send:
            send_event: threading.Event = kwargs['send_event']
            send_event.set()

    async def _connect_implementation_lifecycle(self, backend_info: dict, event: threading.Event) -> Task:
        if not self.loop:
            self.loop = asyncio.get_running_loop()
        task = asyncio.create_task(self._connect_to_websocket(backend_info, event))
        self.working_lifecycle_task = task
        return await task

    async def _connect_to_websocket(self, backend_info: dict, event: threading.Event):
        heartbeat = self.heartbeat
        try:
            while True:
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.ws_connect(self.lifecycle_url) as ws:
                            self.mechanism = ws
                            await ws.send_json(backend_info)
                            event.set()
                            heartbeat = self.heartbeat
                            logger.info(f'Connected to server socket {self.lifecycle_url}')
                            while True:
                                try:
                                    msg = await ws.receive(timeout=0.1)
                                    if msg.type == aiohttp.WSMsgType.TEXT:
                                        await ws.send_json({'status': 200})
                                    elif msg.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.ERROR):
                                        break
                                except asyncio.TimeoutError:
                                    ...
                                except Exception as e:
                                    logger.warning(f"Error: {e}")
                                    break

                                info = {
                                    'project_name': backend_info['project_name'],
                                    'last_readings': self.get_client_readings(),
                                    'request_path': 'heartbeat'
                                }
                                try:
                                    await ws.send_json(info)
                                except Exception as e:
                                    logger.warning(f"Error: {e}")

                                await asyncio.sleep(self.heartbeat)

                except (aiohttp.ClientError, asyncio.TimeoutError):
                    heartbeat += heartbeat
                    self.mechanism = None
                    logger.warning(f'Not connect to server websocket {self.lifecycle_url}')
                    await asyncio.sleep(heartbeat)
        except asyncio.CancelledError:
            self.mechanism = None


class WebhookLifecycle(Lifecycle, AbstractBackend):
    def __init__(self,
                 webhook_url: str,
                 heartbeat: int = 60,
                 send_timeout: int = 5,
                 wait_send: bool = False,
                 auto_release: bool = True,
                 loop: AbstractEventLoop = None):
        super().__init__(
            backend_url=webhook_url.rstrip('/'),
            wait_send=wait_send,
            send_timeout=send_timeout,
            auto_release=auto_release,
            loop=loop
        )
        self.heartbeat = heartbeat
        self.implementation = 'webhook'

    def write_flow(self, text: str, project_name: str, *args, **kwargs):
        ...

    async def async_write_flow(self, text: str, project_name: str, *args, **kwargs):
        if self.mechanism and 'Traceback (most recent call last):' in text:
            data = {
                'project_name': project_name,
                'traceback': text,
                'request_path': 'project_error'
            }
            try:
                async with self.mechanism.post(f'{self.lifecycle_url}/project_error', json=data):
                    ...
            except Exception:
                self.mechanism = None
        if self.wait_send:
            send_event: threading.Event = kwargs['send_event']
            send_event.set()

    async def _connect_implementation_lifecycle(self, backend_info: dict, event: threading.Event):
        if not self.loop:
            self.loop = asyncio.get_running_loop()
        task = asyncio.create_task(self._connect_to_session(backend_info, event))
        self.working_lifecycle_task = task
        return await task

    async def _connect_to_session(self, backend_info: dict, event: threading.Event):
        try:
            async with ClientSession() as session:
                async with session.post(f'{self.lifecycle_url}/handshake', json=backend_info) as response:
                    event.set()
                    if response.status == 200:
                        logger.info(f'Connected to server webhook {self.lifecycle_url}')
                        self.mechanism = session
                        heartbeat = self.heartbeat
                        while True:
                            info = {
                                'project_name': backend_info['project_name'],
                                'last_readings': self.get_client_readings()
                            }
                            try:
                                async with session.post(f'{self.lifecycle_url}/heartbeat', json=info):
                                    if heartbeat != self.heartbeat:
                                        heartbeat = self.heartbeat
                                        logger.debug(f'Server {self.lifecycle_url} restored, heartbeat sent')
                            except Exception:
                                logger.warning(f'Heartbeat not sent to server {self.lifecycle_url}; (+{heartbeat})')
                                heartbeat += heartbeat
                            await asyncio.sleep(heartbeat)
                    else:
                        logger.warning(f'Not connect to server webhook {self.lifecycle_url}')

        except asyncio.CancelledError:
            self.mechanism = None
        except Exception:
            self.mechanism = None
            logger.warning(f'Not connect to server webhook {self.lifecycle_url}')
