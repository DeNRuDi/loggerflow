import logging


class LoggingHandler(logging.Handler):
    def __init__(self, telegram_stream):
        super().__init__()
        self.telegram_stream = telegram_stream

    def emit(self, record):
        msg = self.format(record)
        self.telegram_stream.write(msg)
