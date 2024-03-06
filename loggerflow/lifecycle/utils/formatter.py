import logging


class ANSIColors:
    RESET = "\033[0m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"


class ColorFormatter(logging.Formatter):
    COLOR_MAP = {
        logging.WARNING: ANSIColors.YELLOW,
        logging.INFO: ANSIColors.WHITE,
        logging.DEBUG: ANSIColors.BLUE,
        logging.ERROR: ANSIColors.RED,
        logging.CRITICAL: ANSIColors.MAGENTA,
    }

    def format(self, record):
        color = self.COLOR_MAP.get(record.levelno, ANSIColors.WHITE)
        result = super().format(record)
        return f"{color}{result}{ANSIColors.RESET}"
