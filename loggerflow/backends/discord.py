from loggerflow.backends.abstract_backend import AbstractBackend
from loggerflow.utils.filters import Filter

from discordwebhook import Discord


class DiscordBackend(AbstractBackend, Filter):
    def __init__(self, webhook_url: str, authors: list = None):
        self.webhook_url = webhook_url
        self.authors = authors
        self.discord = Discord(url=self.webhook_url)

    def write_flow(self, text: str, project_name: str):
        if not any(note in text for note in self.filters):
            try:
                authors = '\nAuthors: ' + ', '.join(self.authors) if self.authors else ''
                self.discord.post(content=f'Project: {project_name}{authors}\n\n' + text)
            except Exception:
                pass
