from loggerflow.backends.abstract_backend import AbstractBackend
from loggerflow.utils.filters import Filter
import requests


class TelegramBackend(AbstractBackend, Filter):
    def __init__(self, token: str, chat_id: int,  authors: list = None):
        self.token = token
        self.chat_id = chat_id
        self.authors = authors
        self.traceback_filters.append('A request to the Telegram API was unsuccessful')

    def write_flow(self, text: str, project_name: str):
        if not any(note in text for note in self.filters):
            try:
                authors = '\nAuthors: ' + ', '.join(self.authors) if self.authors else ''
                url = f"https://api.telegram.org/bot{self.token}/sendMessage"
                letters_count = 4000
                if len(text) >= letters_count:
                    text = [text[i:i + letters_count] for i in range(0, len(text), letters_count)]

                if isinstance(text, list):
                    data = {"chat_id": self.chat_id, "text": f'Project: {project_name}{authors}\n\n' + text[0]}
                    requests.post(url, data=data)
                    for part in text[1:]:
                        data = {"chat_id": self.chat_id, "text": part}
                        requests.post(url, data=data)
                else:
                    data = {"chat_id": self.chat_id, "text": f'Project: {project_name}{authors}\n\n' + text}
                    requests.post(url, data=data)
            except Exception:
                pass
