from .telegram import TelegramBackend
from .discord import DiscordBackend
from .file import FileBackend
from loggerflow.lifecycle.lifecycle_cli import Lifecycle

from typing import Union, List

Backend = Union[TelegramBackend, DiscordBackend, FileBackend, Lifecycle, List]
