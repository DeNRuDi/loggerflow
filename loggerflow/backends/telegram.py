import aiohttp

from loggerflow.backends.abstract_backend import AbstractBackend
from loggerflow.utils.filters import Filter
import requests


class TelegramBackend(AbstractBackend, Filter):
    def __init__(self, token: str, chat_id: int,  authors: list = None):
        self.token = token
        self.chat_id = chat_id
        self.authors = authors
        self.traceback_filters.append('A request to the Telegram API was unsuccessful')

    def _run_logic_flow(self, text: str, project_name: str) -> tuple:
        authors = '\nAuthors: ' + ', '.join(self.authors) if self.authors else ''
        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        letters_count = 4000

        results = [
            {'chat_id': self.chat_id, 'text': f'Project: {project_name}{authors}\n\n' + text[0]}
        ]

        if len(text) >= letters_count:
            text = [text[i:i + letters_count] for i in range(0, len(text), letters_count)]
            for part in text[1:]:
                results.append({'chat_id': self.chat_id, 'text': part})

        return url, results

    def write_flow(self, text: str, project_name: str):
        if not any(note in text for note in self.filters):
            url, results = self._run_logic_flow(text=text, project_name=project_name)
            try:
                for data in results:
                    requests.post(url, data=data)
            except Exception:
                pass

    async def async_write_flow(self, text: str, project_name: str):
        if not any(note in text for note in self.filters):
            url, results = self._run_logic_flow(text=text, project_name=project_name)
            try:
                async with aiohttp.ClientSession() as session:
                    for data in results:
                        async with session.post(url, data=data):
                            ...
            except Exception:
                pass
