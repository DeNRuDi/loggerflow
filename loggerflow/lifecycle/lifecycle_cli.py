from loggerflow.exceptions import LifecycleException

from typing import Literal

import requests


class Lifecycle:
    def __init__(self,
                 webhook_url: str, heartbeat: int = 60,
                 implementation: Literal['webhook', 'websocket'] = 'webhook'):
        self.webhook_url = webhook_url
        self.heartbeat = heartbeat
        self.implementation = implementation


class LifecycleMixin:
    @staticmethod
    def _create_handshake_for_lifecycle_server(backend: Lifecycle):
        try:
            response = requests.get(f'{backend.webhook_url}/handshake')
            if response.status_code == 200:
                return True
        except requests.exceptions.ConnectionError:
            pass
        raise LifecycleException(
            f'Lifecycle Server {backend.webhook_url} don`t return success code, '
            f'please check that LoggerFlow Server is running on this server.'
        )
