from loggerflow.backends.abstract_backend import AbstractBackend
from loggerflow.backends.filters import Filter
import requests


class TelegramBackend(AbstractBackend, Filter):
    """
    TODO write docstring
    """
    def __init__(self, token: str, chat_id: int,  authors: list = None):
        self.token = token
        self.chat_id = chat_id
        self.authors = authors
        self.traceback_filters.append('A request to the Telegram API was unsuccessful')

    def write_flow(self, text: str, project_name: str = None):
        if 'Traceback (most recent call last):' in text:
            if not any(note in text for note in self.filters):
                try:
                    authors = '\nAuthors: ' + ', '.join(self.authors) if self.authors else ''
                    url = f"https://api.telegram.org/bot{self.token}/sendMessage"
                    data = {"chat_id": self.chat_id, "text": f'Project: {project_name}{authors}\n\n' + text}
                    requests.post(url, data=data)
                except Exception:
                    pass