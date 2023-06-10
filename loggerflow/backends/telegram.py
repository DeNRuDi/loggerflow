from loggerflow.backends.backend import Backend

import requests


class Telegram(Backend):
    """
    TODO write docstring
    """
    def __init__(self, token: str, chat_id: int):
        self.token = token
        self.chat_id = chat_id
        self.traceback_filters.append('A request to the Telegram API was unsuccessful')

    def write_flow(self, text: str):
        if 'Traceback (most recent call last):' in text:
            if not any(note in text for note in self.filters):
                try:
                    authors = '\nAuthors: ' + ', '.join(self.authors) if self.authors else ''
                    url = f"https://api.telegram.org/bot{self.token}/sendMessage"
                    data = {"chat_id": self.chat_id, "text": f'Project: {self.project_name}{authors}\n\n' + text}
                    requests.post(url, data=data)
                except Exception:
                    pass