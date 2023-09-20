from loggerflow.backends.abstract_backend import AbstractBackend
from loggerflow.utils.filters import Filter


class FileBackend(AbstractBackend, Filter):

    def __init__(self, file: str = None):
        self.file = file

    def write_flow(self, text: str, project_name: str):
        if not any(note in text for note in self.filters):
            if self.file:
                path = self.file
            else:
                path = f'{project_name.lower()}.log'

            with open(path, 'a') as file:
                file.write(f'{text}\n')
