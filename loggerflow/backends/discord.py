from loggerflow.backends.backend import Backend
from discordwebhook import Discord


class DiscordSender(Backend):
    """
    TODO write docstring
    """
    def __init__(self, webhook_url: str, authors: list = None):
        self.webhook_url = webhook_url
        self.authors = authors
        self.traceback_filters = []
    def write_flow(self, text: str, project_name: str = None):
        if 'Traceback (most recent call last):' in text:
            if not any(note in text for note in self.filters):
                try:
                    print(1)
                    discord = Discord(url=self.webhook_url)
                    authors = '\nAuthors: ' + ', '.join(self.authors) if self.authors else ''
                    discord.post(content=f'Project: {project_name}{authors}\n\n' + text)
                except Exception:
                    pass