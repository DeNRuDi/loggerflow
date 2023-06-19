import logging


class LoggingHandler(logging.Handler):
    def __init__(self, flow):
        super().__init__()
        self.flow = flow

    def emit(self, record):
        msg = self.format(record)
        self.flow.write(msg)
