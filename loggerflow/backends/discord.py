from loggerflow.backends.abstract_backend import AbstractBackend
from loggerflow.exceptions import BackendException

from loggerflow.utils.aiodiscord import AIODiscord
from discordwebhook import Discord


class DiscordBackend(AbstractBackend):
    alarm_required_fields = ['webhook_url']

    def __init__(self, webhook_url: str, authors: list = None):
        self.webhook_url = webhook_url
        self.authors = authors
        self.discord = Discord(url=self.webhook_url)
        self.aiodiscord = AIODiscord(url=self.webhook_url)

        if self.authors and not isinstance(authors, list):
            raise BackendException("Authors should be a list")

    def write_flow(self, text: str, project_name: str,  *args, **kwargs):
        try:
            authors = '\nAuthors: ' + ', '.join(self.authors) if self.authors else ''
            self.discord.post(content=f'Project: {project_name}{authors}\n\n' + text)
        except Exception:
            pass

    async def async_write_flow(self, text: str, project_name: str,  *args, **kwargs):
        try:
            authors = '\nAuthors: ' + ', '.join(self.authors) if self.authors else ''
            await self.aiodiscord.post(content=f'Project: {project_name}{authors}\n\n' + text)
        except Exception:
            pass
