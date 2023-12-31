from io import StringIO

import re


class StackCleaner:

    def clean_traceback(self, text: str, minimal: bool = False) -> str:
        traceback_string, last_line = self._clean(text)
        if minimal:
            traceback_string = traceback_string.getvalue().splitlines()
            if traceback_string:
                search_result = re.search(r'File "(.*?)", line (.*?),', traceback_string[0])
                if search_result:
                    path, number_line = search_result.groups()
                    file_name = re.search(r'([^/\\]+\.py)', path).group(1)
                    traceback_string = f"{file_name}:{number_line} - {last_line}"
                else:
                    return last_line
            else:
                return last_line
        else:
            if last_line not in traceback_string.getvalue():
                traceback_string.write(last_line)
            traceback_string.seek(0)
            traceback_string = traceback_string.getvalue()

        return traceback_string.strip()

    @staticmethod
    def _clean(text: str) -> tuple:
        traceback_string = StringIO()
        split_text = [row.strip() for row in text.splitlines() if row.strip() != '']
        last_line = split_text[-1]

        parse_lines = re.findall(r'(File.+)\n(.+)', text)
        for file_line, code_line in parse_lines:
            if (not re.search(r'[/\\][Pp]ython\d.*?[/\\]', file_line) and
                    not re.search(r'[/\\]site-packages[/\\]', file_line)):
                traceback_string.write(f'{file_line}\n{code_line}\n')

        if not traceback_string.getvalue():
            return StringIO(text), last_line

        return traceback_string, last_line
