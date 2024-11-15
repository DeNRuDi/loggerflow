from traceback import format_exc
from typing import Literal

from loggerflow.excepthook import ExceptHook
from loggerflow.utils.stack_cleaner import StackCleaner


class TracebackBacklighter(ExceptHook):

    def __init__(self, backlight: Literal['no', 'clean', 'myline'] = 'no', disable: bool = False,
                 thread_logging: bool = True,
                 color: Literal['no', 'red', 'green', 'yellow', 'blue', 'magenta', 'cyan', 'white'] = 'no'):
        super().__init__(disable, thread_logging)
        self.backlight = backlight
        self.color = color

    def write(self, text: str):
        if not self.disable:
            self.custom_format_exception(text)


    def custom_format_exception(self, traceback: str = None):
        traceback = traceback or format_exc()

        if self.backlight != 'no':
            sc = StackCleaner()
            if traceback != '\n':
                traceback = sc.clean_traceback(traceback) if self.backlight == 'clean' else traceback
                traceback = sc.format_traceback_with_backlight(traceback, format_type='terminal', color=self.color)

        self.original_stdout.write(traceback)