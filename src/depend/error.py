"""All custom exceptions raised by Dependency Inspector"""
import abc


class UnsupportedError(Exception):
    """Raised when an unsupported action is attempted"""

    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def __init__(self, msg):
        super().__init__(msg)


class LanguageNotSupportedError(UnsupportedError):
    """Raised when language is currently not supported"""

    def __init__(self, lang: str):
        self.msg = f"{lang} is not currently supported"
        super().__init__(self.msg)


class VCSNotSupportedError(UnsupportedError):
    """Raised when VCS used is not supported"""

    def __init__(self, package: str):
        self.msg = f"VCS used by {package} is not supported"
        super().__init__(self.msg)


class FileNotSupportedError(UnsupportedError):
    """Raised when file to be parsed is not supported"""

    def __init__(self, file: str):
        self.msg = f"{file} is currently not supported"
        super().__init__(self.msg)


class ParamMissing(UnsupportedError):
    """Raised when DB parameter is not defined"""

    def __init__(self, param: str):
        self.msg = (
            f"{param} is not defined as an environment variables or is an empty string"
        )
        super().__init__(self.msg)
