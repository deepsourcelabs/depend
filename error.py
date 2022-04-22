"""All custom exceptions raised by Dependency Inspector"""
import abc


class UnsupportedError(Exception):
    """Raised when an unsupported action is attempted"""

    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def __init__(self):
        raise NotImplementedError


class LanguageNotSupportedError(UnsupportedError):
    """Raised when language is currently not supported"""

    def __init__(self, lang: str):
        self.msg = f"{lang} is not currently supported"


class VCSNotSupportedError(UnsupportedError):
    """Raised when VCS used is not supported"""

    def __init__(self, package: str):
        self.msg = f"VCS used by {package} is not supported"


class FileNotSupportedError(UnsupportedError):
    """Raised when file to be parsed is not supported"""

    def __init__(self, file: str):
        self.msg = f"{file} is currently not supported"
