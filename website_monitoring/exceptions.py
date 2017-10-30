class WhileCheckingException(Exception):
    pass

class EmptyNameException(WhileCheckingException):
    """You must provide a name for the website."""

class EmptyURLException(WhileCheckingException):
    """You must provide an URL for the website."""

class EmptyIntervalException(WhileCheckingException):
    """You must provide an interval."""

class BadIntervalException(WhileCheckingException):
    """Interval must be an integer."""

