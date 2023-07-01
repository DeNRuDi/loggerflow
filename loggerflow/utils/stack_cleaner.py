from itertools import chain
from io import StringIO

import re


class StackCleaner:

    def clean_traceback(self, text: str, minimal: bool = False) -> str:
        traceback_string, last_line = self._clean(text)
        if minimal:
            traceback_string = traceback_string.getvalue().splitlines()
            if traceback_string:
                search_string = re.findall(r'File "(.*?)", line (.*?),', traceback_string[0])
                path, number_line = list(chain.from_iterable(search_string))
                file_name = re.search(r'([^/\\]+\.py)', path).group(1)
                traceback_string = f"{file_name}:{number_line} - {last_line}"
            else:
                traceback_string = last_line
        else:
            traceback_string.write(last_line)
            traceback_string.seek(0)
            traceback_string = traceback_string.getvalue()

        return traceback_string

    @staticmethod
    def _clean(text: str) -> tuple:
        traceback_string = StringIO()

        last_line = text.splitlines()[-1].strip()
        parse_lines = re.findall(r'(File.+)\n(.+)', text)

        for file_line, code_line in parse_lines:
            if not re.search(r'[/\\][Pp]ython\d.*?[/\\]', file_line):
                traceback_string.write(f'{file_line}\n{code_line}\n')

        return traceback_string, last_line
