from typing import List, Dict


class Filter:
    filters: List[str] = []
    traceback_filters: List[str] = []


class AlarmFilter:
    filters: Dict = {}