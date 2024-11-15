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
    BOLD = "\033[1m"
    STATIC_COLORS = [RESET, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE, BOLD]
    COLOR_MAP = {
        'red': RED,
        'green': GREEN,
        'yellow': YELLOW,
        'blue': BLUE,
        'magenta': MAGENTA,
        'cyan': CYAN,
        'white': WHITE,
        'no': 'no'
    }

    @staticmethod
    def format_text(text: str, color: str):
        color_code = ANSIColors.COLOR_MAP.get(color.lower())
        if color_code == 'no':
            return text
        return f'{ANSIColors.BOLD}{color_code}{text}{ANSIColors.RESET}'

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
