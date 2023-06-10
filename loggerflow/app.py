from loggerflow.backends.telegram import Telegram
import traceback
import logging
import sys


class LoggerFlow:
    """
    TODO write docstring
    """
    def __init__(self, project_name: str, backend: Telegram | list, authors: list = None, disable: bool = False):
        self.project_name = project_name
        self.original_stdout = sys.stdout
        self.backend = backend
        self.authors = authors
        self.disable = disable
        self.filters = []
        self.traceback_filters = ['A request to the Telegram API was unsuccessful']

    def write(self, text):
        if not any(note in text for note in self.traceback_filters):
            self.original_stdout.write(text)
        if not self.disable:
            self.backend.write_flow(text)

    def flush(self):
        self.original_stdout.flush()

    def exclude_output_tb_filter(self, filter_: str):
        """
        Exclude a filter if you need to avoid double stacktrace output (for example, if used non-standard logging)
        """
        self.traceback_filters.append(filter_)

    def exclude_sending_filter(self, filter_: str):
        """
        Exclude filter from sending to telegram
        """
        self.filters.append(filter_)

    @staticmethod
    def telegram_excepthook(exctype, value, tb):
        print("".join(traceback.format_exception(exctype, value, tb)))

    def run(self):
        if not self.disable:
            logging_handler = TelegramHandler(self)
            sys.excepthook = LoggerFlow.telegram_excepthook
            sys.stdout = self
            logging_handler.setLevel(logging.ERROR)
            logging.getLogger().addHandler(logging_handler)


class TelegramHandler(logging.Handler):
    def __init__(self, telegram_stream):
        super().__init__()
        self.telegram_stream = telegram_stream

    def emit(self, record):
        msg = self.format(record)
        self.telegram_stream.write(msg)
