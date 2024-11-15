import re

from typing_extensions import Literal
from io import StringIO

from loggerflow.lifecycle.utils.formatter import ANSIColors


class StackCleaner:
    """
    Cleaner fot stacktrace.
    """

    def clean_traceback(self, text: str, minimal: bool = False) -> str:
        traceback_string, last_line = self._clean(text)
        if minimal:
            if traceback_string:
                search_result = re.findall(r'File "(.*?)", line (.*?),', traceback_string.getvalue())
                if search_result:
                    path, number_line = search_result[-1]

                    if text != traceback_string.getvalue():
                        path = re.search(r'([^/\\]+\.py)', path).group(1)

                    traceback_string = f"{path}:{number_line} - {last_line}"
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
        raw_last_line = re.findall(r'([\w.]+\w+(?:Exception|Error)\s?:\s.+)', text)
        if raw_last_line:
            last_line = raw_last_line[-1]
        else:
            split_text = [row.strip() for row in text.splitlines() if row.strip() != '']
            last_line = split_text[-1]

        # parse_lines = re.findall(r'(File.+)\n(.+)', text)
        parse_lines = re.findall(r'(^\s*File.+)\n(?!\s*File)(.+)', text, flags=re.MULTILINE)

        for file_line, code_line in parse_lines:
            if (not re.search(r'[/\\][Pp]ython\d.*?[/\\]', file_line) and
                    not re.search(r'[/\\]site-packages[/\\]', file_line)):
                traceback_string.write(f'{file_line}\n{code_line}\n')

        if not traceback_string.getvalue():
            return StringIO(text), last_line

        return traceback_string, last_line

    @staticmethod
    def format_traceback_with_backlight(text: str, format_type: Literal['html', 'terminal'], color: str = 'red') -> str:
        parse_lines = re.findall(r'(^\s*File.+)\n(?!\s*File)(.+)', text, flags=re.MULTILINE)
        for file_line, code_line in parse_lines:
            if (not re.search(r'[/\\][Pp]ython\d.*?[/\\]', file_line)
                    and not re.search(r'[/\\]site-packages[/\\]', file_line)):
                if format_type == 'html':
                    text = text.replace(file_line, f'<span class="traceback-line">{file_line}</span>')
                    text = text.replace(code_line, f'<span class="traceback-line">{code_line}</span>')
                elif format_type == 'terminal':
                    text = text.replace(file_line, ANSIColors.format_text(file_line, color))
                    text = text.replace(code_line, ANSIColors.format_text(code_line, color))
        return text