import sys
import threading

from traceback import format_exception


class ExceptHook:

    def __init__(self,  disable: bool = False, thread_logging: bool = True):
        self.disable = disable
        self.original_stdout = sys.stdout
        self.thread_logging = thread_logging

    def write(self, text: str):
        self.original_stdout.write(text)

    def flush(self):
        self.original_stdout.flush()

    def isatty(self):
        return self.original_stdout.isatty()

    @staticmethod
    def _except_hook(exctype, value, tb):
        print("".join(format_exception(exctype, value, tb)))

    def _thread_excepthook(self, args):
        exctype, value, tb = args.exc_type, args.exc_value, args.exc_traceback
        self._except_hook(exctype, value, tb)

    def run(self):
        if not self.disable:
            sys.excepthook = self._except_hook
            if self.thread_logging:
                threading.excepthook = self._thread_excepthook
            sys.stdout = self
