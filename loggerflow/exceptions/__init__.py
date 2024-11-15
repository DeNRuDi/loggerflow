class LifecycleException(Exception):
    """Exception for Lifecycle, if Lifecycle Server don`t return success response"""
    pass


class BackendException(Exception):
    """Exception for Backend, if Backend incorrectly configured"""
    pass

class NotCorrectAlarmException(Exception):
    pass