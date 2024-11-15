from loggerflow.backends.abstract_backend import AbstractBackend
from loggerflow.utils.filters import Filter
import aiofiles


class FileBackend(AbstractBackend, Filter):
    alarm_required_fields = ['file']

    def __init__(self, file: str = None):
        self.file = file

    def _run_logic_flow(self, project_name: str) -> str:
        if self.file:
            path = self.file
        else:
            path = f'{project_name.lower()}.log'
        return path

    def write_flow(self, text: str, project_name: str,  *args, **kwargs):
        path = self._run_logic_flow(project_name)
        with open(path, 'a') as file:
            file.write(f'{text}\n')

    async def async_write_flow(self, text: str, project_name: str,  *args, **kwargs):
        path = self._run_logic_flow(project_name)
        async with aiofiles.open(path, 'a') as file:
            await file.write(f'{text}\n')
