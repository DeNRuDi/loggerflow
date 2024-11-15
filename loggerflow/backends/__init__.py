from .abstract_backend import AbstractBackend
from .telegram import TelegramBackend
from .discord import DiscordBackend
from .file import FileBackend

from typing import Union, List

Backend = Union[AbstractBackend, List, None]
AlarmBackend = [TelegramBackend, DiscordBackend, FileBackend]
