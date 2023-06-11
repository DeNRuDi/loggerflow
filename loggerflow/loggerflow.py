#  \     \
#  _\_____\
# | |   __  \___       /     __     __   ___   ___   ___   ----         __
# | |  |__/     |     /    /   /  / __  /__   /__   /  /  /___  /     /   /   /  /  /
# | |      ____/     /___ /___/  /___/ /___/ /___  /     /     /___  /___/   /__/__/
# |_|_____/


from loggerflow.utils.handler import LoggingHandler
from loggerflow.backends.telegram import Telegram
from loggerflow.backends.discord import DiscordSender

import traceback
import logging
import sys


class LoggerFlow:
    """
    TODO write docstring
    """
    def __init__(self, project_name: str, backends: list, disable: bool = False):
        self.project_name = project_name
        self.original_stdout = sys.stdout
        self.backends = backends
        self.disable = disable

    def write(self, text):
        for backend in self.backends:
            if not any(note in text for note in backend.traceback_filters):
                self.original_stdout.write(text)
            if not self.disable:
                backend.write_flow(text, self.project_name)

    def flush(self):
        self.original_stdout.flush()

    def exclude_output_tb_filter(self, filter_: str):
        """
        Exclude a filter if you need to avoid double stacktrace output (for example, if used non-standard logging)
        """
        self.backends.traceback_filters.append(filter_)

    def exclude_sending_filter(self, filter_: str):
        """
        Exclude filter from sending to telegram
        """
        self.backends.filters.append(filter_)

    @staticmethod
    def telegram_excepthook(exctype, value, tb):
        print("".join(traceback.format_exception(exctype, value, tb)))

    def run(self):
        if not self.disable:
            logging_handler = LoggingHandler(self)
            sys.excepthook = LoggerFlow.telegram_excepthook
            sys.stdout = self
            logging_handler.setLevel(logging.ERROR)
            logging.getLogger().addHandler(logging_handler)



