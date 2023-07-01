from .telegram import TelegramBackend
from .discord import DiscordBackend

from typing import Union

Backend = Union[TelegramBackend, DiscordBackend]
