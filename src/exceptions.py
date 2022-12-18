class Error(Exception):
    """Base class for exception."""


class InfeasibleConfigError(Error):
    """Infeasible parameters entered."""

    def __init__(self, message: str) -> None:
        self.message = message


class BuildFailedError(Error):
    """Failed to build."""

    def __init__(self, message: str) -> None:
        self.message = message
