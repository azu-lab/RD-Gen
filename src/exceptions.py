class Error(Exception):
    """Base class for exception in this module."""


class MaxBuildFailError(Error):
    def __init__(self, message: str = '') -> None:
        self.message = message


class InvalidArgumentError(Error):
    def __init__(self, message: str = '') -> None:
        self.message = message
